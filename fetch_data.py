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
