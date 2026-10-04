"""English text Pydantic English text

English text HTML English textEnglish text 6 English text ModeResult English text
Decision English textexecuted/regret/dialogueHistoryStats English textexecutedRate/regretRate/weekTrend
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ─── English text ───────────────────────────────────────────────────


class Brief(BaseModel):
    """English text - AI English textEnglish text nature English text"""

    summary: str = Field(..., description="English text")
    confidence: int = Field(..., ge=0, le=100, description="English text 0-100")
    perspectives: List[str] = Field(default_factory=list, description="English text")
    nextSteps: List[str] = Field(default_factory=list, description="English text")
    risks: List[str] = Field(default_factory=list, description="English text")
    source: Optional[str] = Field(default=None, description="English textreal / mock")


# ─── 6 English text ModeResult ─────────────────────────────────────────


class RationalResult(BaseModel):
    """English text"""

    type: str = Field(default="rational")
    pros: List[str] = Field(default_factory=list, description="English text")
    cons: List[str] = Field(default_factory=list, description="English text")
    conclusion: str = Field(default="", description="English text")
    score: Optional[Dict[str, Any]] = Field(default=None, description="English text")


class RandomResult(BaseModel):
    """English text"""

    type: str = Field(default="random")
    options: List[str] = Field(default_factory=list, description="6 English text")
    wheelResult: Optional[str] = Field(default=None, description="English text")
    reason: Optional[str] = Field(default=None)


class NatureResult(BaseModel):
    """English text"""

    type: str = Field(default="nature")
    time: str = ""
    season: str = ""
    weather: str = ""
    sun: Optional[str] = ""
    wind: str = ""
    source: str = ""
    isReal: bool = False
    signal: str = ""
    poem: str = ""
    suggestion: str = ""
    city: Optional[str] = ""
    temperature: Optional[str] = ""
    humidity: Optional[str] = ""
    air: Optional[str] = ""
    signals: Optional[Dict[str, Any]] = None


class DialogueResult(BaseModel):
    """English text"""

    type: str = Field(default="dialogue")
    question: str = ""
    options: List[str] = Field(default_factory=list)


class FengshuiResult(BaseModel):
    """English text"""

    type: str = Field(default="fengshui")
    needBirth: bool = False
    question: str = ""
    bazi: str = ""
    wuxing: str = ""
    element: str = ""
    analysis: str = ""
    suggestion: str = ""
    baziAudit: str = ""


# ─── chat English text ─────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """/api/chat English text

    English text v0.7.0 English text
      - weatherKeyEnglish text KeyEnglish text
      - weatherBaseUrl English text
      - weatherAppsecret English textEnglish text weatherKey English text
    """

    question: str = Field(..., min_length=1, max_length=4000, description="English text")
    mode: Literal["auto", "rational", "random", "nature", "dialogue", "fengshui"] = Field(
        default="auto", description="English text"
    )
    # LLM/English textEnglish textEnglish text
    apiKey: Optional[str] = Field(default=None, max_length=512)
    llmModel: Optional[str] = Field(default=None, max_length=128)
    llmBaseUrl: Optional[str] = Field(default=None, max_length=2048)
    weatherKey: Optional[str] = Field(default=None, max_length=512, description="English text Keyv0.7.0 English text")
    weatherBaseUrl: Optional[str] = Field(default=None, max_length=2048, description="English text Base URL")
    weatherAppsecret: Optional[str] = Field(default=None, max_length=512, description="English textEnglish text weatherKey")
    weatherCity: Optional[str] = Field(default=None, max_length=128)
    # English textrational English text
    values: Optional[Dict[str, int]] = Field(default=None)
    # English textbase64 data URLEnglish text
    image: Optional[str] = Field(default=None, max_length=7000000, description="English textbase64 data URL")


class ChatResponse(BaseModel):
    """/api/chat English text"""

    brief: Optional[Brief] = Field(default=None, description="English textnature English text")
    nature: Optional[Dict[str, Any]] = Field(default=None, description="nature English text")
    mode: str = Field(..., description="English textauto English text")
    reply: str = Field(..., description="English text")
    result: Optional[Dict[str, Any]] = Field(default=None, description="English text ModeResultEnglish text")
    autoRecognized: Optional[Dict[str, Any]] = Field(default=None, description="auto English text")
    decisionId: Optional[str] = Field(default=None, description="English text id")


# ─── decision English text ─────────────────────────────────────────────


class DecisionSave(BaseModel):
    """POST /api/decision English text"""

    id: Optional[str] = None
    question: str
    mode: str
    result: Dict[str, Any] = Field(default_factory=dict)
    brief: Optional[Brief] = None
    executed: bool = False
    regret: bool = False
    dialogueHistory: Optional[List[Dict[str, str]]] = None


class DecisionPatch(BaseModel):
    """PATCH /api/decision/:id English text"""

    executed: Optional[bool] = None
    regret: Optional[bool] = None
    dialogueHistory: Optional[List[Dict[str, str]]] = None


# ─── stats English text ────────────────────────────────────────────────


class Stats(BaseModel):
    """/api/stats English text"""

    totalDecisions: int
    modeDistribution: Dict[str, int] = Field(default_factory=dict)
    avgConfidence: float = 0.0
    executedRate: float = 0.0
    regretRate: float = 0.0
    weekTrend: List[Dict[str, Any]] = Field(default_factory=list)


# ─── English text ────────────────────────────────────────────────


class ModeMeta(BaseModel):
    """English text"""

    id: str
    name: str
    icon: str
    color: str
    description: str


# ─── English text ─────────────────────────────────────────────────


class ConfigResponse(BaseModel):
    """/api/config GET English textEnglish text"""

    llm: Dict[str, Any] = Field(default_factory=dict, description="LLM English textEnglish text")
    weather: Dict[str, Any] = Field(default_factory=dict, description="English textEnglish text")
    hasLlm: bool = False
    hasWeather: bool = False


class ConfigUpdate(BaseModel):
    """/api/config POST English text

    English text v0.7.0 English text
      - weather_keyEnglish text KeyEnglish text
      - weather_base_url English text
      - weather_appsecret English textEnglish text weather_key English text
    """

    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None
    weather_key: Optional[str] = None
    weather_base_url: Optional[str] = None
    weather_appsecret: Optional[str] = None  # English text
    weather_city: Optional[str] = None


class PreferencesUpdate(BaseModel):
    """/api/preferences POST English text"""

    language: Optional[str] = None
    default_mode: Optional[str] = None
    theme: Optional[str] = None
    skin: Optional[str] = None
    logo: Optional[str] = None
    auto_speak: Optional[bool] = None
    tts_rate: Optional[float] = None
    tts_pitch: Optional[float] = None
    tts_voice_uri: Optional[str] = None
    values: Optional[Dict[str, int]] = None
    demo_mode: Optional[bool] = None
