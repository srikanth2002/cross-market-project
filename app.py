import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Cross Market Analysis", layout="wide")

conn = sqlite3.connect("market.db")

st.title("💰🛢️📈 Cross-Market Analysis: Crypto, Oil & Stocks")

page = st.sidebar.selectbox(
    "Select Page",
    ["Filters & Data Exploration", "SQL Query Runner", "Top 3 Crypto Analysis"]
)

if page == "Filters & Data Exploration":
    st.header("Filters & Data Exploration")

    st.caption(
        "Note: crypto prices only cover the last ~365 days (CoinGecko free API limit), "
        "while oil and stock prices go back to 2020. Dates outside the crypto range will "
        "show 'N/A' for Bitcoin and the Daily Market Snapshot."
    )

    min_date = "2024-01-01"
    max_date = "2025-12-31"

    start_date = st.date_input("Start Date", pd.to_datetime(min_date))
    end_date = st.date_input("End Date", pd.to_datetime(max_date))

    start_date = str(start_date)
    end_date = str(end_date)

    btc_avg = pd.read_sql("""
        SELECT ROUND(AVG(price_usd), 2) AS avg_price
        FROM crypto_prices
        WHERE coin_id='bitcoin' AND date BETWEEN ? AND ?
    """, conn, params=(start_date, end_date))

    oil_avg = pd.read_sql("""
        SELECT ROUND(AVG(price_usd), 2) AS avg_price
        FROM oil_prices
        WHERE date BETWEEN ? AND ?
    """, conn, params=(start_date, end_date))

    sp_avg = pd.read_sql("""
        SELECT ROUND(AVG(close), 2) AS avg_close
        FROM stock_prices
        WHERE ticker='^GSPC' AND date BETWEEN ? AND ?
    """, conn, params=(start_date, end_date))

    nifty_avg = pd.read_sql("""
        SELECT ROUND(AVG(close), 2) AS avg_close
        FROM stock_prices
        WHERE ticker='^NSEI' AND date BETWEEN ? AND ?
    """, conn, params=(start_date, end_date))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bitcoin Avg", btc_avg.iloc[0, 0] if not btc_avg.empty else "N/A")
    col2.metric("Oil Avg", oil_avg.iloc[0, 0] if not oil_avg.empty else "N/A")
    col3.metric("S&P 500 Avg", sp_avg.iloc[0, 0] if not sp_avg.empty else "N/A")
    col4.metric("NIFTY Avg", nifty_avg.iloc[0, 0] if not nifty_avg.empty else "N/A")

    st.subheader("Daily Market Snapshot")

    query = """
        SELECT cp.date,
               cp.price_usd AS bitcoin_price,
               op.price_usd AS oil_price,
               sp1.close AS sp500_close,
               sp2.close AS nifty_close
        FROM crypto_prices cp
        LEFT JOIN oil_prices op ON cp.date = op.date
        LEFT JOIN stock_prices sp1 ON cp.date = sp1.date AND sp1.ticker='^GSPC'
        LEFT JOIN stock_prices sp2 ON cp.date = sp2.date AND sp2.ticker='^NSEI'
        WHERE cp.coin_id='bitcoin'
          AND cp.date BETWEEN ? AND ?
        ORDER BY cp.date
    """

    df = pd.read_sql(query, conn, params=(start_date, end_date))
    df = df.fillna("N/A")
    st.dataframe(df, use_container_width=True)

