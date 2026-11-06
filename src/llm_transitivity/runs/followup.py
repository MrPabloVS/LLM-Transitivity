"""Freeze and execute the authorized Haiku follow-up with direct 64-slot load."""

import fcntl
import importlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile
from zoneinfo import ZoneInfo

from inspect_flow import FlowSpec
from inspect_flow.api import init, run

from llm_transitivity.analysis.followup import review_phase
from llm_transitivity.costs.archive import save_estimate
from llm_transitivity.costs.estimate import estimate
from llm_transitivity.evidence.serialization import digest, json_bytes
from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.runs.archive import finalize_archive, prepare_archive

HAIKU_IDS = ("anthropic/claude-haiku-4.5", "anthropic/claude-haiku-5.5")


def stage_specs(root: Path) -> list[tuple[str, FlowSpec]]:
    return [
        ("preflight", build_pilot_spec(root, profile="haiku", preflight=True)),
        (
            "coverage",
            build_pilot_spec(root, profile="haiku", selected_models=HAIKU_IDS),
        ),
        ("load-64", build_pilot_spec(root, profile="haiku", load=True, concurrency=64)),
    ]


def preview(root: Path) -> dict:
    return {
        name: {
            "tasks": len(spec.tasks),
            "responses": spec.options.metadata["planned_responses"],
            "max_samples": spec.options.max_samples,
            "max_tasks": spec.options.max_tasks,
        }
        for name, spec in stage_specs(root)
    }


def prepare(root: Path) -> Path:
    stages = stage_specs(root)
    quote = estimate(root, profile="haiku", followup=True)
    estimate_path = save_estimate(root, quote)
    campaign_id = str(uuid4())
    stamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    directory = root / "results/pilot" / f"{stamp}-{campaign_id[:8]}-haiku-followup"
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "version": 1,
        "campaign_id": campaign_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "profile": "haiku",
        "direct_load_concurrency": 64,
        "coverage_concurrency": 16,
        "no_spend_pause": True,
        "full_corpus_run": False,
        "planned_responses": 2382,
        "planned_tasks": 48,
        "omitted_load_levels": {
            "16": "User requested direct 64-slot load",
            "32": "User requested direct 64-slot load",
        },
        "price_estimate": str(estimate_path.relative_to(root)),
        "price_estimate_sha256": digest(estimate_path.read_bytes()),
        "stages": [],
    }
    for name, spec in stages:
        phase = directory / name
        spec.log_dir = str(phase / "inspect")
        spec.options.metadata.update(
            {
                "campaign_id": campaign_id,
                "profile": "haiku",
                "results_root": str(phase.relative_to(root)),
            }
        )
        spec.options.tags += [
            f"campaign:{campaign_id}",
            "profile:haiku",
            f"concurrency:{spec.options.max_samples}",
        ]
        for task in spec.tasks:
            task.metadata["campaign_id"] = campaign_id
            task.tags += [
                f"campaign:{campaign_id}",
                "profile:haiku",
                f"concurrency:{spec.options.max_samples}",
            ]
        prepare_archive(spec, root)
        manifest["stages"].append(
            {
                "name": name,
                "spec": str(
                    (phase / "provenance/flow_spec.json").relative_to(directory)
                ),
                "spec_sha256": digest(
                    (phase / "provenance/flow_spec.json").read_bytes()
                ),
            }
        )
    (directory / "campaign.json").write_bytes(json_bytes(manifest))
    return directory


def launch(root: Path, directory: Path) -> int:
    with (directory / "console.txt").open("ab") as output:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "llm_transitivity.cli.app",
                "--root",
                str(root),
                "followup",
                "--resume",
                str(directory),
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    path = directory / f"launcher-{child.pid}.json"
    path.write_bytes(
        json_bytes({"pid": child.pid, "mode": "detached", "directory": str(directory)})
    )
    return child.pid


