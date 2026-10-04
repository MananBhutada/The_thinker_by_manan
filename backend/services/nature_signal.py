"""English text

English text HTML English text NatureSignalEngineEnglish text 3364-3377
English textEnglish text nature English text"English text"English text

English text
  English textEnglish textEnglish textEnglish textEnglish textEnglish textEnglish textEnglish text
  English textEnglish textEnglish textEnglish text
  English textEnglish text
"""

from typing import Any, Dict, List, Optional


def build(weather: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """English text

    English text
      weather: English text dictEnglish text alerts / weatherTrend /
               livingAdvice / airDetail / moonPhase / forecastEnglish text None

    English text{weights: [{name, weight, value}], summary: str}
    """
    w = weather or {}
    weights: List[Dict[str, Any]] = []

    # English text vs English textEnglish text
    if w.get("isReal"):
        weights.append({"name": "English text", "weight": 32, "value": w.get("weather") or "English text"})
    else:
        weights.append({"name": "English text", "weight": 16, "value": w.get("weather") or "English text"})

    alerts = _text_list(w.get("alarms") or w.get("alerts") or w.get("weatherAlerts") or w.get("warnings"))
    if alerts:
        weights.append({"name": "English text", "weight": 28, "value": "".join(alerts[:2])})
    if w.get("wind"):
        weights.append({"name": "English text", "weight": 18, "value": w["wind"]})
    if w.get("temperature") not in (None, ""):
        weights.append({"name": "English text", "weight": 14, "value": f"{w['temperature']}℃"})
    if w.get("humidity"):
        weights.append({"name": "English text", "weight": 10, "value": w["humidity"]})
    air_detail = _air_detail(w)
    if w.get("air") or air_detail:
        weights.append({"name": "English text", "weight": 12, "value": air_detail or str(w.get("air") or "")})
    trend = _trend_text(w)
    if trend:
        weights.append({"name": "English text", "weight": 12, "value": trend})
    living = _text_list(w.get("life_indices") or w.get("livingAdvice") or w.get("lifeAdvice") or w.get("tips"))
    if living:
        weights.append({"name": "English text", "weight": 10, "value": "".join(living[:2])})

    weights.append({"name": "English text", "weight": 8, "value": w.get("time") or "English text"})
    weights.append({"name": "English text", "weight": 8, "value": w.get("season") or "English text"})
    if w.get("moonPhase"):
        weights.append({"name": "English text", "weight": 6, "value": w["moonPhase"]})

    summary = "".join(f"{x['name']}{x['weight']}%:{x['value']}" for x in weights)
    return {"weights": weights, "summary": summary}


def _text_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        fields = ("name", "level", "desc", "title", "text", "description", "value")
        items = [str(value[key]).strip() for key in fields if str(value.get(key) or "").strip()]
        ids = value.get("ids")
        if isinstance(ids, list):
            for item in ids:
                items.extend(_text_list(item))
        return items
    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            items.extend(_text_list(item))
        return items
    return [str(value).strip()] if value is not None and str(value).strip() else []


def _air_detail(weather: Dict[str, Any]) -> str:
    detail = weather.get("airDetail") or weather.get("air_detail") or weather.get("airQuality")
    if isinstance(detail, dict):
        labels = (("aqi", "AQI"), ("pm25", "PM2.5"), ("pm10", "PM10"))
        readings = [f"{label} {detail[key]}" for key, label in labels if detail.get(key) not in (None, "")]
        if readings:
            return " · ".join(readings)
    items = _text_list(detail)
    if items:
        return "".join(items[:2])
    aqi = weather.get("aqi")
    return f"{weather.get('air', '')} · AQI {aqi}".strip(" ·") if aqi not in (None, "") else ""


def _trend_text(weather: Dict[str, Any]) -> str:
    direct = _text_list(weather.get("weatherTrend") or weather.get("trend"))
    if direct:
        return "".join(direct[:2])
    forecast = weather.get("forecast_1h") or weather.get("forecast_24h") or []
    if not isinstance(forecast, list):
        return ""
    texts = []
    for item in forecast[:2]:
        if not isinstance(item, dict):
            continue
        info = item.get("infos") or item.get("info") or {}
        info = info if isinstance(info, dict) else {}
        time = item.get("hour") or item.get("time") or item.get("update_time") or item.get("forecast_time")
        condition = item.get("weather") or info.get("weather") or item.get("text") or info.get("text")
        temperature = item.get("temperature") or info.get("temperature") or item.get("temp") or info.get("temp")
        parts = [time, condition, f"{temperature}℃" if temperature not in (None, "") else ""]
        text = " ".join(str(part).strip() for part in parts if part)
        if text:
            texts.append(text)
    return "".join(texts)


if __name__ == "__main__":
    # English textEnglish text
    w1 = {
        "isReal": True,
        "weather": "English text",
        "wind": "English text 3 English text",
        "temperature": 22,
        "humidity": "65%",
        "air": "English text",
        "time": "English text",
        "season": "English text",
    }
    r1 = build(w1)
    print("case1English text:", r1["summary"])
    assert r1["weights"][0] == {"name": "English text", "weight": 32, "value": "English text"}
    assert len(r1["weights"]) == 7  # English text + English text + English text + English text + English text + English text + English text
    assert "English text32%:English text" in r1["summary"]
    assert "English text14%:22℃" in r1["summary"]

    # English textEnglish textEnglish text
    w2 = {"isReal": False}
    r2 = build(w2)
    print("case2English text:", r2["summary"])
    assert r2["weights"][0] == {"name": "English text", "weight": 16, "value": "English text"}
    assert len(r2["weights"]) == 3  # English text + English text + English text
    assert "English text8%:English text" in r2["summary"]
    assert "English text8%:English text" in r2["summary"]

    # English textNone English text
    r3 = build(None)
    print("case3None:", r3["summary"])
    assert r3["weights"][0]["name"] == "English text"

    print("\nEnglish text")
