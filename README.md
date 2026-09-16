# Cross-Market Analysis: Crypto, Oil & Stocks (SQL + Streamlit)

Compares Bitcoin/Ethereum/top-3 crypto, WTI crude oil, and global stock
indices (S&P 500, NASDAQ, NIFTY) using a SQLite database and a 3-page
Streamlit dashboard.

## Folder structure

```
cross_market_project/
├── scripts/
│   ├── create_db.py     # creates market.db and all 4 tables (with FK)
│   ├── fetch_crypto.py  # CoinGecko: coin metadata (paginated) + top-3 365-day prices
│   ├── fetch_oil.py     # WTI daily oil prices (2020-2026) from GitHub dataset
│   └── fetch_stocks.py  # Yahoo Finance: ^GSPC, ^IXIC, ^NSEI (2020-2025)
├── run_all.py           # runs all 4 scripts above in order
├── app.py               # Streamlit app (3 pages)
├── queries.sql          # all 30 required SQL queries, standalone
├── requirements.txt
├── market.db            # generated after running run_all.py
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## 1. Build the database

Run from the project root (this folder, the one containing `run_all.py`
and the `scripts/` folder):

```bash
python run_all.py
```

This creates `market.db` in the project root and populates all four
tables: `cryptocurrencies`, `crypto_prices`, `oil_prices`, `stock_prices`.

You can also run the individual scripts one by one if you only need to
refresh one data source, e.g. `python scripts/fetch_oil.py` (still run
from the project root, so the `market.db` path resolves correctly).

## 2. Run the Streamlit app

```bash
streamlit run app.py
```

### Pages
1. **Filters & Data Exploration** - date-range filter, Bitcoin/Oil/S&P
   500/NIFTY averages, and a daily market snapshot (SQL JOIN).
2. **SQL Query Runner** - pick any of the 30 required queries from a
   dropdown and run it against the database.
3. **Top 3 Crypto Analysis** - pick one of the top-3 coins, filter by
   date range, view the price trend and table.

## Notes / known limitations

- Crypto price history is limited to the last ~365 days (CoinGecko
  free-tier limit on `market_chart`), while oil and stock data go back
  to 2020. Dates outside the crypto range show "N/A" in the snapshot.
- Prices are stored in USD (`price_usd`) across all tables for
  consistency, even though the original CoinGecko coin-list endpoint in
  the spec uses `vs_currency=inr`.
- `crypto_prices.coin_id` is a foreign key referencing
  `cryptocurrencies.id`.
