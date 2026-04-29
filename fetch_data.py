import requests
import json
import os
from datetime import datetime

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY")

# Debug: confirm keys are loaded (won't print actual values)
print(f"POLYGON_KEY loaded: {bool(POLYGON_KEY)}")
print(f"FINNHUB_KEY loaded: {bool(FINNHUB_KEY)}")

TICKERS = ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"]

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "stocks": {}
}

for ticker in TICKERS:
    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=10)
        print(f"{ticker} status: {r.status_code}")
        data = r.json()
        result = data.get("results", [{}])[0]

        output["stocks"][ticker] = {
            "open":   result.get("o"),
            "high":   result.get("h"),
            "low":    result.get("l"),
            "close":  result.get("c"),
            "volume": result.get("v"),
        }
    except Exception as e:
        print(f"ERROR on {ticker}: {e}")
        output["stocks"][ticker] = {"error": str(e)}

os.makedirs("data", exist_ok=True)
with open("data/prices.json", "w") as f:
    json.dump(output, f, indent=2)

print("Done:", json.dumps(output, indent=2))
