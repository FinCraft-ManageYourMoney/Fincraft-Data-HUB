# FinCraft Data Hub

**FinCraft Data Hub** to publiczne źródło codziennych notowań rynkowych dla aplikacji FinCraft.

## Co to jest

- Wspólna, otwarta paczka cen i kursów (akcje, ETF, waluty).
- Aktualizowana automatycznie — aplikacja FinCraft może z niej pobierać dane do wyceny portfela.
- **Nie zawiera** żadnych danych użytkowników, transakcji ani portfeli.

## Status

**H0–H1:** watchlista 10 tickerów + lokalny fetch.

```powershell
cd C:\Users\user\Desktop\Fincraft-Data-HUB
python scripts/fetch_stooq.py
```

Stooq CSV bywa blokowane (`Access denied` / `Odmowa dostępu`) nawet po bramce PoW — skrypt wtedy bierze **Yahoo** (zgodnie z fallbackiem z docs). Artefakty: `data/raw/` (gitignored). Dalej: H2 NBP, H3 Parquet+manifest, H4 Release.

## Struktura

```
config/tickers_watchlist.csv
scripts/fetch_stooq.py
schema/prices_eod.md
```

## Powiązane projekty

| Projekt | Opis |
|---|---|
| [Fincraft](https://github.com/FinCraft-ManageYourMoney/Fincraft) | Aplikacja desktopowa FinCraft |
| Fincraft-Docs | Prywatna dokumentacja produktowa (wewnętrzna) |

---

© FinCraft — Manage Your Money
