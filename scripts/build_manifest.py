"""Build Hub manifest.json with SHA-256 of Parquet files (Hub H3).

Contract: docs/09_DATA_HUB.md §6
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "out"
MANIFEST = OUT / "manifest.json"


def sha256_file(path: Path) -> str:
    # Streaming hash — pattern from Python docs / StackOverflow hashlib large files.
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parquet_meta(path: Path) -> dict:
    import pyarrow.parquet as pq

    table = pq.read_table(path, columns=None)
    rows = table.num_rows
    date_min = date_max = None
    names = set(table.column_names)
    if "date" in names:
        dates = [str(x) for x in table.column("date").to_pylist() if x]
        if dates:
            date_min = min(dates)
            date_max = max(dates)
    return {
        "name": path.name,
        "url_path": path.name,
        "sha256": sha256_file(path),
        "rows": rows,
        **({"date_min": date_min, "date_max": date_max} if date_min else {}),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(OUT.glob("*.parquet"))
    if not files:
        print("ERROR: no parquet in data/out — run build_parquet.py first", file=sys.stderr)
        return 2

    try:
        import pyarrow.parquet  # noqa: F401
    except ImportError as e:
        raise SystemExit("Missing pyarrow. pip install -r requirements.txt") from e

    entries = []
    for path in files:
        meta = parquet_meta(path)
        print(f"OK  {meta['name']} sha256={meta['sha256'][:16]}… rows={meta['rows']}")
        entries.append(meta)

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hub_version": "0.1.0",
        "files": entries,
        "sources_degraded": [],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST}")

    # Self-check: re-hash matches manifest (HUB-03).
    for entry in entries:
        path = OUT / entry["name"]
        got = sha256_file(path)
        if got != entry["sha256"]:
            print(f"FAIL SHA mismatch {entry['name']}", file=sys.stderr)
            return 3
    print("SHA self-check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
