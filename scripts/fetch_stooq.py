"""Fetch EOD OHLCV for the V1 watchlist (Hub H1).

Primary: Stooq CSV (with PoW gate).
Fallback: Yahoo chart API when Stooq returns Access denied / empty
(docs/09 — Yahoo only for gaps, not a permanent Hub replacement).

Writes normalized CSV under data/raw/ (gitignored).
"""

from __future__ import annotations

import csv
import hashlib
import http.cookiejar
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "config" / "tickers_watchlist.csv"
OUT_DIR = ROOT / "data" / "raw"
STOOQ_BASE = "https://stooq.pl"
UA = "Mozilla/5.0 (compatible; FinCraft-Data-HUB/0.1)"


def load_watchlist() -> list[dict[str, str]]:
    with WATCHLIST.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def http_get(opener: urllib.request.OpenerDirector, url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with opener.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def solve_pow(opener: urllib.request.OpenerDirector, html: str, base: str) -> None:
    import re

    m = re.search(r'const c="([^"]+)",d=(\d+)', html)
    if not m:
        raise RuntimeError("Stooq PoW challenge not found")
    challenge, difficulty = m.group(1), int(m.group(2))
    prefix = "0" * difficulty
    n = 0
    while True:
        if hashlib.sha256(f"{challenge}{n}".encode()).hexdigest().startswith(prefix):
            break
        n += 1
        if n > 5_000_000:
            raise RuntimeError("Stooq PoW solve timeout")
    body = urllib.parse.urlencode({"c": challenge, "n": str(n)}).encode()
    req = urllib.request.Request(
        f"{base}/__verify",
        data=body,
        headers={
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": base,
            "Referer": base + "/",
        },
        method="POST",
    )
    with opener.open(req, timeout=30) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Stooq verify HTTP {resp.status}")


def ensure_stooq_session(opener: urllib.request.OpenerDirector) -> None:
    home = http_get(opener, STOOQ_BASE + "/")
    if "const c=" in home or "requires JavaScript" in home:
        solve_pow(opener, home, STOOQ_BASE)


def fetch_stooq_csv(opener: urllib.request.OpenerDirector, symbol: str) -> str:
    url = f"{STOOQ_BASE}/q/d/l/?s={urllib.parse.quote(symbol.lower())}&i=d"
    body = http_get(opener, url)
    if body.lstrip().startswith("<!DOCTYPE") or "const c=" in body:
        solve_pow(opener, body, STOOQ_BASE)
        body = http_get(opener, url)
    head = body.splitlines()[0] if body.strip() else ""
    lowered = head.lower()
    if "access denied" in lowered or "odmowa" in lowered:
        raise RuntimeError("STOOQ_ACCESS_DENIED")
    if "Date" not in head:
        raise RuntimeError(f"unexpected Stooq header: {head[:80]!r}")
    return body


def fetch_yahoo_rows(yahoo_symbol: str) -> list[dict[str, str]]:
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(yahoo_symbol)}"
        "?interval=1d&range=2y"
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        raise RuntimeError("Yahoo empty result")
    block = result[0]
    timestamps = block.get("timestamp") or []
    quote = ((block.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    rows: list[dict[str, str]] = []
    for i, ts in enumerate(timestamps):
        c = closes[i] if i < len(closes) else None
        if c is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        rows.append(
            {
                "Date": day,
                "Open": _num(opens[i] if i < len(opens) else None),
                "High": _num(highs[i] if i < len(highs) else None),
                "Low": _num(lows[i] if i < len(lows) else None),
                "Close": _num(c),
                "Volume": _vol(volumes[i] if i < len(volumes) else None),
            }
        )
    if not rows:
        raise RuntimeError("Yahoo produced 0 bars")
    return rows


def _num(v: float | None) -> str:
    if v is None:
        return ""
    return f"{v:.6f}".rstrip("0").rstrip(".")


def _vol(v: float | None) -> str:
    if v is None:
        return ""
    return str(int(v))


def write_normalized_csv(
    path: Path,
    rows: list[dict[str, str]],
    *,
    ticker: str,
    source: str,
) -> int:
    fieldnames = ["ticker", "date", "open", "high", "low", "close", "volume", "source"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "ticker": ticker,
                    "date": r["Date"],
                    "open": r["Open"],
                    "high": r["High"],
                    "low": r["Low"],
                    "close": r["Close"],
                    "volume": r.get("Volume", ""),
                    "source": source,
                }
            )
    return len(rows)


def stooq_to_rows(body: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(body)))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_watchlist()
    if not rows:
        print("ERROR: empty watchlist", file=sys.stderr)
        return 1

    opener = build_opener()
    try:
        ensure_stooq_session(opener)
    except Exception as e:  # noqa: BLE001 — warm-up is best-effort
        print(f"WARN: Stooq session: {e}", file=sys.stderr)

    ok = 0
    failed: list[str] = []
    today = date.today().isoformat()

    for row in rows:
        ticker = row["ticker"]
        stooq_symbol = row["stooq_symbol"]
        yahoo_symbol = row["yahoo_symbol"]
        out = OUT_DIR / f"{ticker}_{today}.csv"
        try:
            source = "STOOQ"
            try:
                raw = fetch_stooq_csv(opener, stooq_symbol)
                bars = stooq_to_rows(raw)
            except Exception as stooq_err:  # noqa: BLE001
                print(f"  fallback {ticker}: Stooq -> Yahoo ({stooq_err})")
                bars = fetch_yahoo_rows(yahoo_symbol)
                source = "YAHOO"
            n = write_normalized_csv(out, bars, ticker=ticker, source=source)
            print(f"OK  {ticker:6} source={source:6} -> {n} rows -> {out.name}")
            ok += 1
        except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as e:
            print(f"FAIL {ticker:6}: {e}", file=sys.stderr)
            failed.append(ticker)

    print(f"\nDone: {ok}/{len(rows)} ok")
    if failed:
        print("Failed:", ", ".join(failed), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
