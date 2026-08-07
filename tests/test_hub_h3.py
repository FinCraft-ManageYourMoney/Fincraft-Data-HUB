"""Minimal Hub H3 tests: parquet exists + manifest SHA matches files."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "out"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    # Ensure artifacts
    for script in ("build_parquet.py", "build_manifest.py"):
        rc = subprocess.call([sys.executable, str(ROOT / "scripts" / script)])
        if rc != 0:
            print(f"FAIL {script} exit={rc}", file=sys.stderr)
            return rc

    manifest_path = OUT / "manifest.json"
    if not manifest_path.exists():
        print("FAIL missing manifest.json", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("schema_version") == 1
    assert manifest.get("files"), "empty files[]"

    for entry in manifest["files"]:
        path = OUT / entry["name"]
        assert path.exists(), path
        got = sha256_file(path)
        assert got == entry["sha256"], (entry["name"], got, entry["sha256"])
        assert entry["rows"] > 0

    print(f"PASS HUB-03 style checks ({len(manifest['files'])} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
