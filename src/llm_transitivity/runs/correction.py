"""Execute a fixed correction with the original model configuration."""

import fcntl
import json
import os
import subprocess
import sys
import tomllib
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from inspect_flow import FlowSpec
from inspect_flow.api import init

from llm_transitivity.analysis.followup import review_phase
from llm_transitivity.datasets.correction import (
    CORRECTION_ID,
    DATASETS,
    MANIFEST,
    SOURCE_RUN,
)
from llm_transitivity.datasets.inputs import load_input
from llm_transitivity.datasets.pilot import verify
from llm_transitivity.evidence.serialization import digest, json_bytes
from llm_transitivity.inspect.samples import task_metadata
from llm_transitivity.runs.archive import prepare_archive
from llm_transitivity.runs.followup import _event, _phase_run


def read(path):
    return json.loads(path.read_text())


def specs(root: Path) -> dict:
    verify(root)
    correction = read(root / MANIFEST)
    source = root / SOURCE_RUN
    frozen = read(source / "corpus/provenance/flow_spec.json")
    snapshot = source / "corpus/provenance/snapshot"
    for relative in (
        "prompts/systemPrompts/zeroShot.json",
        "src/llm_transitivity/domain/scoring.py",
        "src/llm_transitivity/inspect/scoring.py",
    ):
        if (root / relative).read_bytes() != (snapshot / relative).read_bytes():
            raise ValueError("Experimental dependency changed: " + relative)
    old_packages = {
        p["name"]: p.get("version")
        for p in tomllib.loads((snapshot / "uv.lock").read_text())["package"]
    }
    new_packages = {
        p["name"]: p.get("version")
        for p in tomllib.loads((root / "uv.lock").read_text())["package"]
    }
    if any(new_packages.get(name) != version for name, version in old_packages.items()):
        raise ValueError("Frozen dependency versions changed")
    inputs = {name: load_input(root, name) for name in DATASETS}
    selected = {
        name: [r["original_row"] for r in correction["cases"] if r["dataset"] == name]
        for name in DATASETS
    }
    result = {}
    for phase in ("preflight", "corpus"):
        value = deepcopy(frozen)
        value["tasks"] = [
            t
            for t in value["tasks"]
            if t["metadata"]["dataset_name"] in DATASETS
            and (phase == "corpus" or t["metadata"]["dataset_name"] == "HS_HF_PA_2000")
        ]
        for task in value["tasks"]:
            name = task["metadata"]["dataset_name"]
            task["args"]["root"] = str(root)
            task["sample_id"] = (
                selected[name] if phase == "corpus" else selected[name][:1]
            )
            task["metadata"].update(task_metadata(inputs[name]))
            task["metadata"].update(
                pilot_manifest_sha256=digest(
                    (root / "datasets/pilot/manifest.json").read_bytes()
                ),
                correction_id=CORRECTION_ID,
                phase=phase,
                selected_case_count=len(task["sample_id"]),
                sample_count=len(task["sample_id"]),
            )
            task["tags"] += [f"correction:{CORRECTION_ID}", f"phase:{phase}"]
        md = value["options"]["metadata"]
        md.update(
            correction_id=CORRECTION_ID,
            source_run=SOURCE_RUN,
            phase=phase,
            planned_responses=3672 if phase == "corpus" else 6,
            selected_cases_per_model=612 if phase == "corpus" else 1,
            pilot_manifest_sha256=digest(
                (root / "datasets/pilot/manifest.json").read_bytes()
            ),
        )
        paths = set(md["source_sha256"]) | {str(MANIFEST)}
        paths.update(
            str(p.relative_to(root))
            for p in (root / "src/llm_transitivity").rglob("*")
            if p.is_file() and p.suffix in {".py", ".html", ".css", ".js"}
        )
        md["source_sha256"] = {
            rel: digest((root / rel).read_bytes()) for rel in sorted(paths)
        }
        md["pilot_manifest_sha256"] = digest(
            (root / "datasets/pilot/manifest.json").read_bytes()
        )
        value["options"]["tags"] += [f"correction:{CORRECTION_ID}"]
        result[phase] = FlowSpec.model_validate(value)
    return result


def prepare(root: Path) -> Path:
    stages = specs(root)
    directory = (
        root
        / "results/corrections"
        / (
            datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
            + "-"
            + uuid4().hex[:8]
            + "-"
            + CORRECTION_ID
        )
    )
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "id": CORRECTION_ID,
        "source_run": SOURCE_RUN,
        "planned_responses": 3672,
        "preflight_responses": 6,
        "correction_manifest": str(MANIFEST),
        "correction_manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "stages": [],
    }
    for name, spec in stages.items():
        phase = directory / name
        spec.log_dir = str(phase / "inspect")
        spec.options.metadata["results_root"] = str(phase.relative_to(root))
        spec.options.metadata["source_experiment_run_id"] = spec.options.metadata[
            "experiment_run_id"
        ]
        spec.options.metadata["experiment_run_id"] = directory.name
        spec.options.metadata["configuration_created_utc"] = datetime.now(
            UTC
        ).isoformat()
        spec.options.metadata["full_run_root"] = str(directory.relative_to(root))
        prepare_archive(spec, root)
        path = phase / "provenance/flow_spec.json"
        manifest["stages"].append(
            {
                "name": name,
                "spec": str(path.relative_to(directory)),
                "spec_sha256": digest(path.read_bytes()),
            }
        )
    (directory / "correction_manifest.json").write_bytes(json_bytes(manifest))
    return directory


