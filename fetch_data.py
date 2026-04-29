import requests
import json
import os
from datetime import datetime

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")

print(f"POLYGON_KEY loaded: {bool(POLYGON_KEY)}")

TICKERS = ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"]

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "stocks": {}
}

for ticker in TICKERS:
    print(f"\nFetching data for {ticker}...")
    stock_data = {}

    # ─────────────────────────────────────────
    # 1. PREVIOUS DAY OHLCV (already working)
    # ─────────────────────────────────────────
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=10)
        result = r.json().get("results", [{}])[0]
        stock_data["ohlcv"] = {
            "open":   result.get("o"),
            "high":   result.get("h"),
            "low":    result.get("l"),
            "close":  result.get("c"),
            "volume": result.get("v"),
        }
        print(f"  OHLCV: OK")
    except Exception as e:
        stock_data["ohlcv"] = {"error": str(e)}
        print(f"  OHLCV: ERROR - {e}")

    # ─────────────────────────────────────────
    # 2. TIME OF SALES (last 25 trades)
    # ─────────────────────────────────────────
    try:
        url = (
            f"https://api.polygon.io/v3/trades/{ticker}"
            f"?limit=25&order=desc&sort=timestamp&apiKey={POLYGON_KEY}"
        )
        r = requests.get(url, timeout=10)
        trades_raw = r.json().get("results", [])
        trades = []
        for t in trades_raw:
            trades.append({
                "timestamp": t.get("sip_timestamp"),
                "price":     t.get("price"),
                "size":      t.get("size"),
                "exchange":  t.get("exchange"),
                "conditions": t.get("conditions", []),
            })
        stock_data["time_of_sales"] = trades
        print(f"  Time of Sales: {len(trades)} trades fetched")
    except Exception as e:
        stock_data["time_of_sales"] = {"error": str(e)}
        print(f"  Time of Sales: ERROR - {e}")

    # ─────────────────────────────────────────
    # 3. NBBO QUOTE SNAPSHOT (best bid & ask)
    # ─────────────────────────────────────────
    try:
        url = (
            f"https://api.polygon.io/v3/quotes/{ticker}"
            f"?limit=1&order=desc&sort=timestamp&apiKey={POLYGON_KEY}"
        )
        r = requests.get(url, timeout=10)
        quotes_raw = r.json().get("results", [{}])
        q = quotes_raw[0] if quotes_raw else {}
        stock_data["nbbo"] = {
            "timestamp":  q.get("sip_timestamp"),
            "bid_price":  q.get("bid_price"),
            "bid_size":   q.get("bid_size"),
            "ask_price":  q.get("ask_price"),
            "ask_size":   q.get("ask_size"),
            "spread":     round(
                (q.get("ask_price") or 0) - (q.get("bid_price") or 0), 4
            ),
        }
        print(f"  NBBO: bid={stock_data['nbbo']['bid_price']} ask={stock_data['nbbo']['ask_price']}")
    except Exception as e:
        stock_data["nbbo"] = {"error": str(e)}
        print(f"  NBBO: ERROR - {e}")

    output["stocks"][ticker] = stock_data

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
os.makedirs("data", exist_ok=True)
with open("data/prices.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n✅ Done - data/prices.json updated")
