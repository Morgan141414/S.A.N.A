from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.llm_contract import build_guarded_response
from app.services.llm_providers import get_configured_llm_provider
from app.services.policy_router import ConversationMode, route_policy
from app.services.response_quality import ResponseQualityCheck
from app.services.risk_classifier import RiskAssessment, RiskLevel, analyze_risk
from app.services.safety_checker import SafetyCheck
from app.services.support_protocols import SupportProtocol, select_support_protocol

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    age: int | None = Field(default=None, ge=0, le=120)
    locale: str = Field(default="ru")


class ChatResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: float
    conversation_mode: ConversationMode
    support_protocol: SupportProtocol
    risk_assessment: RiskAssessment
    safety_check: SafetyCheck
    quality_check: ResponseQualityCheck
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    risk_assessment = analyze_risk(request.message)
    conversation_mode = route_policy(risk_assessment=risk_assessment, age=request.age)
    support_protocol = select_support_protocol(
        message=request.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    guarded_response = build_guarded_response(
        message=request.message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        age=request.age,
        locale=request.locale,
        llm_provider=get_configured_llm_provider(),
    )
    return ChatResponse(
        risk_level=risk_assessment.level,
        risk_score=risk_assessment.score,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        risk_assessment=risk_assessment,
        safety_check=guarded_response.safety_check,
        quality_check=guarded_response.quality_check,
        response=guarded_response.response,
    )
