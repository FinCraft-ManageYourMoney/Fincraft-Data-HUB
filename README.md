# FinCraft Data Hub

**FinCraft Data Hub** to publiczne źródło codziennych notowań rynkowych dla aplikacji FinCraft.

## Co to jest

- Wspólna, otwarta paczka cen i kursów (akcje, ETF, waluty).
- Aktualizowana automatycznie — aplikacja FinCraft może z niej pobierać dane do wyceny portfela.
- **Nie zawiera** żadnych danych użytkowników, transakcji ani portfeli.

## Status

**H0–H3:** watchlista + fetch + NBP + Parquet + manifest SHA.

```powershell
cd C:\Users\user\Desktop\Fincraft-Data-HUB
pip install -r requirements.txt
python scripts/fetch_stooq.py
python scripts/fetch_nbp_fx.py
python scripts/build_parquet.py
python scripts/build_manifest.py
python tests/test_hub_h3.py
```

Stooq CSV bywa blokowane — wtedy Yahoo. Artefakty lokalne w `data/` (gitignored). Dalej: H4 Release `data-latest`.

## Struktura

```
config/tickers_watchlist.csv
scripts/fetch_stooq.py
scripts/fetch_nbp_fx.py
scripts/build_parquet.py
scripts/build_manifest.py
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
