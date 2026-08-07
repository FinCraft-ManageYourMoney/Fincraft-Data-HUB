# FinCraft Data Hub

**FinCraft Data Hub** to publiczne źródło codziennych notowań rynkowych dla aplikacji FinCraft.

## Co to jest

- Wspólna, otwarta paczka cen i kursów (akcje, ETF, waluty).
- Aktualizowana automatycznie — aplikacja FinCraft może z niej pobierać dane do wyceny portfela.
- **Nie zawiera** żadnych danych użytkowników, transakcji ani portfeli.

## Status

**H0–H4:** watchlista + fetch + NBP + Parquet + manifest SHA + GitHub Actions Release `data-latest`.

```powershell
cd C:\Users\user\Desktop\Fincraft-Data-HUB
pip install -r requirements.txt
python scripts/run_eod.py
```

Stooq CSV bywa blokowane — wtedy Yahoo. Artefakty lokalne w `data/` (gitignored). Release: tag `data-latest` (cron pn–pt ~22:30 CET).

### Pierwszy Release (H4 — ręcznie)

1. GitHub → repo **Fincraft-Data-HUB** → **Actions** → **EOD Data Hub**
2. **Run workflow** → branch `main` → Run
3. Po sukcesie: **Releases** → `data-latest` (manifest.json + Parquet)
4. W App: **Odśwież notowania z Hub** (Tracker pobiera i weryfikuje SHA)

Bez Release App zwróci `HUB_RELEASE_NOT_FOUND` (fallback: lokalny `hub_cache` jeśli wcześniej zsynchronizowano).

## Struktura

```
config/tickers_watchlist.csv
scripts/run_eod.py
scripts/fetch_stooq.py
scripts/fetch_nbp_fx.py
scripts/build_parquet.py
scripts/build_manifest.py
.github/workflows/eod.yml
schema/prices_eod.md
schema/fx_nbp_a.md
tests/test_hub_h3.py
requirements.txt
```

## Powiązane projekty

| Projekt | Opis |
|---|---|
| [Fincraft](https://github.com/FinCraft-ManageYourMoney/Fincraft) | Aplikacja desktopowa FinCraft |
| Fincraft-Docs | Prywatna dokumentacja produktowa (wewnętrzna) |

---

© FinCraft — Manage Your Money
