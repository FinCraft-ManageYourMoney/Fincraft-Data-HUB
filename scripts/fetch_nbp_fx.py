"""Fetch NBP table A mid rates for USD/PLN and EUR/PLN (Hub H2).

API: https://api.nbp.pl/api/exchangerates/...
Writes normalized CSV under data/raw/.
"""

from __future__ import annotations

import csv
import json
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"
UA = "FinCraft-DataHub/1.0"
CODES = ("USD", "EUR")
DAYS_BACK = 120


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        return ctx


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_code(code: str, start: date, end: date) -> list[dict[str, str]]:
    # NBP limits range requests; chunk by ~90 days.
    rows: list[dict[str, str]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=89), end)
        url = (
            f"https://api.nbp.pl/api/exchangerates/rates/a/{code.lower()}/"
            f"{cursor.isoformat()}/{chunk_end.isoformat()}/?format=json"
        )
        try:
            payload = fetch_json(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cursor = chunk_end + timedelta(days=1)
                continue
            raise
        for r in payload.get("rates", []):
            rows.append(
                {
                    "pair": f"{code}/PLN",
                    "date": r["effectiveDate"],
                    "rate_mid": str(r["mid"]),
                    "source": "NBP_A",
                }
            )
        cursor = chunk_end + timedelta(days=1)
    # de-dupe by date
    by_date = {r["date"]: r for r in rows}
    return [by_date[k] for k in sorted(by_date)]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    end = date.today()
    start = end - timedelta(days=DAYS_BACK)
    today = end.isoformat()
    all_rows: list[dict[str, str]] = []
    failed: list[str] = []

    for code in CODES:
        try:
            rows = fetch_code(code, start, end)
            print(f"OK  {code}/PLN -> {len(rows)} rates")
            all_rows.extend(rows)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            print(f"FAIL {code}: {e}", file=sys.stderr)
            failed.append(code)

    out = OUT_DIR / f"fx_nbp_a_{today}.csv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair", "date", "rate_mid", "source"])
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    print(f"Wrote {len(all_rows)} rows -> {out.name}")
    if failed:
        print("Failed:", ", ".join(failed), file=sys.stderr)
        return 2 if not all_rows else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
