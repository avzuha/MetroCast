from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from routes import get_route, get_fare
from crowd_predictor import CrowdPredictor
from dmrc_api import DMRCClient
from routes import list_all_stations
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env", encoding="utf-8")
TRANSPORTSTACK_API_KEY = os.getenv("TRANSPORTSTACK_API_KEY")



app = FastAPI(
    title="MetroCast API",
    description="Open-source Delhi Metro crowd intelligence. No personal data.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

predictor = CrowdPredictor()
dmrc = DMRCClient()


class RouteRequest(BaseModel):
    from_station: str
    to_station: str


# ---- ROUTES ----
@app.get("/api/route")
async def plan_route(from_station: str, to_station: str):
    """Returns route path, fare, stops, estimated time."""
    try:
        route = get_route(from_station, to_station)
        fare  = get_fare(route["distance_km"])
        return {
            "from": from_station,
            "to": to_station,
            "path": route["path"],
            "stops": route["stops"],
            "interchanges": route["interchanges"],
            "distance_km": route["distance_km"],
            "duration_min": route["duration_min"],
            "fare_inr": fare,
            "lines": route["lines"],
            "fromLine": route["lines"][0]["name"] if route["lines"] else "",
            "fromColor": route["lines"][0]["color"] if route["lines"] else "#0057A8"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stations")
def get_stations():
    """Returns all stations A-Z for the frontend dropdowns."""
    return list_all_stations()

# ---- CROWD PREDICTION ----
@app.get("/api/crowd/predict")
async def predict_crowd(
    station: str,
    line: str,
    horizon_minutes: int = 15
):
    """
    Returns crowd % prediction for next N minutes.
    Combines DMRC check-in data + ticket data + ARIMA/LSTM model.
    No personal data involved — aggregate only.
    """
    # 1. Fetch live check-in/out data from TransportStack
    live_data = await dmrc.get_station_flow(station)

    # 2. Run ML prediction
    prediction = predictor.predict(
        station=station,
        line=line,
        live_checkins=live_data["checkins_last_30min"],
        live_checkouts=live_data["checkouts_last_30min"],
        horizon_minutes=horizon_minutes
    )

    return {
        "station": station,
        "line": line,
        "current_crowd_pct": prediction["current"],
        "predicted_crowd_pct": prediction["forecast"],
        "confidence": prediction["confidence"],
        "model_used": prediction["model"],
        "data_sources": ["ticket_purchases", "checkin_taps"],
        "personal_data_collected": False,
        "forecast_horizon_min": horizon_minutes
    }


# ---- LIVE STATION FLOW ----
@app.get("/api/stations/flow")
async def stations_flow():
    """Aggregate check-in/out rates across all stations. No personal data."""
    return await dmrc.get_all_station_flows()


# ---- SYSTEM STATS ----
@app.get("/api/system/load")
async def system_load():
    return await dmrc.get_system_load()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
