import requests
import json
import os
from datetime import datetime

POLYGON_KEY = os.environ.get("POLYGON_API_KEY")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY")

TICKERS = ["AAPL", "MSFT", "TSLA", "SPY", "QQQ"]  # customize this list

output = {
    "last_updated": datetime.utcnow().isoformat() + "Z",
    "stocks": {}
}

for ticker in TICKERS:
    try:
        # Polygon - previous day close
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={POLYGON_KEY}"
        r = requests.get(url)
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
        output["stocks"][ticker] = {"error": str(e)}

# Save to file
with open("data/prices.json", "w") as f:
    json.dump(output, f, indent=2)

print("Done:", json.dumps(output, indent=2))
