from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class _ProviderFields(BaseModel):
    provider: str = Field(default="byok", pattern="^(byok|free)$")
    apiKey: Optional[str] = Field(default=None, max_length=512)
    llmModel: Optional[str] = Field(default=None, max_length=128)
    llmBaseUrl: Optional[str] = Field(default=None, max_length=2048)


class GraphExtractRequest(_ProviderFields):
    text: str = Field(..., min_length=1, max_length=12000)


class GraphChatTurn(BaseModel):
    role: Literal["user", "coach"] = "user"
    text: str = Field(default="", max_length=2000)


class GraphChatRequest(_ProviderFields):
    """Chat about one node. The server builds the graph context itself - the client only sends the node id."""
    nodeId: Optional[str] = Field(default="root", max_length=64)
    question: str = Field(..., min_length=1, max_length=2000)
    mode: Literal["founder", "product", "people", "money", "growth", "conflict"] = "founder"
    history: List[GraphChatTurn] = Field(default_factory=list, max_length=12)
    sessionId: Optional[str] = Field(default=None, max_length=128)


class GraphProposalRequest(BaseModel):
    nodeId: str = Field(..., max_length=64)
    action: Literal["accept", "reject", "ignore"]


class GraphPositionsRequest(BaseModel):
    positions: Dict[str, List[float]] = Field(default_factory=dict)
