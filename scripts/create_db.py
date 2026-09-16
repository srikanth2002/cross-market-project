import sqlite3

conn = sqlite3.connect("market.db")
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    current_price REAL,
    market_cap REAL,
    market_cap_rank INTEGER,
    total_volume REAL,
    circulating_supply REAL,
    total_supply REAL,
    ath REAL,
    atl REAL,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS crypto_prices (
    coin_id TEXT,
    date TEXT,
    price_usd REAL,
    FOREIGN KEY (coin_id) REFERENCES cryptocurrencies(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS oil_prices (
    date TEXT PRIMARY KEY,
    price_usd REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_prices (
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    ticker TEXT
)
""")

conn.commit()
conn.close()

print("Database and tables created successfully.")
