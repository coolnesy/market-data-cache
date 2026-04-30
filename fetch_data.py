import requests
import json
import os
from datetime import datetime, timedelta, timezone

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY")

print(f"POLYGON_KEY loaded: {bool(POLYGON_KEY)}")
print(f"FINNHUB_KEY loaded: {bool(FINNHUB_KEY)}")

TICKER = "AR"
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "ticker": TICKER,
    "stocks": {}
}

stock_data = {}

# 1. OHLCV (Polygon)
try:
    url = f"https://api.polygon.io/v2/aggs/ticker/{TICKER}/prev?adjusted=true&apiKey={POLYGON_KEY}"
    r = requests.get(url, timeout=10)
    result = r.json().get("results", [{}])[0]
    stock_data["ohlcv"] = {
        "open": result.get("o"), "high": result.get("h"),
        "low": result.get("l"), "close": result.get("c"),
        "volume": result.get("v"), "vwap": result.get("vw"),
    }
    print("  OHLCV: OK")
except Exception as e:
    stock_data["ohlcv"] = {"error": str(e)}
    print(f"  OHLCV: ERROR - {e}")

# 2. MINUTE BARS (Polygon)
try:
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{TICKER}/range/1/minute"
        f"/{yesterday}/{today}?adjusted=true&sort=asc&limit=50000&apiKey={POLYGON_KEY}"
    )
    r = requests.get(url, timeout=30)
    bars = [{"timestamp": b.get("t"), "open": b.get("o"), "high": b.get("h"),
              "low": b.get("l"), "close": b.get("c"), "volume": b.get("v"),
              "vwap": b.get("vw"), "trades": b.get("n")}
             for b in r.json().get("results", [])]
    stock_data["minute_bars"] = {"total_bars": len(bars), "bars": bars}
    print(f"  Minute bars: {len(bars)} bars fetched")
except Exception as e:
    stock_data["minute_bars"] = {"error": str(e)}
    print(f"  Minute bars: ERROR - {e}")

# 3. TIME OF SALES (Finnhub tick)
try:
    url = (
        f"https://finnhub.io/api/v1/stock/tick"
        f"?symbol={TICKER}&date={today}&limit=50&skip=0&token={FINNHUB_KEY}"
    )
    r = requests.get(url, timeout=15)
    data = r.json()
    print(f"  Finnhub ToS raw: {data}")
    trades = []
    timestamps = data.get("t", [])
    prices = data.get("p", [])
    volumes = data.get("v", [])
    conditions = data.get("c", [])
    for i in range(len(timestamps)):
        trades.append({
            "timestamp": timestamps[i],
            "price": prices[i] if i < len(prices) else None,
            "size": volumes[i] if i < len(volumes) else None,
            "conditions": conditions[i] if i < len(conditions) else [],
        })
    stock_data["time_of_sales"] = {
        "note": "Last 50 trades via Finnhub",
        "total_trades": len(trades),
        "trades": trades
    }
    print(f"  ToS: {len(trades)} trades fetched")
except Exception as e:
    stock_data["time_of_sales"] = {"error": str(e)}
    print(f"  ToS: ERROR - {e}")

# 4. QUOTE/NBBO (Finnhub)
try:
    url = f"https://finnhub.io/api/v1/quote?symbol={TICKER}&token={FINNHUB_KEY}"
    r = requests.get(url, timeout=10)
    q = r.json()
    stock_data["nbbo"] = {
        "timestamp": q.get("t"),
        "current": q.get("c"),
        "open": q.get("o"),
        "high": q.get("h"),
        "low": q.get("l"),
        "prev_close": q.get("pc"),
        "change": round((q.get("c") or 0) - (q.get("pc") or 0), 4),
        "change_pct": round(((q.get("c") or 0) - (q.get("pc") or 0)) / (q.get("pc") or 1) * 100, 4),
    }
    print(f"  Quote: current={stock_data['nbbo']['current']}")
except Exception as e:
    stock_data["nbbo"] = {"error": str(e)}
    print(f"  Quote: ERROR - {e}")

output["stocks"][TICKER] = stock_data

os.makedirs("data", exist_ok=True)
with open("data/prices.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n✅ Done - data/prices.json updated")
