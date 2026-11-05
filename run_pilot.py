"""Run the pilot with all results and evidence in one unique run directory."""

import argparse
import json
from pathlib import Path
from zipfile import BadZipFile

from dotenv import load_dotenv
from inspect_ai.log import read_eval_log
from inspect_flow.api import dump_spec, run

from collect_openrouter import export_run
from inspect_tasks import PROJECT_ROOT
from pilot_config import build_pilot_spec
from prepare_pilot import MANIFEST, digest, json_bytes, verify


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
    if logs:
        try:
            export_run(archive)
            export_status = "exported"
        except (OSError, ValueError, RuntimeError, KeyError, BadZipFile) as error:
            export_status = f"failed: {type(error).__name__}"
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


def execute(spec, root: Path) -> bool:
    archive = prepare_archive(spec, root)
    success, error_type = None, None
    print(f"Results: {archive}")
    try:
        result = run(spec=spec)
        success = result.success
        return success
    except BaseException as error:
        error_type = type(error).__name__
        raise
    finally:
        finalize_archive(archive, flow_success=success, error_type=error_type)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check the spec without creating an archive or calling models",
    )
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    spec = build_pilot_spec()
    if args.dry_run:
        run(spec=spec, dry_run=True)
    elif not execute(spec, PROJECT_ROOT):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
