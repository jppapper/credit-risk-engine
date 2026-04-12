import json
import os
import redis
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from src.database.eod_marks import get_prior_eod_mark

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

app = FastAPI(title="Credit Risk Engine", version="1.0.0")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@app.get("/health")
def health():
    try:
        redis_client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"
    
    return {
        "status": "ok",
        "redis": redis_status,
        "version": "1.0.0"
    }

@app.get("/risk/portfolio")
def get_portfolio_risk():
    keys = redis_client.keys("CDS-*") + redis_client.keys("BOND-*")
    if not keys:
        raise HTTPException(status_code=404, detail="No risk data found in cache")
    
    total_cs01 = 0
    total_dv01 = 0
    position_count = 0

    for key in keys:
        result = redis_client.get(key)
        if result:
            data = json.loads(result)
            total_cs01 += data.get("cs01", 0)
            total_dv01 += data.get("dv01", 0)
            position_count += 1

    return {
        "position_count": position_count,
        "total_cs01": total_cs01,
        "total_dv01": total_dv01
    }

@app.get("/risk/{instrument_id}")
def get_risk(instrument_id: str):
    result = redis_client.get(instrument_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"No risk data found for {instrument_id}")
    return json.loads(result)

@app.get("/pnl/portfolio")
def get_portfolio_pnl():
    keys = redis_client.keys("CDS-*") + redis_client.keys("BOND-*")
    if not keys:
        raise HTTPException(status_code=404, detail="No risk data found in cache")
    
    total_pnl = 0
    position_count = 0
    errors = 0

    for key in keys:
        try:
            result = get_pnl(key)
            total_pnl += result["pnl"]
            position_count += 1
        except HTTPException:
            errors += 1

    return {
        "position_count": position_count,
        "total_pnl": total_pnl,
        "errors": errors
    }

@app.get("/pnl/{instrument_id}")
def get_pnl(instrument_id: str):
    current = redis_client.get(instrument_id)
    if not current:
        raise HTTPException(status_code=404, detail=f"No current risk data found for {instrument_id}")
    
    current_data = json.loads(current)
    prior_mark = get_prior_eod_mark(instrument_id)
    
    if not prior_mark:
        raise HTTPException(status_code=404, detail=f"No prior EOD mark found for {instrument_id}")
    
    if current_data["product"] == "CDS":
        pnl = (current_data["upfront"] - prior_mark.upfront) * prior_mark.notional
    else:
        pnl = (current_data["dirty_price"] - prior_mark.dirty_price) / 100 * prior_mark.notional

    return {
        "instrument_id": instrument_id,
        "product": current_data["product"],
        "pnl": pnl,
        "current_mark": current_data.get("upfront") or current_data.get("dirty_price"),
        "prior_mark": prior_mark.upfront or prior_mark.dirty_price
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)