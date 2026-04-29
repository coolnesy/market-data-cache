import requests
import json
import os
from datetime import datetime, timedelta, timezone

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")

print(f"POLYGON_KEY loaded: {bool(POLYGON_KEY)}")

TICKERS = ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"]

# 24 hours ago in nanoseconds (Polygon uses nanosecond timestamps)
since_ns = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp() * 1_000_000_000)

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "since": datetime.now(timezone.utc) - timedelta(hours=24),
    "stocks": {}
}
output["since"] = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

for ticker in TICKERS:
    print(f"\nFetching data for {ticker}...")
    stock_data = {}

    # ─────────────────────────────────────────
    # 1. PREVIOUS DAY OHLCV
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
    # 2. TIME OF SALES — ALL TRADES (last 24h)
    #    Paginated — fetches every page until done
    # ─────────────────────────────────────────
    try:
        trades = []
        url = (
            f"https://api.polygon.io/v3/trades/{ticker}"
            f"?timestamp.gte={since_ns}"
            f"&limit=50000"
            f"&order=desc"
            f"&sort=timestamp"
            f"&apiKey={POLYGON_KEY}"
        )

        page = 0
        while url:
            page += 1
            print(f"  Trades page {page}...")
            r = requests.get(url, timeout=30)
            data = r.json()

            for t in data.get("results", []):
                trades.append({
                    "timestamp": t.get("sip_timestamp"),
                    "price":     t.get("price"),
                    "size":      t.get("size"),
                    "exchange":  t.get("exchange"),
                    "conditions": t.get("conditions", []),
                })

            # Polygon returns a next_url if there are more pages
            url = data.get("next_url")
            if url:
                url = f"{url}&apiKey={POLYGON_KEY}"

        stock_data["time_of_sales"] = {
            "total_trades": len(trades),
            "trades": trades
        }
        print(f"  Time of Sales: {len(trades):,} total trades fetched")

    except Exception as e:
        stock_data["time_of_sales"] = {"error": str(e)}
        print(f"  Time of Sales: ERROR - {e}")

    # ─────────────────────────────────────────
    # 3. NBBO QUOTE SNAPSHOT
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
