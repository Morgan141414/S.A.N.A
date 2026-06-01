from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import RiskAssessment, RiskLevel, analyze_risk
from app.services.safety_checker import SafetyCheck, check_response_safety
from app.services.support_response import build_support_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    age: int | None = Field(default=None, ge=0, le=120)
    locale: str = Field(default="ru")


class ChatResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: float
    conversation_mode: ConversationMode
    risk_assessment: RiskAssessment
    safety_check: SafetyCheck
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    risk_assessment = analyze_risk(request.message)
    conversation_mode = route_policy(risk_assessment=risk_assessment, age=request.age)
    response = build_support_response(
        message=request.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        age=request.age,
        locale=request.locale,
    )
    safety_check = check_response_safety(
        response=response,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    return ChatResponse(
        risk_level=risk_assessment.level,
        risk_score=risk_assessment.score,
        conversation_mode=conversation_mode,
        risk_assessment=risk_assessment,
        safety_check=safety_check,
        response=safety_check.safe_response,
    )
