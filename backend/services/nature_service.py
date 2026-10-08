"""nature English text LLM English text

English text HTML English text Prompts.natureEnglish textEnglish text prompt
English text LLM English textEnglish text LLM English text mock English text

English text
  { type, time, season, weather, sun, wind, source, isReal, signal, poem, suggestion }
"""

from typing import Any, Dict, List, Optional

from backend.config import get_effective_config, has_llm_config
from backend.services.llm_service import NoApiKeyError, call_openai_llm
from backend.services.weather_service import get_current_weather

# ponytail: nature_signal English textImportError English text None
# English textEnglish text services/nature_signal.py English text build_signals
try:
    from backend.services.nature_signal import build as build_signals
except ImportError:
    build_signals = None

_HUMANIZE = (
    "English textEnglish textEnglish textAIEnglish text"
    "English text\"English text/English text/English text/English text\"English textEnglish text"
    "English textEnglish textEnglish text"
)


def _build_nature_prompt(question: str, w: Dict[str, Any]) -> str:
    source = str(w.get("source") or "English text")
    city = str(w.get("city") or "English text")
    source_note = (
        f"English text{source}English text{city}English text{w.get('updateTime') or 'English text'}"
        if w.get("isReal")
        else f"English text{source}English text"
    )
    alerts = _as_text_list(w.get("alarms") or w.get("alerts") or w.get("warnings"))
    trend = _weather_trend_text(w)
    living = _as_text_list(w.get("life_indices") or w.get("livingAdvice") or w.get("tips"))
    lines = [
        f"English text{w.get('date','')} {w.get('time', '')}".strip(),
        f"English text{w.get('season', '')}",
        f"English text{w.get('weather', '')}",
        f"English text{w['temperature']}℃" if w.get("temperature") else "",
        f"English text{w.get('wind', '')}",
        f"English text{w['humidity']}" if w.get("humidity") else "",
        f"English text{w['air']}" if w.get("air") else "",
        f"English text{''.join(alerts)}" if alerts else "",
        f"English text{trend}" if trend else "",
        f"English text{''.join(living)}" if living else "",
        f"English text{w.get('sun', '')}",
        f"English text{w.get('moonPhase', '')}" if w.get("moonPhase") else "",
        source_note,
    ]
    weather_line = "".join(x for x in lines if x)
    time = str(w.get("time") or "English text")
    season = str(w.get("season") or "English text")
    weather_name = str(w.get("weather") or "English text")
    wind = str(w.get("wind") or "English text")
    return (
        f"{_HUMANIZE}\n\n"
        f"English textEnglish text{weather_line}"
        f"English text\"{question}\"English textEnglish text\n"
        "English textEnglish textEnglish text\n"
        "English text JSON\n"
        '{"type":"nature","time":"' + time + '","season":"' + season + '",'
        '"weather":"' + weather_name + '","sun":"' + str(w.get('sun', '')) + '",'
        '"wind":"' + wind + '","source":"' + source + '",'
        '"isReal":' + ("true" if w.get("isReal") else "false") + ","
        '"signal":"English text","poem":"English text2-3English textEnglish text",'
        '"suggestion":"English textEnglish text"}'
    )


def _as_text_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        fields = ("name", "level", "desc", "title", "text", "description", "value")
        items = [str(value[key]).strip() for key in fields if str(value.get(key) or "").strip()]
        ids = value.get("ids")
        if isinstance(ids, list):
            for item in ids:
                items.extend(_as_text_list(item))
        return items
    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            items.extend(_as_text_list(item))
        return items
    return [str(value).strip()] if value is not None and str(value).strip() else []


def _weather_trend_text(weather: Dict[str, Any]) -> str:
    direct = _as_text_list(weather.get("weatherTrend") or weather.get("trend"))
    if direct:
        return "".join(direct[:2])
    forecast = weather.get("forecast_1h") or weather.get("forecast_24h") or []
    if not isinstance(forecast, list):
        return ""
    items = []
    for item in forecast[:3]:
        if not isinstance(item, dict):
            continue
        info = item.get("infos") or item.get("info") or {}
        info = info if isinstance(info, dict) else {}
        time = item.get("hour") or item.get("time") or item.get("forecast_time")
        condition = item.get("weather") or info.get("weather") or item.get("text") or info.get("text")
        temperature = item.get("temperature") or info.get("temperature") or item.get("temp") or info.get("temp")
        parts = [time, condition, f"{temperature}℃" if temperature not in (None, "") else ""]
        text = " ".join(str(part).strip() for part in parts if part)
        if text:
            items.append(text)
    return "".join(items)


def _with_weather_evidence(result: Dict[str, Any], weather: Dict[str, Any]) -> Dict[str, Any]:
    """English textLLM English textEnglish text"""
    signals = build_signals(weather) if build_signals else None
    for key in (
        "source", "isReal", "city", "weather", "temperature", "humidity", "wind", "air",
        "time", "season", "sun", "moonPhase", "updateTime", "weatherStatus", "weatherStatusText",
        "alarms", "forecast_1h", "forecast_24h", "weatherTrend", "life_indices",
    ):
        default = [] if key in {"alarms", "forecast_1h", "forecast_24h"} else ({} if key == "life_indices" else "")
        result[key] = weather.get(key, default)
    result["signals"] = weather.get("signals") or signals
    result["type"] = "nature"
    return result


