"""TTS English textedge-tts English text TTS

- GET /api/tts/voices  English textEnglish text
- GET /api/tts/speak?text=&voice=&rate=&pitch=  English text MP3 English text

rate:  English text '+0%''+20%''-10%'
pitch: English text '+0Hz''+5Hz''-5Hz'

ponytail: English textEnglish textEnglish text edge_tts.list_voices() English text
"""

from typing import Optional

import edge_tts
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter()

# English textEnglish text+English text
VOICES = [
    # English textEnglish text
    {"id": "zh-CN-XiaoxiaoNeural",    "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English textEnglish text/English text"},
    {"id": "zh-CN-YunxiNeural",       "lang": "zh-CN", "name": "English text",   "gender": "M", "desc": "English textEnglish text"},
    {"id": "zh-CN-YunjianNeural",     "lang": "zh-CN", "name": "English text",   "gender": "M", "desc": "English textEnglish text"},
    {"id": "zh-CN-YunyangNeural",     "lang": "zh-CN", "name": "English text",   "gender": "M", "desc": "English textEnglish text"},
    {"id": "zh-CN-XiaoyiNeural",      "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English textEnglish text"},
    {"id": "zh-CN-YunxiaNeural",      "lang": "zh-CN", "name": "English text",   "gender": "M", "desc": "English textEnglish text"},
    {"id": "zh-CN-XiaomoNeural",      "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English textEnglish text"},
    {"id": "zh-CN-XiaohanNeural",     "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English text"},
    {"id": "zh-CN-XiaomengNeural",    "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English text"},
    {"id": "zh-CN-XiaoshuangNeural",  "lang": "zh-CN", "name": "English text",   "gender": "F", "desc": "English text"},
    # English text
    {"id": "zh-HK-HiuMaanNeural",     "lang": "yue",   "name": "English text",   "gender": "F", "desc": "English text"},
    {"id": "zh-HK-WanLungNeural",     "lang": "yue",   "name": "English text",   "gender": "M", "desc": "English text"},
    # English text
    {"id": "en-US-AriaNeural",        "lang": "en",    "name": "Aria",   "gender": "F", "desc": "Female US"},
    {"id": "en-US-GuyNeural",         "lang": "en",    "name": "Guy",    "gender": "M", "desc": "Male US"},
    {"id": "en-US-JennyNeural",       "lang": "en",    "name": "Jenny",  "gender": "F", "desc": "Female US (friendly)"},
    # English text
    {"id": "ja-JP-NanamiNeural",      "lang": "ja",    "name": "English text",   "gender": "F", "desc": "English text"},
    {"id": "ja-JP-KeitaNeural",       "lang": "ja",    "name": "English text",   "gender": "M", "desc": "English text"},
    # English text
    {"id": "fr-FR-DeniseNeural",      "lang": "fr",    "name": "Denise", "gender": "F", "desc": "Female FR"},
    {"id": "fr-FR-HenriNeural",       "lang": "fr",    "name": "Henri",  "gender": "M", "desc": "Male FR"},
    # English text
    {"id": "es-ES-ElviraNeural",      "lang": "es",    "name": "Elvira", "gender": "F", "desc": "Female ES"},
    {"id": "es-ES-AlvaroNeural",      "lang": "es",    "name": "Alvaro", "gender": "M", "desc": "Male ES"},
]

# English text
DEFAULT_VOICE = {
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "yue":   "zh-HK-HiuMaanNeural",
    "en":    "en-US-AriaNeural",
    "fr":    "fr-FR-DeniseNeural",
    "ja":    "ja-JP-NanamiNeural",
    "es":    "es-ES-ElviraNeural",
}


@router.get("/api/tts/voices")
def list_voices(lang: Optional[str] = None) -> dict:
    """English textEnglish text lang English text"""
    items = VOICES
    if lang:
        items = [v for v in VOICES if v["lang"] == lang]
    return {"voices": items, "defaults": DEFAULT_VOICE}


def _normalise_rate(rate: float) -> str:
    """English text 0.5~1.5 English text edge-tts English text"""
    pct = int(round((float(rate) - 1.0) * 100))
    pct = max(-50, min(100, pct))
    return f"{pct:+d}%"


def _normalise_pitch(pitch: float) -> str:
    """English text 0.5~1.5 English text edge-tts Hz English text"""
    # English text 0Hz English textEnglish text 1.05 English text +5Hz
    hz = int(round((float(pitch) - 1.0) * 100))
    hz = max(-50, min(50, hz))
    return f"{hz:+d}Hz"


async def _audio_generator(text: str, voice: str, rate: str, pitch: str):
    """English textEnglish text edge-tts English text audio chunk English text yield"""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]


@router.get("/api/tts/speak")
async def speak(
    text: str = Query(..., min_length=1, max_length=5000),
    voice: Optional[str] = None,
    rate: float = Query(0.95, ge=0.5, le=2.0),
    pitch: float = Query(1.05, ge=0.5, le=2.0),
):
    """English text TTS English text MP3 English text

    voice English textzh-CN-XiaoxiaoNeural
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="text English text")
    voice_id = voice or DEFAULT_VOICE["zh-CN"]
    # English text voice English textedge-tts English textEnglish text
    if not any(v["id"] == voice_id for v in VOICES):
        voice_id = DEFAULT_VOICE["zh-CN"]
    rate_str = _normalise_rate(rate)
    pitch_str = _normalise_pitch(pitch)

    filename = "tts.mp3"
    return StreamingResponse(
        _audio_generator(text, voice_id, rate_str, pitch_str),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Cache-Control": "no-cache",
        },
    )
