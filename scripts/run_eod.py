"""End-of-day Hub pipeline orchestrator (H4).

Runs fetch -> parquet -> manifest + self-check (HUB-03).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(name: str) -> int:
    path = SCRIPTS / name
    print(f"\n==> {name}")
    rc = subprocess.call([sys.executable, str(path)], cwd=ROOT)
    if rc != 0:
        print(f"FAIL {name} exit={rc}", file=sys.stderr)
    return rc


def main() -> int:
    steps = (
        "fetch_stooq.py",
        "fetch_nbp_fx.py",
        "build_parquet.py",
        "build_manifest.py",
    )
    for step in steps:
        if run(step) != 0:
            return 1

    rc = subprocess.call([sys.executable, str(ROOT / "tests" / "test_hub_h3.py")], cwd=ROOT)
    if rc != 0:
        print("FAIL test_hub_h3", file=sys.stderr)
        return rc

    print("\nEOD pipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
