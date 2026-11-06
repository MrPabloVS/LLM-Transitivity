"""Open DuckDB UI with views of a saved report."""

import argparse
import hashlib
import threading
from pathlib import Path


def register_views(connection, report: Path) -> None:
    """Register nonempty CSV tables and JSON cases without changing source files."""
    tables = sorted((report / "tables").glob("*.csv"))
    if not tables or not list((report / "data").glob("*.json")):
        raise ValueError("The report must contain tables/*.csv and data/*.json")
    connection.execute("CREATE SCHEMA IF NOT EXISTS report")
    for path in tables:
        if not path.stat().st_size:
            continue
        name = path.stem.replace('"', '""')
        source = str(path).replace("'", "''")
        connection.execute(
            f'CREATE OR REPLACE VIEW report."{name}" AS '
            f"SELECT * FROM read_csv_auto('{source}', sample_size=-1)"
        )
    source = str(report / "data/*.json").replace("'", "''")
    connection.execute(
        "CREATE OR REPLACE VIEW report.case_details AS "
        f"SELECT * FROM read_json_auto('{source}', union_by_name=true)"
    )


def main(root: Path, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--port", type=int, default=4213)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    report = (root / args.report).resolve()
    if not list((report / "tables").glob("*.csv")) or not list(
        (report / "data").glob("*.json")
    ):
        parser.error("The report must contain tables/*.csv and data/*.json")

    import duckdb

    identity = hashlib.sha256(str(report).encode()).hexdigest()[:16]
    database = root / ".local" / "duckdb" / f"{identity}.duckdb"
    database.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database)) as connection:
        register_views(connection, report)
        connection.execute("INSTALL ui")
        connection.execute("LOAD ui")
        connection.execute(f"SET ui_local_port = {args.port}")
        connection.execute(
            "CALL start_ui_server()" if args.no_browser else "CALL start_ui()"
        )
        print(f"DuckDB UI: http://localhost:{args.port}", flush=True)
        print("Open report in the database tree. Press Ctrl+C to stop.", flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            connection.execute("CALL stop_ui_server()")