elif page == "SQL Query Runner":
    st.header("SQL Query Runner")

    query_dict = {
        # --- cryptocurrencies ---
        "1. Top 3 cryptocurrencies by market cap": """
            SELECT name, market_cap FROM cryptocurrencies
            ORDER BY market_cap DESC LIMIT 3
        """,
        "2. Coins with circulating supply > 90% of total supply": """
            SELECT name, circulating_supply, total_supply FROM cryptocurrencies
            WHERE total_supply > 0 AND circulating_supply >= 0.9 * total_supply
        """,
        "3. Coins within 10% of their all-time-high": """
            SELECT name, current_price, ath FROM cryptocurrencies
            WHERE ath > 0 AND current_price >= 0.9 * ath
        """,
        "4. Avg market cap rank of coins with volume > $1B": """
            SELECT ROUND(AVG(market_cap_rank), 2) AS avg_rank FROM cryptocurrencies
            WHERE total_volume > 1000000000
        """,
        "5. Most recently updated coin": """
            SELECT name, date FROM cryptocurrencies ORDER BY date DESC LIMIT 1
        """,

        # --- crypto_prices ---
        "6. Highest daily price of Bitcoin (last 365 days)": """
            SELECT MAX(price_usd) AS highest_bitcoin_price FROM crypto_prices
            WHERE coin_id='bitcoin'
        """,
        "7. Average daily price of Ethereum (past 1 year)": """
            SELECT ROUND(AVG(price_usd), 2) AS avg_ethereum_price FROM crypto_prices
            WHERE coin_id='ethereum'
        """,
        "8. Bitcoin daily price trend (Jan 2025)": """
            SELECT date, price_usd FROM crypto_prices
            WHERE coin_id='bitcoin' AND date BETWEEN '2025-01-01' AND '2025-01-31'
            ORDER BY date
        """,
        "9. Coin with highest average price over 1 year": """
            SELECT coin_id, ROUND(AVG(price_usd), 2) AS avg_price FROM crypto_prices
            GROUP BY coin_id ORDER BY avg_price DESC LIMIT 1
        """,
        "10. % change in Bitcoin price (Sep 2024 to Sep 2025)": """
            SELECT
              (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2025-09-16') AS end_price,
              (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16') AS start_price,
              ROUND((
                (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2025-09-16') -
                (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16')
              ) * 100.0 /
              (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16'), 2) AS pct_change
        """,

        # --- oil_prices ---
        "11. Highest oil price (last 5 years)": """
            SELECT MAX(price_usd) AS highest_oil_price FROM oil_prices
            WHERE date >= '2021-01-01'
        """,
        "12. Average oil price per year": """
            SELECT SUBSTR(date,1,4) AS year, ROUND(AVG(price_usd),2) AS avg_oil_price
            FROM oil_prices GROUP BY SUBSTR(date,1,4) ORDER BY year
        """,
        "13. Oil prices during COVID crash (Mar-Apr 2020)": """
            SELECT date, price_usd FROM oil_prices
            WHERE date BETWEEN '2020-03-01' AND '2020-04-30' ORDER BY date
        """,
        "14. Lowest oil price (last 10 years)": """
            SELECT MIN(price_usd) AS lowest_oil_price FROM oil_prices
            WHERE date >= '2016-01-01'
        """,
        "15. Oil price volatility per year (max-min)": """
            SELECT SUBSTR(date,1,4) AS year,
                   ROUND(MAX(price_usd) - MIN(price_usd), 2) AS volatility
            FROM oil_prices GROUP BY SUBSTR(date,1,4) ORDER BY year
        """,

        # --- stock_prices ---
        "16. All stock prices for ^GSPC": """
            SELECT * FROM stock_prices WHERE ticker='^GSPC' ORDER BY date
        """,
        "17. Highest closing price for NASDAQ (^IXIC)": """
            SELECT MAX(close) AS highest_nasdaq_close FROM stock_prices
            WHERE ticker='^IXIC'
        """,
        "18. Top 5 most volatile days for S&P 500": """
            SELECT date, ROUND(high-low,2) AS diff FROM stock_prices
            WHERE ticker='^GSPC' ORDER BY diff DESC LIMIT 5
        """,
        "19. Monthly average closing price per ticker": """
            SELECT ticker, SUBSTR(date,1,7) AS month, ROUND(AVG(close),2) AS avg_close
            FROM stock_prices GROUP BY ticker, SUBSTR(date,1,7) ORDER BY ticker, month
        """,
        "20. Average trading volume of NIFTY in 2024": """
            SELECT ROUND(AVG(volume), 2) AS avg_volume FROM stock_prices
            WHERE ticker='^NSEI' AND SUBSTR(date,1,4)='2024'
        """,

        # --- join queries ---
        "21. Bitcoin vs Oil average price in 2025": """
            SELECT
              (SELECT ROUND(AVG(price_usd),2) FROM crypto_prices
               WHERE coin_id='bitcoin' AND SUBSTR(date,1,4)='2025') AS btc_avg_2025,
              (SELECT ROUND(AVG(price_usd),2) FROM oil_prices
               WHERE SUBSTR(date,1,4)='2025') AS oil_avg_2025
        """,
        "22. Bitcoin vs S&P 500 (same dates)": """
            SELECT cp.date, cp.price_usd AS btc_price, sp.close AS sp500_close
            FROM crypto_prices cp
            JOIN stock_prices sp ON cp.date = sp.date AND sp.ticker='^GSPC'
            WHERE cp.coin_id='bitcoin' ORDER BY cp.date
        """,
        "23. Ethereum vs NASDAQ daily prices (2025)": """
            SELECT cp.date, cp.price_usd AS eth_price, sp.close AS nasdaq_close
            FROM crypto_prices cp
            JOIN stock_prices sp ON cp.date = sp.date AND sp.ticker='^IXIC'
            WHERE cp.coin_id='ethereum' AND SUBSTR(cp.date,1,4)='2025'
            ORDER BY cp.date
        """,
        "24. Oil price spikes (>5%) vs Bitcoin change": """
            WITH oil_change AS (
                SELECT date, price_usd,
                       ROUND((price_usd - LAG(price_usd) OVER (ORDER BY date)) * 100.0
                             / LAG(price_usd) OVER (ORDER BY date), 2) AS oil_pct_change
                FROM oil_prices
            )
            SELECT oc.date, oc.oil_pct_change, cp.price_usd AS btc_price
            FROM oil_change oc
            JOIN crypto_prices cp ON oc.date = cp.date AND cp.coin_id='bitcoin'
            WHERE oc.oil_pct_change > 5 ORDER BY oc.date
        """,
        "25. Top 3 coins vs Nifty (^NSEI) trend": """
            SELECT cp.coin_id, cp.date, cp.price_usd, sp.close AS nifty_close
            FROM crypto_prices cp
            JOIN stock_prices sp ON cp.date = sp.date AND sp.ticker='^NSEI'
            ORDER BY cp.coin_id, cp.date
        """,
        "26. S&P 500 vs crude oil (same dates)": """
            SELECT sp.date, sp.close AS sp500_close, op.price_usd AS oil_price
            FROM stock_prices sp
            JOIN oil_prices op ON sp.date = op.date
            WHERE sp.ticker='^GSPC' ORDER BY sp.date
        """,
        "27. Bitcoin vs crude oil closing price (same date)": """
            SELECT cp.date, cp.price_usd AS btc_price, op.price_usd AS oil_price
            FROM crypto_prices cp
            JOIN oil_prices op ON cp.date = op.date
            WHERE cp.coin_id='bitcoin' ORDER BY cp.date
        """,
        "28. NASDAQ vs Ethereum price trends": """
            SELECT sp.date, sp.close AS nasdaq_close, cp.price_usd AS eth_price
            FROM stock_prices sp
            JOIN crypto_prices cp ON sp.date = cp.date AND cp.coin_id='ethereum'
            WHERE sp.ticker='^IXIC' ORDER BY sp.date
        """,
        "29. Top 3 crypto coins joined with stock indices (2025)": """
            SELECT cp.coin_id, cp.date, cp.price_usd, sp.ticker, sp.close
            FROM crypto_prices cp
            JOIN stock_prices sp ON cp.date = sp.date
            WHERE SUBSTR(cp.date,1,4)='2025'
            ORDER BY cp.coin_id, sp.ticker, cp.date
        """,
        "30. Multi-join: stocks + oil + Bitcoin daily comparison": """
            SELECT sp.date, sp.ticker, sp.close AS stock_close,
                   op.price_usd AS oil_price, cp.price_usd AS btc_price
            FROM stock_prices sp
            LEFT JOIN oil_prices op ON sp.date = op.date
            LEFT JOIN crypto_prices cp ON sp.date = cp.date AND cp.coin_id='bitcoin'
            ORDER BY sp.date, sp.ticker
        """,
    }

    selected_query = st.selectbox("Choose Query", list(query_dict.keys()))
    if st.button("Run Query"):
        result = pd.read_sql(query_dict[selected_query], conn)
        st.dataframe(result, use_container_width=True)

