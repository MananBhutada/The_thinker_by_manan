"""English textEnglish text

English text API
  - English textEnglish text weather_base_url
  - English texthttps://lbs.amap.com/api/webservice/guide/api/weatherinfo
  - English textEnglish text 10 English text
  - English textEnglish text Keyweather_key

English text weather_key English text mock English textEnglish text
English textEnglish text
  { isReal, source, city, weather, temperature, humidity, wind,
    air, time, season, sun, moonPhase, updateTime, forecast_24h }
"""

import random
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from backend.config import get_effective_config, has_weather_config

_TIMEOUT = 8.0


def _get_period(now: datetime) -> str:
    h = now.hour
    if h < 6:
        return "English text"
    if h < 11:
        return "English text"
    if h < 13:
        return "English text"
    if h < 17:
        return "English text"
    if h < 19:
        return "English text"
    return "English text"


def _get_season(now: datetime) -> str:
    m = now.month
    if m < 3 or m == 12:
        return "English text"
    if m < 6:
        return "English text"
    if m < 9:
        return "English text"
    return "English text"


def _get_sun(now: datetime, weather: str) -> str:
    h = now.hour
    if "English text" in weather:
        return "English text"
    if "English text" in weather:
        return "English text"
    if "English text" in weather:
        return "English text" if 6 <= h < 18 else "English text"
    if 6 <= h < 18:
        if h < 12:
            return "English text"
        if h < 15:
            return "English text"
        return "English text"
    return "English text"


def _get_moon_phase(now: datetime) -> str:
    """English text"""
    reference = datetime(2000, 1, 6, 18, 14)
    day_in_cycle = ((now - reference).total_seconds() / 86400) % 29.53058867
    if day_in_cycle < 1:
        return "English text"
    if day_in_cycle < 7:
        return "English text"
    if day_in_cycle < 10:
        return "English text"
    if day_in_cycle < 14:
        return "English text"
    if day_in_cycle < 17:
        return "English text"
    if day_in_cycle < 21:
        return "English text"
    if day_in_cycle < 24:
        return "English text"
    return "English text"


def _base_context(now: datetime) -> Dict[str, Any]:
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": _get_period(now),
        "season": _get_season(now),
        "moonPhase": _get_moon_phase(now),
    }


def _coalesce(*vals):
    for v in vals:
        if v not in (None, "", []):
            return v
    return ""


def _parse_amap_response(data: Any) -> Optional[Dict[str, Any]]:
    """English text

    English text
      {
        "status": "1",
        "count": "1",
        "lives": [{
          "province": "English text", "city": "English text",
          "weather": "English text", "temperature": "23",
          "winddirection": "English text", "windpower": "3",
          "humidity": "45", "reporttime": "2026-06-29 14:32:18",
          "temperature_float": "23.0", "humidity_float": "45.0"
        }]
      }
    """
    if not isinstance(data, dict):
        return None
    # status=0 English text
    if str(data.get("status", "0")) != "1":
        return None
    lives = data.get("lives") or []
    if not lives or not isinstance(lives, list):
        return None
    live = lives[0]
    if not isinstance(live, dict):
        return None
    city = _coalesce(live.get("city"), live.get("province"))
    weather = _coalesce(live.get("weather"))
    temperature = _coalesce(live.get("temperature"), live.get("temperature_float"))
    humidity = _coalesce(live.get("humidity"), live.get("humidity_float"))
    wind_dir = _coalesce(live.get("winddirection"))
    wind_power = _coalesce(live.get("windpower"))
    # English text
    wind = f"{wind_dir}English text {wind_power}English text" if (wind_dir or wind_power) else "English text"
    update_time = _coalesce(live.get("reporttime"), live.get("updatetime"))
    return {
        "city": city or "English text",
        "weather": weather or "English text",
        "temperature": str(temperature) if temperature != "" else "",
        "humidity": str(humidity) if humidity != "" else "",
        "air": "",  # English text AQI
        "wind": wind,
        "updateTime": str(update_time) if update_time != "" else "",
    }


def _parse_amap_forecast(data: Any) -> list[Dict[str, str]]:
    """English text"""
    if not isinstance(data, dict) or str(data.get("status", "0")) != "1":
        return []
    forecasts = data.get("forecasts") or []
    if not forecasts or not isinstance(forecasts, list):
        return []
    casts = forecasts[0].get("casts") or [] if isinstance(forecasts[0], dict) else []
    items = []
    for cast in casts[:3]:
        if not isinstance(cast, dict):
            continue
        day_weather = str(cast.get("dayweather") or "")
        night_weather = str(cast.get("nightweather") or "")
        weather = day_weather if not night_weather or day_weather == night_weather else f"{day_weather}English text{night_weather}"
        items.append({
            "time": str(cast.get("date") or ""),
            "weather": weather,
            "temperature": str(cast.get("daytemp") or cast.get("nighttemp") or ""),
        })
    return items


