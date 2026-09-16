import yfinance as yf
import pandas as pd
import sqlite3

DB_PATH = "market.db"

def fetch_stock_data():
    tickers = ["^GSPC", "^IXIC", "^NSEI"]
    all_data = []

    for ticker in tickers:
        df = yf.download(
            ticker,
            start="2020-01-01",
            end="2025-09-30",
            auto_adjust=False,
            progress=False
        )

        if df.empty:
            continue

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        df["ticker"] = ticker
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        needed_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "ticker"]
        df = df[needed_cols]
        df.columns = ["date", "open", "high", "low", "close", "volume", "ticker"]

        all_data.append(df)

    if all_data:
        return pd.concat(all_data, ignore_index=True)

    return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "ticker"])

def save_stock_data(df):
    # Delete+insert (instead of to_sql replace) so the schema defined
    # in create_db.py is preserved across runs.
    conn = sqlite3.connect(DB_PATH)
    cols = ["date", "open", "high", "low", "close", "volume", "ticker"]
    conn.execute("DELETE FROM stock_prices")
    conn.executemany(
        f"INSERT INTO stock_prices ({', '.join(cols)}) "
        f"VALUES ({', '.join(['?'] * len(cols))})",
        df[cols].itertuples(index=False, name=None)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    df = fetch_stock_data()
    save_stock_data(df)
    print("Stock data inserted successfully.")
