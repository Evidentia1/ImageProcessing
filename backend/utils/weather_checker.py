"""
Weather checker for storm / calamity validation
───────────────────────────────────────────────
Requires:  WEATHER_API_KEY in .env  (get one free at https://www.weatherapi.com/)
"""

import os, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
_API_KEY = os.getenv("WEATHER_API_KEY")
_BASE    = "http://api.weatherapi.com/v1/history.json"

KEYWORDS = ("storm", "rain", "flood", "hurricane", "cyclone", "gale", "thunder")

def check_storm(location: str, date_iso: str) -> dict:
    """
    Args
    ----
    location : "London" | "90210" etc.
    date_iso : "YYYY-MM-DD"

    Returns
    -------
    { "storm": bool, "details": str, "raw": dict }
    """
    if not _API_KEY:
        return {"storm": None, "details": "No WEATHER_API_KEY", "raw": {}}

    try:
        resp = requests.get(
            _BASE,
            params={"key": _API_KEY, "q": location, "dt": date_iso},
            timeout=15
        ).json()

        hour_data = resp.get("forecast", {}).get("forecastday", [])[0]["hour"]
        # Look for any hour with severe wind or heavy precipitation:
        severe = False
        reason = []
        for h in hour_data:
            cond = h["condition"]["text"].lower()
            if any(k in cond for k in KEYWORDS):
                severe = True
                reason.append(cond)
                break
            if h["wind_kph"] >= 60 or h["precip_mm"] >= 20:
                severe = True
                reason.append(
                    f"wind {h['wind_kph']} kph / precip {h['precip_mm']} mm"
                )
                break

        return {
            "storm": severe,
            "details": ", ".join(reason) or "No severe weather detected.",
            "raw": resp,
        }
    except Exception as e:
        return {"storm": None, "details": f"weather api error: {e}", "raw": {}}