def _weather_trend(forecast: list[Dict[str, str]]) -> str:
    return "".join(
        " · ".join(part for part in (item.get("time", ""), item.get("weather", ""),
                                      f"{item.get('temperature')}℃" if item.get("temperature") else "") if part)
        for item in forecast[:2]
    )


def _mock_weather(now: datetime, language: str = "zh-CN") -> Dict[str, Any]:
    """English text"""
    if language == "en":
        conditions = [
            {"weather": "Sunny", "wind": random.choice(["light southeast breeze", "gentle south wind", "cool west wind", "fresh north wind"])},
            {"weather": "Cloudy", "wind": random.choice(["light east wind", "soft south wind", "mild west wind", "thin north wind"])},
            {"weather": "Overcast", "wind": random.choice(["still", "cool east wind", "soft south wind", "chilly west wind"])},
            {"weather": "Drizzle", "wind": random.choice(["damp east wind", "cool south wind", "cold west wind", "wintry north wind"])},
        ]
        source, city = "Simulated nature data", "City not set"
    else:
        conditions = [
            {"weather": "English text", "wind": random.choice(["English text", "English text", "English text", "English text"])},
            {"weather": "English text", "wind": random.choice(["English text", "English text", "English text", "English text"])},
            {"weather": "English text", "wind": random.choice(["English text", "English text", "English text", "English text"])},
            {"weather": "English text", "wind": random.choice(["English text", "English text", "English text", "English text"])},
        ]
        source, city = "English text", "English text"
    c = random.choice(conditions)
    return {
        "isReal": False,
        "source": source,
        "city": city,
        "weather": c["weather"],
        "temperature": "",
        "humidity": "",
        "wind": c["wind"],
        "air": "",
        "time": _get_period(now),
        "season": _get_season(now),
        "sun": _get_sun(now, c["weather"]),
        "moonPhase": _get_moon_phase(now),
        "updateTime": "",
        "weatherStatus": "not_configured",
        "weatherStatusText": "English text Key" if language != "en" else "Weather key not configured",
        "alarms": [],
        "forecast_1h": [],
        "forecast_24h": [],
        "weatherTrend": "",
        "life_indices": {},
    }


def get_current_weather(config: Optional[Dict[str, Any]] = None,
                        language: str = "zh-CN") -> Dict[str, Any]:
    """English textEnglish textEnglish text mock

    config English text None English text get_effective_config() English text
    """
    if config is None:
        config = get_effective_config()
    now = datetime.now()
    base = _base_context(now)

    if has_weather_config(config):
        # English text Key
        key = config.get("weather_key") or config.get("weather_appsecret")
        endpoint = config.get("weather_base_url")
        city = config.get("weather_city") or "English text"
        params = {
            "key": key,
            "city": city,
            "extensions": "base",  # base=English text, all=English text
        }
        try:
            forecast = []
            with httpx.Client(timeout=_TIMEOUT) as client:
                resp = client.get(endpoint, params=params)
                resp.raise_for_status()
                parsed = _parse_amap_response(resp.json())
                if parsed:
                    try:
                        forecast_resp = client.get(endpoint, params={**params, "extensions": "all"})
                        forecast_resp.raise_for_status()
                        forecast = _parse_amap_forecast(forecast_resp.json())
                    except Exception as forecast_error:
                        print(f"[weather] English text: {type(forecast_error).__name__}")
            if parsed:
                weather_str = parsed["weather"]
                return {
                    "isReal": True,
                    "source": "amap",
                    "city": parsed["city"],
                    "weather": weather_str,
                    "temperature": parsed["temperature"],
                    "humidity": parsed["humidity"],
                    "wind": parsed["wind"],
                    "air": parsed["air"],
                    "time": base["time"],
                    "season": base["season"],
                    "date": base["date"],
                    "sun": _get_sun(now, weather_str),
                    "moonPhase": base["moonPhase"],
                    "updateTime": parsed["updateTime"],
                    "weatherStatus": "ok",
                    "weatherStatusText": "English text",
                    "alarms": [],
                    "forecast_1h": [],
                    "forecast_24h": forecast,
                    "weatherTrend": _weather_trend(forecast),
                    "life_indices": {},
                }
        except Exception as e:
            # English text KeyEnglish text
            print(f"[weather] English textEnglish text mock: {type(e).__name__}")

    return {**_mock_weather(now, language=language), "date": base["date"]}
