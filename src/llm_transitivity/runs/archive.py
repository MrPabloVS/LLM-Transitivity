"""Run the pilot with all results and evidence in one unique run directory."""

import json
from pathlib import Path
from zipfile import BadZipFile

from inspect_ai.log import read_eval_log
from inspect_flow.api import dump_spec

from llm_transitivity.datasets.pilot import MANIFEST, verify
from llm_transitivity.evidence.serialization import digest, json_bytes
from llm_transitivity.runs.export import export_run


def prepare_archive(spec, root: Path) -> Path:
    """Freeze inputs and source evidence before the first model request."""
    manifest = verify(root)
    archive = Path(spec.log_dir).parent
    if Path(spec.log_dir).name != "inspect":
        raise ValueError("The managed log directory must end in /inspect")
    spec.options.metadata["archive_mode"] = "managed"
    flow_payload = json_bytes(dump_spec(spec))
    files = set(spec.options.metadata["source_sha256"])
    files.add(str(MANIFEST))
    files.add(manifest["system_prompt"]["path"])
    files.update(e["pilot_path"] for e in manifest["datasets"])
    expected_hashes = dict(spec.options.metadata["source_sha256"])
    expected_hashes[str(MANIFEST)] = spec.options.metadata["pilot_manifest_sha256"]
    expected_hashes[manifest["system_prompt"]["path"]] = manifest["system_prompt"][
        "sha256"
    ]
    expected_hashes.update(
        {e["pilot_path"]: e["pilot_sha256"] for e in manifest["datasets"]}
    )
    snapshots, hashes = {}, {}
    for relative in sorted(files):
        source = root / relative
        payload = source.read_bytes()
        expected = expected_hashes[relative]
        if expected and digest(payload) != expected:
            raise ValueError(
                f"{relative}: evidence changed after configuration was built"
            )
        snapshots[relative] = payload
        hashes[relative] = digest(payload)
    archive.mkdir(parents=True, exist_ok=False)
    for name in ["inspect", "openrouter_calls", "provenance", "summary"]:
        (archive / name).mkdir()
    for relative, payload in snapshots.items():
        target = archive / "provenance" / "snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    (archive / "provenance" / "run.json").write_bytes(json_bytes(spec.options.metadata))
    (archive / "provenance" / "snapshot_hashes.json").write_bytes(json_bytes(hashes))
    (archive / "provenance" / "flow_spec.json").write_bytes(flow_payload)
    return archive


def finalize_archive(
    archive: Path, *, flow_success: bool | None, error_type: str | None = None
) -> None:
    """Keep partial results discoverable even when a run fails or is interrupted."""
    logs = sorted((archive / "inspect").rglob("*.eval"))
    entries = []
    for path in logs:
        try:
            log = read_eval_log(str(path))
            md = log.eval.metadata or {}
            entries.append(
                {
                    "path": str(path.relative_to(archive)),
                    "sha256": digest(path.read_bytes()),
                    "status": log.status,
                    "task": log.eval.task,
                    "model": log.eval.model,
                    "dataset": md.get("dataset_name"),
                    "generation_group": md.get("generation_group"),
                    "provider_requested": md.get("requested_provider"),
                    "sample_count": len(log.samples or []),
                    "sample_errors": sum(
                        sample.error is not None for sample in log.samples or []
                    ),
                }
            )
        except (OSError, ValueError, RuntimeError, KeyError, BadZipFile) as error:
            entries.append(
                {
                    "path": str(path.relative_to(archive)),
                    "read_error_type": type(error).__name__,
                }
            )
    export_status = "no logs"
    export_error = None
    if logs:
        try:
            export_run(archive)
            export_status = "exported"
        except (OSError, ValueError, RuntimeError, KeyError, BadZipFile) as error:
            export_status = f"failed: {type(error).__name__}"
            export_error = error
    report = {
        "flow_success": flow_success,
        "runner_error_type": error_type,
        "call_export_status": export_status,
        "logs": entries,
        "note": "Log index only; metrics and billing need a separate analysis.",
    }
    with (archive / "summary" / "log_index.json").open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")

    if export_error is not None:
        raise export_error
