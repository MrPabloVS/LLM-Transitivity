"""Record experiment identity and reproducible provenance without credentials."""

import platform
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from llm_transitivity.datasets.pilot import MANIFEST
from llm_transitivity.domain.config import GENERATION_POLICY, GenerationPolicy
from llm_transitivity.evidence.serialization import digest

EXPERIMENT_ID = "llm-transitivity-coverage-pilot-v1"
SCORING_VERSION = "source-label-deterministic-v2"


def package_sources(root: Path) -> list[str]:
    """Allow only Python sources inside the experiment package."""
    return sorted(
        str(path.relative_to(root))
        for path in (root / "src/llm_transitivity").rglob("*.py")
    )


def run_metadata(
    root: Path, manifest: dict, *, policy: GenerationPolicy = GENERATION_POLICY
) -> dict:
    """Snapshot only allowlisted code, package versions, and Git state."""

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True
        ).strip()

    files = [".python-version", "pyproject.toml", "uv.lock"]
    files += package_sources(root)
    return {
        "metadata_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "experiment_run_id": str(uuid4()),
        "configuration_created_utc": datetime.now(UTC).isoformat(),
        "phase": "coverage-pilot",
        "protocol": "zeroShot",
        "scoring_version": SCORING_VERSION,
        "label_basis": "source-label agreement; logical validity not audited",
        "logical_validity_audited": False,
        "openrouter_capture": {
            "http_attempts": True,
            "full_response_json": True,
            "generation_lookup": "automatic, up to three read-only lookup attempts per id",
            "stored_content_lookup": "optional exporter flag; permissions may be restricted",
            "streaming": policy.stream,
            "credentials": "redacted",
        },
        "pilot_manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "original_revision": manifest["baseline_revision"],
        "selection": manifest["selection"],
        "cases_per_stratum": manifest["cases_per_stratum"],
        "pilot_case_count": sum(len(e["selected_rows"]) for e in manifest["datasets"]),
        "git": {
            "revision": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "dirty": bool(git("status", "--porcelain")),
        },
        "source_sha256": {path: digest((root / path).read_bytes()) for path in files},
        "runtime": {
            "python": platform.python_version(),
            "uv": subprocess.check_output(["uv", "--version"], text=True).strip(),
            "platform": platform.system(),
            "packages": {
                name: version(name)
                for name in [
                    "inspect-ai",
                    "inspect-flow",
                    "openai",
                    "python-dotenv",
                    "requests",
                    "tiktoken",
                ]
            },
        },
        "generation_policy": policy.metadata(),
    }