def validate(root, directory, manifest):
    if digest((root / MANIFEST).read_bytes()) != manifest["correction_manifest_sha256"]:
        raise ValueError("Correction manifest changed")
    for stage in manifest["stages"]:
        path = directory / stage["spec"]
        if digest(path.read_bytes()) != stage["spec_sha256"]:
            raise ValueError("Correction configuration changed")
        for rel, expected in read(path.parent / "snapshot_hashes.json").items():
            if (
                digest((root / rel).read_bytes()) != expected
                or digest((path.parent / "snapshot" / rel).read_bytes()) != expected
            ):
                raise ValueError("Correction source changed: " + rel)


def execute(root: Path, directory: Path) -> bool:
    with (directory / "execution.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = read(directory / "correction_manifest.json")
        validate(root, directory, manifest)
        init(display="plain", dotenv_base_dir=str(root))
        import llm_transitivity.inspect.tasks  # noqa: F401 - register task factories

        (directory / "worker.json").write_bytes(
            json_bytes({"pid": os.getpid(), "status": "running"})
        )
        for stage in manifest["stages"]:
            phase = directory / stage["name"]
            events = (
                [
                    json.loads(line)
                    for line in (directory / "events.jsonl").read_text().splitlines()
                ]
                if (directory / "events.jsonl").exists()
                else []
            )
            prior = next(
                (
                    e
                    for e in reversed(events)
                    if e.get("stage") == stage["name"] and e.get("status") == "passed"
                ),
                None,
            )
            if prior:
                if (
                    digest((directory / prior["review"]).read_bytes())
                    != prior["review_sha256"]
                ):
                    raise ValueError("Correction closure changed")
                continue
            validate(root, directory, manifest)
            spec_data = read(directory / stage["spec"])
            _event(directory, stage=stage["name"], status="started")
            try:
                success = _phase_run(root, phase, FlowSpec.model_validate(spec_data))
            except BaseException as error:
                (directory / "worker.json").write_bytes(
                    json_bytes(
                        {
                            "pid": os.getpid(),
                            "status": "failed",
                            "stage": stage["name"],
                            "error_type": type(error).__name__,
                        }
                    )
                )
                raise
            review = review_phase(root, phase, spec_data)
            index_path = max(
                (phase / "summary").glob("log_index*.json"),
                key=lambda p: p.stat().st_mtime_ns,
            )
            index = read(index_path)
            latest = {}
            for entry in sorted(
                index["logs"], key=lambda e: (e.get("status") == "success", e["path"])
            ):
                latest[(entry.get("model"), entry.get("dataset"))] = entry
            index["logs"] = list(latest.values())
            selected_index = (
                phase / "summary" / f"selected_log_index-{uuid4().hex[:8]}.json"
            )
            selected_index.write_bytes(json_bytes(index))
            review["selected_log_index"] = str(selected_index.relative_to(directory))
            review["selected_log_index_sha256"] = digest(selected_index.read_bytes())
            success = success and review["technical_pass"]
            path = (
                phase
                / "summary"
                / (
                    "closure.json"
                    if not (phase / "summary/closure.json").exists()
                    else f"closure-{uuid4().hex[:8]}.json"
                )
            )
            path.write_bytes(json_bytes(review))
            _event(
                directory,
                stage=stage["name"],
                status="passed" if success else "stopped",
                review=str(path.relative_to(directory)),
                review_sha256=digest(path.read_bytes()),
            )
            if not success:
                (directory / "worker.json").write_bytes(
                    json_bytes(
                        {
                            "pid": os.getpid(),
                            "status": "stopped",
                            "stage": stage["name"],
                        }
                    )
                )
                return False
        (directory / "worker.json").write_bytes(
            json_bytes({"pid": os.getpid(), "status": "complete"})
        )
        return True


def launch(root: Path, directory: Path) -> int:
    with (directory / "console.txt").open("ab") as stream:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "llm_transitivity.cli.app",
                "--root",
                str(root),
                "correction",
                "--resume",
                str(directory),
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=stream,
            start_new_session=True,
        )
    (directory / f"launcher-{child.pid}.json").write_bytes(
        json_bytes({"pid": child.pid})
    )
    return child.pid