def _event(directory: Path, **fields) -> None:
    with (directory / "events.jsonl").open("a") as stream:
        stream.write(
            json.dumps({"at_utc": datetime.now(UTC).isoformat(), **fields}) + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


def _validate(root: Path, directory: Path, manifest: dict) -> None:
    if (
        digest((root / manifest["price_estimate"]).read_bytes())
        != manifest["price_estimate_sha256"]
    ):
        raise ValueError("Price estimate changed")
    for stage in manifest["stages"]:
        path = directory / stage["spec"]
        if digest(path.read_bytes()) != stage["spec_sha256"]:
            raise ValueError("Frozen Flow spec changed")
        hashes = json.loads((path.parent / "snapshot_hashes.json").read_text())
        for relative, expected in hashes.items():
            if digest((root / relative).read_bytes()) != expected:
                raise ValueError(
                    "Source changed since follow-up preparation: " + relative
                )
            if digest((path.parent / "snapshot" / relative).read_bytes()) != expected:
                raise ValueError("Frozen snapshot changed: " + relative)


def _checkpoint(phase: Path) -> None:
    logs = list((phase / "inspect").glob("*.eval"))
    if logs:
        suffix = uuid4().hex[:8]
        with ZipFile(
            phase / "provenance" / f"resume-checkpoint-{suffix}.zip", "x", ZIP_DEFLATED
        ) as archive:
            for path in sorted((phase / "inspect").rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(phase))


def _finalize(phase: Path, success: bool | None, error: str | None = None) -> None:
    name = "log_index.json"
    if (phase / "summary" / name).exists():
        name = f"log_index-{uuid4().hex[:8]}.json"
    finalize_archive(phase, flow_success=success, error_type=error, index_name=name)


def _phase_run(root: Path, phase: Path, spec: FlowSpec) -> bool:
    _checkpoint(phase)
    try:
        result = run(
            spec=spec,
            base_dir=str(root),
            handle_file=str(phase / f"handle-{uuid4().hex[:8]}.json"),
        )
    except BaseException as primary:
        try:
            _finalize(phase, None, type(primary).__name__)
        except BaseException as secondary:  # noqa: BLE001 - preserve the primary error
            primary.add_note(f"Finalization failed: {type(secondary).__name__}")
        raise
    _finalize(phase, result.success)
    return result.success


def execute(root: Path, directory: Path) -> bool:
    init(display="plain", dotenv_base_dir=str(root))
    importlib.import_module("llm_transitivity.inspect.tasks")
    manifest = json.loads((directory / "campaign.json").read_text())
    with (directory / "execution.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _validate(root, directory, manifest)
        reviews, stopped = {}, False
        previous = []
        if (directory / "events.jsonl").exists():
            previous = [
                json.loads(line)
                for line in (directory / "events.jsonl").read_text().splitlines()
            ]
        for stage in manifest["stages"]:
            name = stage["name"]
            if stopped:
                _event(
                    directory,
                    stage=name,
                    status="omitted",
                    reason="Previous stage failed technical verification",
                )
                continue
            saved = next(
                (
                    e
                    for e in reversed(previous)
                    if e.get("stage") == name and e.get("status") == "passed"
                ),
                None,
            )
            if saved:
                review = json.loads((directory / saved["review"]).read_text())
                if (
                    digest((directory / saved["review"]).read_bytes())
                    != saved["review_sha256"]
                ):
                    raise ValueError("Saved phase review changed")
                reviews[name] = review
                continue
            path = directory / stage["spec"]
            spec_data = json.loads(path.read_text())
            spec = FlowSpec.model_validate(spec_data)
            phase = path.parent.parent
            _validate(root, directory, manifest)
            _event(directory, stage=name, status="started")
            error_type = None
            try:
                if not _phase_run(root, phase, spec):
                    error_type = "FlowIncomplete"
            except Exception as error:  # noqa: BLE001 - record the phase failure without exposing credentials
                error_type = type(error).__name__
            review = review_phase(root, phase, spec_data)
            review["runner_error_type"] = error_type
            if error_type:
                review["technical_pass"] = False
            relative = f"{name}/summary/review-{uuid4().hex[:8]}.json"
            (directory / relative).write_bytes(json_bytes(review))
            reviews[name] = review
            status = "passed" if review["technical_pass"] else "stopped"
            _event(
                directory,
                stage=name,
                status=status,
                review=relative,
                review_sha256=digest((directory / relative).read_bytes()),
            )
            stopped = status != "passed"
        from llm_transitivity.analysis.followup_report import write_report

        write_report(root, directory, manifest, reviews)
        return not stopped
