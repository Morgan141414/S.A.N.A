from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.risk_classifier import RiskLevel, classify_risk
from app.services.support_response import build_support_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    age: int | None = Field(default=None, ge=0, le=120)
    locale: str = Field(default="ru")


class ChatResponse(BaseModel):
    risk_level: RiskLevel
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    risk_level = classify_risk(request.message)
    response = build_support_response(
        message=request.message,
        risk_level=risk_level,
        age=request.age,
        locale=request.locale,
    )
    return ChatResponse(risk_level=risk_level, response=response)

