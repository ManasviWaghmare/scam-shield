"""Request/response models and limits for /assistant."""
from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    text: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    message: str = Field(default="", max_length=4000)
    lang: str = "en"
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=10)


class Citation(BaseModel):
    id: str
    title: str
    url: str
    passage: str


class ChatResponse(BaseModel):
    answer: str
    evidence_status: str  # supported | insufficient | conflicting
    citations: list[Citation] = []
    safety_notice: str = "Do not click suspicious links or share OTPs/PINs. Call 1930 for fraud."
    abstained: bool = False
    verdict: dict | None = None
    generator: str = "offline"  # offline | hosted
