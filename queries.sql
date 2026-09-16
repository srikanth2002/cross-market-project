-- =========================================================
-- 1) cryptocurrencies
-- =========================================================

-- 1.1 Top 3 cryptocurrencies by market cap
SELECT name, market_cap
FROM cryptocurrencies
ORDER BY market_cap DESC
LIMIT 3;

-- 1.2 Coins where circulating supply exceeds 90% of total supply
SELECT name, circulating_supply, total_supply
FROM cryptocurrencies
WHERE total_supply > 0
  AND circulating_supply >= 0.9 * total_supply;

-- 1.3 Coins within 10% of their all-time-high (ATH)
SELECT name, current_price, ath
FROM cryptocurrencies
WHERE ath > 0
  AND current_price >= 0.9 * ath;

-- 1.4 Average market cap rank of coins with volume above $1B
SELECT ROUND(AVG(market_cap_rank), 2) AS avg_rank
FROM cryptocurrencies
WHERE total_volume > 1000000000;

-- 1.5 Most recently updated coin
SELECT name, date
FROM cryptocurrencies
ORDER BY date DESC
LIMIT 1;


-- =========================================================
-- 2) crypto_prices
-- =========================================================

-- 2.1 Highest daily price of Bitcoin in the last 365 days
SELECT MAX(price_usd) AS highest_bitcoin_price
FROM crypto_prices
WHERE coin_id = 'bitcoin';

-- 2.2 Average daily price of Ethereum in the past 1 year
SELECT ROUND(AVG(price_usd), 2) AS avg_ethereum_price
FROM crypto_prices
WHERE coin_id = 'ethereum';

-- 2.3 Daily price trend of Bitcoin in a given month/year
SELECT date, price_usd
FROM crypto_prices
WHERE coin_id = 'bitcoin'
  AND date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY date;

-- 2.4 Coin with the highest average price over 1 year
SELECT coin_id, ROUND(AVG(price_usd), 2) AS avg_price
FROM crypto_prices
GROUP BY coin_id
ORDER BY avg_price DESC
LIMIT 1;

