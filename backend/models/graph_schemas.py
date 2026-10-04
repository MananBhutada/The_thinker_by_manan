from typing import Optional
from pydantic import BaseModel, Field

class GraphExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=12000)
    provider: str = Field(default="byok", pattern="^(byok|free)$")
    apiKey: Optional[str] = Field(default=None, max_length=512)
    llmModel: Optional[str] = Field(default=None, max_length=128)
    llmBaseUrl: Optional[str] = Field(default=None, max_length=2048)
