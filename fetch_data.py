# ─────────────────────────────────────────
# 3. TIME OF SALES (Finnhub)
# ─────────────────────────────────────────
try:
    url = (
        f"https://finnhub.io/api/v1/stock/tick"
        f"?symbol={TICKER}"
        f"&date={today}"
        f"&limit=50"
        f"&skip=0"
        f"&token={FINNHUB_KEY}"
    )
    r = requests.get(url, timeout=15)
    data = r.json()
    print(f"  Finnhub ToS raw: {data}")  # ← add this to see what's returned

    trades = []
    for i in range(len(data.get("t", []))):
        trades.append({
            "timestamp": data["t"][i],
            "price":     data["p"][i],
            "size":      data["v"][i],
            "conditions": data.get("c", [[]])[i] if data.get("c") else [],
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
