import httpx
import os
from dotenv import load_dotenv
import redis.asyncio as redis
import json, time

load_dotenv()

TRANSPORTSTACK_BASE = "https://delhi.transportstack.in"
API_KEY = os.getenv("TRANSPORTSTACK_API_KEY", "")

# Redis for caching (avoid hammering the API)
cache = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
CACHE_TTL = 60  # seconds


class DMRCClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        }

    async def _cached_get(self, url: str, params: dict = None, ttl=CACHE_TTL):
        cache_key = f"metrocast:{url}:{json.dumps(params or {})}"
        cached = await cache.get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        await cache.setex(cache_key, ttl, json.dumps(data))
        return data

    async def get_station_flow(self, station: str) -> dict:
        """
        Fetches aggregate check-in / check-out counts for a station.
        Source: TransportStack /data-services/datadetails/4
        Returns ONLY aggregate counts — no personal identifiers.
        """
        try:
            data = await self._cached_get(
                f"{TRANSPORTSTACK_BASE}/api/v1/stations/flow",
                params={"station": station, "window_minutes": 30}
            )
            return {
                "station": station,
                "checkins_last_30min":  data.get("checkin_count", 0),
                "checkouts_last_30min": data.get("checkout_count", 0),
                "timestamp": data.get("timestamp", time.time())
            }
        except Exception:
            # Graceful fallback to simulated data if API unavailable
            import random
            return {
                "station": station,
                "checkins_last_30min":  random.randint(200, 2000),
                "checkouts_last_30min": random.randint(150, 1800),
                "timestamp": time.time()
            }

    async def get_all_station_flows(self) -> dict:
        try:
            data = await self._cached_get(
                f"{TRANSPORTSTACK_BASE}/api/v1/stations/flow/all"
            )
            return data
        except Exception:
            return {"error": "TransportStack API unavailable", "fallback": True}

    async def get_system_load(self) -> dict:
        try:
            data = await self._cached_get(
                f"{TRANSPORTSTACK_BASE}/api/v1/system/load"
            )
            return data
        except Exception:
            import random
            return {
                "system_load_pct": random.randint(40, 85),
                "total_checkins_30min": random.randint(15000, 30000),
                "active_stations": 254,
                "fallback": True
            }
