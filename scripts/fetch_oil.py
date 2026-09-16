import pandas as pd
import sqlite3

DB_PATH = "market.db"

def fetch_oil_data():
    url = "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-daily.csv"
    df = pd.read_csv(url)

    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= "2020-01-01") & (df["Date"] <= "2026-01-31")]

    df = df.rename(columns={
        "Date": "date",
        "Price": "price_usd"
    })

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[["date", "price_usd"]]

    return df

def save_oil_data(df):
    # Delete+insert (instead of to_sql replace) so the PRIMARY KEY on
    # `date` defined in create_db.py is preserved across runs.
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM oil_prices")
    conn.executemany(
        "INSERT INTO oil_prices (date, price_usd) VALUES (?, ?)",
        df[["date", "price_usd"]].itertuples(index=False, name=None)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    df = fetch_oil_data()
    save_oil_data(df)
    print("Oil data inserted successfully.")