elif page == "Top 3 Crypto Analysis":
    st.header("Top 3 Crypto Analysis")

    top3_df = pd.read_sql("""
        SELECT id, name FROM cryptocurrencies
        ORDER BY market_cap_rank LIMIT 3
    """, conn)

    if not top3_df.empty:
        coin_name = st.selectbox("Select Coin", top3_df["name"].tolist())
        coin_id = top3_df[top3_df["name"] == coin_name]["id"].values[0]

        date_bounds = pd.read_sql(
            "SELECT MIN(date) AS min_d, MAX(date) AS max_d FROM crypto_prices WHERE coin_id=?",
            conn, params=(coin_id,)
        )
        min_d = date_bounds["min_d"].iloc[0]
        max_d = date_bounds["max_d"].iloc[0]

        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date", pd.to_datetime(min_d) if min_d else None)
        end_date = col2.date_input("End Date", pd.to_datetime(max_d) if max_d else None)

        df = pd.read_sql("""
            SELECT date, price_usd
            FROM crypto_prices
            WHERE coin_id=? AND date BETWEEN ? AND ?
            ORDER BY date
        """, conn, params=(coin_id, str(start_date), str(end_date)))

        st.line_chart(df.set_index("date"))
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No crypto data found. Run data scripts first.")

conn.close()