def _mock_nature_brief(question: str, w: Dict[str, Any], language: str = "zh-CN") -> Dict[str, Any]:
    """English text mock English textEnglish text HTML English text"""
    q = question
    is_en = language == "en"
    time, season, weather, sun, wind = w["time"], w["season"], w["weather"], w.get("sun", "English text"), w["wind"]
    if is_en:
        nature_map = [
            (["eat", "food", "lunch", "dinner", "restaurant"], "Ripe fruit",
             f"In the {season} {weather}, fruit falls when it is ready. Under {sun}, everything has its rhythm.",
             f"Pick the one that moves you right now, as the {wind} points."),
            (["quit", "job", "work", "career", "startup"], "Migrating birds",
             f"{season} days with {wind}, migrating birds set off. Not to betray the old forest, but to follow the season. {sun} shows the way.",
             f"If staying is only out of fear, the {wind} is already urging you to go."),
            (["break", "love", "relationship", "marry", "divorce"], "Two converging streams",
             f"Under the {weather}, streams meet and part. {sun} on the water shows that coming together and apart are both natural.",
             "Ask yourself: with them, do you feel more like yourself or less?"),
            (["buy", "sell", "house", "car", "rent", "money", "invest"], "Deep-rooted and shallow-rooted trees",
             f"In the {wind}, deep-rooted trees stand still while shallow-rooted ones sway. The soil of {season} decides where roots go.",
             f"Count the cost, then listen to the {wind}."),
            (["study", "exam", "read", "book", "major", "graduate"], "Sun-seeking vines",
             f"{sun}, vines climb toward the light without asking how far. {season} is a season of growth.",
             "Choose the path that makes your eyes light up."),
            (["move", "city", "stay", "leave"], "Drifting dandelion seeds",
             f"The {wind} rises and dandelion seeds drift. Under the {weather} sky, wherever they land is home.",
             "Imagine where future-you would regret being."),
            (["should", "whether", "can", "could"], "Ebb and flow of the tide",
             f"At {time}, {weather}, the sea does not rush the tide. Under {sun}, advance and retreat have their own rhythm.",
             "Wait three days; if the answer is still the same, do it."),
            (["choose", "pick", "which", "or"], "Forked river",
             f"In the {season} {weather}, the river reaches a fork. The {wind} pushes the current; every branch has its view.",
             "The moment the coin is in the air, you will know."),
        ]
        default_signal, default_poem, default_suggestion = (
            "Go with the flow",
            f"{weather} at {time}, {wind} brushes everything. If you cling to the answer, you cannot hear nature's whisper.",
            "Let go of the fixation and go with the flow."
        )
    else:
        nature_map = [
            (["English text", "English text", "English text", "English text"], "English text",
             f"{season}English text{weather}English textEnglish textEnglish text{sun}English textEnglish text",
             f"English textEnglish text{wind}English text"),
            (["English text", "English text", "English text", "English text", "English text"], "English text",
             f"{season}English text{wind}English textEnglish textEnglish text{sun}English text",
             f"English text{wind}English text"),
            (["English text", "English text", "English text", "English text", "English text", "English text"], "English text",
             f"{weather}English textEnglish text{sun}English textEnglish text",
             "English textEnglish textTAEnglish textEnglish text"),
            (["English text", "English text", "English text", "English text", "English text", "English text", "English text"], "English text",
             f"{wind}English textEnglish textEnglish text{season}English textEnglish text",
             f"English textEnglish text{wind}English text"),
            (["English text", "English text", "English text", "English text", "English text", "English text", "English text"], "English text",
             f"{sun}English textEnglish text{season}English text",
             "English text"),
            (["English text", "English text", "English text", "English text", "English text"], "English text",
             f"{wind}English textEnglish text{weather}English textEnglish text",
             "English text"),
            (["English text", "English text", "English text", "English text"], "English text",
             f"{time}{weather}English text{sun}English textEnglish text",
             "English textEnglish textEnglish text"),
            (["English text", "English text", "English text", "English text"], "English text",
             f"{season}English text{weather}English text{wind}English textEnglish text",
             "English textEnglish text"),
        ]
        default_signal, default_poem, default_suggestion = (
            "English text",
            f"{weather}English text{time}{wind}English textEnglish textEnglish text",
            "English textEnglish text"
        )
    signal, poem, suggestion = default_signal, default_poem, default_suggestion
    for keys, sig, po, sug in nature_map:
        if any(k in q for k in keys):
            signal, poem, suggestion = sig, po, sug
            break
    return _with_weather_evidence({
        "type": "nature",
        "time": time,
        "season": season,
        "weather": weather,
        "sun": sun,
        "wind": wind,
        "source": w["source"],
        "isReal": bool(w.get("isReal")),
        "signal": signal,
        "poem": poem,
        "suggestion": suggestion,
    }, w)


def generate_nature_brief(question: str, config: Optional[Dict[str, Any]] = None,
                         language: str = "zh-CN", allow_mock: bool = False) -> Dict[str, Any]:
    """English text nature English textEnglish text → English text LLMEnglish text prompt→ English text mock

    allow_mock=True English text Key English text mockallow_mock=False English text Key English text NoApiKeyError
    """
    if config is None:
        config = get_effective_config()
    weather = get_current_weather(config, language=language)

    if has_llm_config(config):
        try:
            result = call_openai_llm(_build_nature_prompt(question, weather), config)
            return _with_weather_evidence(result, weather)
        except Exception as e:
            print(f"[nature] LLM English text: {type(e).__name__}")
            if not allow_mock:
                raise
            print(f"[nature] allow_mock=TrueEnglish text mock")

    if not allow_mock:
        raise NoApiKeyError("English text LLM API KeyEnglish text Demo English text")

    return _mock_nature_brief(question, weather, language=language)
