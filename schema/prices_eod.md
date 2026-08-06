# Prices EOD (Parquet target schema — H3)

| Column | Type | Notes |
|---|---|---|
| ticker | string | Watchlist ticker (e.g. AAPL) |
| stooq_symbol | string | Stooq symbol used to fetch |
| date | date | Session date |
| open | decimal string | |
| high | decimal string | |
| low | decimal string | |
| close | decimal string | |
| volume | int64 \| null | |
| source | string | `STOOQ` \| `YAHOO` |