-- 2.5 % change in Bitcoin's price between two dates
SELECT
    (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2025-09-16') AS end_price,
    (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16') AS start_price,
    ROUND(
        (
            (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2025-09-16') -
            (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16')
        ) * 100.0 /
        (SELECT price_usd FROM crypto_prices WHERE coin_id='bitcoin' AND date='2024-09-16')
    , 2) AS pct_change;


-- =========================================================
-- 3) oil_prices
-- =========================================================

-- 3.1 Highest oil price in the last 5 years
SELECT MAX(price_usd) AS highest_oil_price
FROM oil_prices
WHERE date >= '2021-01-01';

-- 3.2 Average oil price per year
SELECT SUBSTR(date, 1, 4) AS year, ROUND(AVG(price_usd), 2) AS avg_oil_price
FROM oil_prices
GROUP BY SUBSTR(date, 1, 4)
ORDER BY year;

-- 3.3 Oil prices during COVID crash (March-April 2020)
SELECT date, price_usd
FROM oil_prices
WHERE date BETWEEN '2020-03-01' AND '2020-04-30'
ORDER BY date;

-- 3.4 Lowest price of oil in the last 10 years
SELECT MIN(price_usd) AS lowest_oil_price
FROM oil_prices
WHERE date >= '2016-01-01';

-- 3.5 Volatility of oil prices (max-min difference per year)
SELECT SUBSTR(date, 1, 4) AS year,
       ROUND(MAX(price_usd) - MIN(price_usd), 2) AS volatility
FROM oil_prices
GROUP BY SUBSTR(date, 1, 4)
ORDER BY year;


-- =========================================================
-- 4) stock_prices
-- =========================================================

-- 4.1 All stock prices for a given ticker
SELECT *
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY date;

-- 4.2 Highest closing price for NASDAQ (^IXIC)
SELECT MAX(close) AS highest_nasdaq_close
FROM stock_prices
WHERE ticker = '^IXIC';

-- 4.3 Top 5 days with highest price difference (high - low) for S&P 500
SELECT date, ROUND(high - low, 2) AS diff
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY diff DESC
LIMIT 5;

-- 4.4 Monthly average closing price for each ticker
SELECT ticker, SUBSTR(date, 1, 7) AS month, ROUND(AVG(close), 2) AS avg_close
FROM stock_prices
GROUP BY ticker, SUBSTR(date, 1, 7)
ORDER BY ticker, month;

-- 4.5 Average trading volume of NIFTY (^NSEI) in 2024
SELECT ROUND(AVG(volume), 2) AS avg_volume
FROM stock_prices
WHERE ticker = '^NSEI'
  AND SUBSTR(date, 1, 4) = '2024';


-- =========================================================
-- 5) Join queries (Cross-Market Analysis)
-- =========================================================

-- 5.1 Compare Bitcoin vs Oil average price in 2025
SELECT
    (SELECT ROUND(AVG(price_usd), 2) FROM crypto_prices
     WHERE coin_id='bitcoin' AND SUBSTR(date,1,4)='2025') AS btc_avg_2025,
    (SELECT ROUND(AVG(price_usd), 2) FROM oil_prices
     WHERE SUBSTR(date,1,4)='2025') AS oil_avg_2025;

-- 5.2 Bitcoin vs S&P 500 on the same dates (for correlation analysis)
SELECT cp.date, cp.price_usd AS btc_price, sp.close AS sp500_close
FROM crypto_prices cp
JOIN stock_prices sp
  ON cp.date = sp.date AND sp.ticker = '^GSPC'
WHERE cp.coin_id = 'bitcoin'
ORDER BY cp.date;

-- 5.3 Ethereum and NASDAQ daily prices for 2025
SELECT cp.date, cp.price_usd AS eth_price, sp.close AS nasdaq_close
FROM crypto_prices cp
JOIN stock_prices sp
  ON cp.date = sp.date AND sp.ticker = '^IXIC'
WHERE cp.coin_id = 'ethereum'
  AND SUBSTR(cp.date,1,4) = '2025'
ORDER BY cp.date;

-- 5.4 Days when oil price spiked (>5% day-over-day) vs Bitcoin price change
WITH oil_change AS (
    SELECT date, price_usd,
           ROUND((price_usd - LAG(price_usd) OVER (ORDER BY date)) * 100.0
                 / LAG(price_usd) OVER (ORDER BY date), 2) AS oil_pct_change
    FROM oil_prices
)
SELECT oc.date, oc.oil_pct_change, cp.price_usd AS btc_price
FROM oil_change oc
JOIN crypto_prices cp
  ON oc.date = cp.date AND cp.coin_id = 'bitcoin'
WHERE oc.oil_pct_change > 5
ORDER BY oc.date;

-- 5.5 Top 3 coins daily price trend vs Nifty (^NSEI)
SELECT cp.coin_id, cp.date, cp.price_usd, sp.close AS nifty_close
FROM crypto_prices cp
JOIN stock_prices sp
  ON cp.date = sp.date AND sp.ticker = '^NSEI'
ORDER BY cp.coin_id, cp.date;

-- 5.6 Stock prices (^GSPC) with crude oil prices on the same dates
SELECT sp.date, sp.close AS sp500_close, op.price_usd AS oil_price
FROM stock_prices sp
JOIN oil_prices op ON sp.date = op.date
WHERE sp.ticker = '^GSPC'
ORDER BY sp.date;

-- 5.7 Correlate Bitcoin closing price with crude oil closing price (same date)
SELECT cp.date, cp.price_usd AS btc_price, op.price_usd AS oil_price
FROM crypto_prices cp
JOIN oil_prices op ON cp.date = op.date
WHERE cp.coin_id = 'bitcoin'
ORDER BY cp.date;

-- 5.8 Compare NASDAQ (^IXIC) with Ethereum price trends
SELECT sp.date, sp.close AS nasdaq_close, cp.price_usd AS eth_price
FROM stock_prices sp
JOIN crypto_prices cp
  ON sp.date = cp.date AND cp.coin_id = 'ethereum'
WHERE sp.ticker = '^IXIC'
ORDER BY sp.date;

-- 5.9 Join top 3 crypto coins with stock indices for 2025
SELECT cp.coin_id, cp.date, cp.price_usd, sp.ticker, sp.close
FROM crypto_prices cp
JOIN stock_prices sp ON cp.date = sp.date
WHERE SUBSTR(cp.date,1,4) = '2025'
ORDER BY cp.coin_id, sp.ticker, cp.date;

-- 5.10 Multi-join: stock prices, oil prices, and Bitcoin prices for daily comparison
SELECT sp.date,
       sp.ticker,
       sp.close AS stock_close,
       op.price_usd AS oil_price,
       cp.price_usd AS btc_price
FROM stock_prices sp
LEFT JOIN oil_prices op ON sp.date = op.date
LEFT JOIN crypto_prices cp ON sp.date = cp.date AND cp.coin_id = 'bitcoin'
ORDER BY sp.date, sp.ticker;
