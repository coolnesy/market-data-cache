import requests
import json
import os
from datetime import datetime, timedelta, timezone

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")
print(f"POLYGON_KEY loaded: {bool(POLYGON_KEY)}")

TICKER = "AR"

# Date range — last 2 trading days to ensure we capture a full session
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "ticker": TICKER,
    "stocks": {}
}

stock_data = {}

# ─────────────────────────────────────────
# 1. PREVIOUS DAY OHLCV
# ─────────────────────────────────────────
try:
    url = f"https://api.polygon.io/v2/aggs/ticker/{TICKER}/prev?adjusted=true&apiKey={POLYGON_KEY}"
    r = requests.get(url, timeout=10)
    result = r.json().get("results", [{}])[0]
    stock_data["ohlcv"] = {
        "open":   result.get("o"),
        "high":   result.get("h"),
        "low":    result.get("l"),
        "close":  result.get("c"),
        "volume": result.get("v"),
        "vwap":   result.get("vw"),
    }
    print(f"  OHLCV: OK")
except Exception as e:
    stock_data["ohlcv"] = {"error": str(e)}
    print(f"  OHLCV: ERROR - {e}")

# ─────────────────────────────────────────
# 2. 1-MINUTE BARS (last 2 days)
#    ~800 rows — tiny file, full detail
# ─────────────────────────────────────────
try:
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{TICKER}/range/1/minute"
        f"/{yesterday}/{today}"
        f"?adjusted=true&sort=asc&limit=50000&apiKey={POLYGON_KEY}"
    )
    r = requests.get(url, timeout=30)
    data = r.json()
    bars = []
    for b in data.get("results", []):
        bars.append({
            "timestamp": b.get("t"),
            "open":      b.get("o"),
            "high":      b.get("h"),
            "low":       b.get("l"),
            "close":     b.get("c"),
            "volume":    b.get("v"),
            "vwap":      b.get("vw"),
            "trades":    b.get("n"),  # number of trades in this bar
        })
    stock_data["minute_bars"] = {
        "total_bars": len(bars),
        "bars": bars
    }
    print(f"  Minute bars: {len(bars)} bars fetched")
except Exception as e:
    stock_data["minute_bars"] = {"error": str(e)}
    print(f"  Minute bars: ERROR - {e}")

# ─────────────────────────────────────────
# 3. LAST 50 TRADES (ToS sample)
# ─────────────────────────────────────────
try:
    url = (
        f"https://api.polygon.io/v3/trades/{TICKER}"
        f"?limit=50&order=desc&sort=timestamp&apiKey={POLYGON_KEY}"
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
    stock_data["time_of_sales"] = {
        "note": "Last 50 trades (snapshot)",
        "total_trades": len(trades),
        "trades": trades
    }
    print(f"  ToS: {len(trades)} trades fetched")
except Exception as e:
    stock_data["time_of_sales"] = {"error": str(e)}
    print(f"  ToS: ERROR - {e}")

# ─────────────────────────────────────────
# 4. NBBO QUOTE SNAPSHOT
# ─────────────────────────────────────────
try:
    url = (
        f"https://api.polygon.io/v3/quotes/{TICKER}"
        f"?limit=1&order=desc&sort=timestamp&apiKey={POLYGON_KEY}"
    )
    r = requests.get(url, timeout=10)
    quotes_raw = r.json().get("results", [{}])
    q = quotes_raw[0] if quotes_raw else {}
    stock_data["nbbo"] = {
        "timestamp": q.get("sip_timestamp"),
        "bid_price": q.get("bid_price"),
        "bid_size":  q.get("bid_size"),
        "ask_price": q.get("ask_price"),
        "ask_size":  q.get("ask_size"),
        "spread":    round((q.get("ask_price") or 0) - (q.get("bid_price") or 0), 4),
    }
    print(f"  NBBO: bid={stock_data['nbbo']['bid_price']} ask={stock_data['nbbo']['ask_price']}")
except Exception as e:
    stock_data["nbbo"] = {"error": str(e)}
    print(f"  NBBO: ERROR - {e}")

output["stocks"][TICKER] = stock_data

# ─────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────
os.makedirs("data", exist_ok=True)
with open("data/prices.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n✅ Done - data/prices.json updated")
