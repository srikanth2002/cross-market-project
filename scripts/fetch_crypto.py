import requests
import sqlite3
import pandas as pd
import time

DB_PATH = "market.db"

def get_with_retry(url, params, max_retries=6):
    """GET request with exponential backoff on 429 (rate limit) errors."""
    wait = 10
    for attempt in range(1, max_retries + 1):
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 429:
            print(f"  Rate limited (429). Waiting {wait}s before retry {attempt}/{max_retries}...")
            time.sleep(wait)
            wait = min(wait * 2, 90)  # cap the backoff at 90s
            continue
        response.raise_for_status()
        return response
    # last attempt, let it raise naturally if it still fails
    response.raise_for_status()
    return response

def fetch_crypto_metadata():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    all_rows = []
    page = 1

    while True:
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "sparkline": "false"
        }

        response = get_with_retry(url, params)
        data = response.json()

        if not data:
            break

        for coin in data:
            last_updated = coin.get("last_updated", "")
            all_rows.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol"),
                "name": coin.get("name"),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "total_volume": coin.get("total_volume"),
                "circulating_supply": coin.get("circulating_supply"),
                "total_supply": coin.get("total_supply"),
                "ath": coin.get("ath"),
                "atl": coin.get("atl"),
                "date": last_updated[:10] if last_updated else None
            })

        print(f"  Fetched page {page} ({len(data)} coins)")
        page += 1
        time.sleep(8)  # free-tier CoinGecko is strict (~5-15 calls/min) - be generous

        # stop once we've paged through everything available
        if len(data) < 250:
            break

    df = pd.DataFrame(all_rows)
    return df

def save_metadata(df):
    # Delete+insert (instead of to_sql replace) so the PRIMARY KEY / schema
    # defined in create_db.py is preserved across runs.
    conn = sqlite3.connect(DB_PATH)
    cols = [
        "id", "symbol", "name", "current_price", "market_cap",
        "market_cap_rank", "total_volume", "circulating_supply",
        "total_supply", "ath", "atl", "date"
    ]
    conn.execute("DELETE FROM crypto_prices")  # clear child rows first (FK)
    conn.execute("DELETE FROM cryptocurrencies")
    conn.executemany(
        f"INSERT INTO cryptocurrencies ({', '.join(cols)}) "
        f"VALUES ({', '.join(['?'] * len(cols))})",
        df[cols].itertuples(index=False, name=None)
    )
    conn.commit()
    conn.close()

def fetch_top3_prices(top3_ids):
    conn = sqlite3.connect(DB_PATH)

    conn.execute("DELETE FROM crypto_prices")

    for coin_id in top3_ids:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": "365"
        }

        print(f"  Fetching 365-day prices for {coin_id} ...")
        response = get_with_retry(url, params)
        data = response.json()

        prices = data.get("prices", [])
        rows = []
        for item in prices:
            timestamp_ms, price = item
            date = pd.to_datetime(timestamp_ms, unit="ms").strftime("%Y-%m-%d")
            rows.append((coin_id, date, float(price)))

        conn.executemany(
            "INSERT INTO crypto_prices (coin_id, date, price_usd) VALUES (?, ?, ?)",
            rows
        )
        time.sleep(8)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    df = fetch_crypto_metadata()
    save_metadata(df)
    print(f"Fetched {len(df)} coins across pagination.")

    top3 = df.sort_values("market_cap_rank").head(3)["id"].tolist()
    print("Top 3 coins:", top3)

    fetch_top3_prices(top3)
    print("Crypto data inserted successfully.")