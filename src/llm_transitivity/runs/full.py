"""Freeze and execute the authorized full-corpus run in a detached worker."""

import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

from inspect_flow import FlowSpec
from inspect_flow.api import init

from llm_transitivity.analysis.followup import review_phase
from llm_transitivity.costs.archive import save_estimate
from llm_transitivity.costs.estimate import estimate
from llm_transitivity.evidence.serialization import digest, json_bytes
from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.inspect.full import build_full_spec
from llm_transitivity.runs.archive import prepare_archive
from llm_transitivity.runs.followup import _event, _phase_run, _validate


def prepare(root: Path) -> Path:
    full = build_full_spec(root)
    preflight = build_pilot_spec(root, profile="pilot3", preflight=True)
    quote = save_estimate(root, estimate(root, profile="pilot3", full=True))
    directory = Path(full.log_dir).parent
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "profile": "pilot3",
        "scope": "full-corpus",
        "planned_responses": 324000,
        "preflight_responses": 6,
        "price_estimate": str(quote.relative_to(root)),
        "price_estimate_sha256": digest(quote.read_bytes()),
        "stages": [],
    }
    for name, spec in [("preflight", preflight), ("corpus", full)]:
        phase = directory / name
        spec.log_dir = str(phase / "inspect")
        spec.options.metadata["results_root"] = str(phase.relative_to(root))
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
    (directory / "full_manifest.json").write_bytes(json_bytes(manifest))
    return directory


def launch(root: Path, directory: Path) -> int:
    with (directory / "console.txt").open("ab") as stream:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "llm_transitivity.cli.app",
                "--root",
                str(root),
                "full",
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


def execute(root: Path, directory: Path) -> bool:
    with (directory / "execution.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = json.loads((directory / "full_manifest.json").read_text())
        _validate(root, directory, manifest)
        init(display="plain", dotenv_base_dir=str(root))
        (directory / "worker.json").write_bytes(
            json_bytes({"pid": os.getpid(), "status": "running"})
        )
        previous = (
            [
                json.loads(line)
                for line in (directory / "events.jsonl").read_text().splitlines()
            ]
            if (directory / "events.jsonl").exists()
            else []
        )
        for stage in manifest["stages"]:
            saved = next(
                (
                    e
                    for e in reversed(previous)
                    if e.get("stage") == stage["name"] and e.get("status") == "passed"
                ),
                None,
            )
            if saved:
                if (
                    digest((directory / saved["review"]).read_bytes())
                    != saved["review_sha256"]
                ):
                    raise ValueError("Saved full-run review changed")
                continue
            _validate(root, directory, manifest)
            path = directory / stage["spec"]
            phase = path.parent.parent
            spec_data = json.loads(path.read_text())
            spec = FlowSpec.model_validate(spec_data)
            _event(directory, stage=stage["name"], status="started")
            try:
                success = _phase_run(root, phase, spec)
            except BaseException as primary:
                try:
                    _event(
                        directory,
                        stage=stage["name"],
                        status="stopped",
                        error_type=type(primary).__name__,
                    )
                    (directory / "worker.json").write_bytes(
                        json_bytes(
                            {
                                "pid": os.getpid(),
                                "status": "failed",
                                "error_type": type(primary).__name__,
                            }
                        )
                    )
                except BaseException as secondary:  # noqa: BLE001 - preserve the execution failure
                    primary.add_note(
                        "Worker status write failed: " + type(secondary).__name__
                    )
                raise
            if stage["name"] == "preflight":
                review = review_phase(root, phase, spec_data)
                success = success and review["technical_pass"]
            else:
                index = json.loads(
                    max(
                        (phase / "summary").glob("log_index*.json"),
                        key=lambda p: p.stat().st_mtime_ns,
                    ).read_text()
                )
                latest = {}
                for entry in sorted(
                    index["logs"],
                    key=lambda v: (v.get("status") == "success", v["path"]),
                ):
                    latest[(entry.get("model"), entry.get("dataset"))] = entry
                expected = {
                    (task.model.name, task.metadata["dataset_name"]): task.metadata[
                        "selected_case_count"
                    ]
                    for task in spec.tasks
                }
                complete = set(latest) == set(expected) and all(
                    latest[k].get("status") == "success"
                    and latest[k].get("sample_count") == count
                    and latest[k].get("sample_errors") == 0
                    for k, count in expected.items()
                )
                success = success and complete
                review = {
                    "complete": complete,
                    "expected_responses": 324000,
                    "saved_samples": sum(
                        v.get("sample_count", 0) for v in latest.values()
                    ),
                    "sample_errors": sum(
                        v.get("sample_errors", 0) for v in latest.values()
                    ),
                    "note": "Finalization checks completeness. Per-call routing, usage, and cost analysis remains separate.",
                }
            review_path = phase / "summary/closure.json"
            if review_path.exists():
                from uuid import uuid4

                review_path = phase / "summary" / f"closure-{uuid4().hex[:8]}.json"
            review_path.write_bytes(json_bytes(review))
            _event(
                directory,
                stage=stage["name"],
                status="passed" if success else "stopped",
                review=str(review_path.relative_to(directory)),
                review_sha256=digest(review_path.read_bytes()),
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
