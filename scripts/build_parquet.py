"""Build Parquet packages from local raw CSV (Hub H3).

Inputs (data/raw/):
  - {TICKER}_YYYY-MM-DD.csv  (normalized OHLCV from fetch_stooq.py)
  - fx_nbp_a_YYYY-MM-DD.csv  (from fetch_nbp_fx.py)

Outputs (data/out/):
  - prices_eod_{year}.parquet
  - fx_nbp_a.parquet
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "out"


def _require_pyarrow():
    try:
        import pyarrow as pa  # noqa: F401
        import pyarrow.parquet as pq  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            "Missing pyarrow. Run: pip install -r requirements.txt\n" + str(e)
        ) from e


def load_price_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(RAW.glob("*_????-??-??.csv")):
        if path.name.startswith("fx_nbp_a_"):
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if not r.get("ticker") or not r.get("date"):
                    continue
                rows.append(
                    {
                        "ticker": r["ticker"],
                        "date": r["date"],
                        "open": r.get("open") or None,
                        "high": r.get("high") or None,
                        "low": r.get("low") or None,
                        "close": r.get("close") or None,
                        "volume": r.get("volume") or None,
                        "source": r.get("source") or "UNKNOWN",
                    }
                )
    # de-dupe ticker+date keeping last
    keyed = {(r["ticker"], r["date"]): r for r in rows}
    return [keyed[k] for k in sorted(keyed)]


def load_fx_rows() -> list[dict]:
    candidates = sorted(RAW.glob("fx_nbp_a_*.csv"))
    if not candidates:
        return []
    path = candidates[-1]
    rows: list[dict] = []
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "pair": r["pair"],
                    "date": r["date"],
                    "rate_mid": r["rate_mid"],
                    "source": r.get("source") or "NBP_A",
                }
            )
    keyed = {(r["pair"], r["date"]): r for r in rows}
    return [keyed[k] for k in sorted(keyed)]


def write_prices(rows: list[dict]) -> Path | None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print("WARN: no price rows", file=sys.stderr)
        return None
    year = date.today().year
    table = pa.Table.from_pydict(
        {
            "ticker": [r["ticker"] for r in rows],
            "date": [r["date"] for r in rows],
            "open": [r["open"] for r in rows],
            "high": [r["high"] for r in rows],
            "low": [r["low"] for r in rows],
            "close": [r["close"] for r in rows],
            "volume": [r["volume"] for r in rows],
            "source": [r["source"] for r in rows],
        }
    )
    out = OUT / f"prices_eod_{year}.parquet"
    pq.write_table(table, out, compression="snappy")
    print(f"OK  prices -> {out.name} ({len(rows)} rows)")
    return out


def write_fx(rows: list[dict]) -> Path | None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print("WARN: no FX rows", file=sys.stderr)
        return None
    table = pa.Table.from_pydict(
        {
            "pair": [r["pair"] for r in rows],
            "date": [r["date"] for r in rows],
            "rate_mid": [r["rate_mid"] for r in rows],
            "source": [r["source"] for r in rows],
        }
    )
    out = OUT / "fx_nbp_a.parquet"
    pq.write_table(table, out, compression="snappy")
    print(f"OK  fx     -> {out.name} ({len(rows)} rows)")
    return out


def main() -> int:
    _require_pyarrow()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    prices = write_prices(load_price_rows())
    fx = write_fx(load_fx_rows())
    if prices is None and fx is None:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
