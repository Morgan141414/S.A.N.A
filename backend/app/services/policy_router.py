from enum import StrEnum

from app.services.risk_classifier import RiskAssessment, RiskLevel


class ConversationMode(StrEnum):
    SUPPORT = "support"
    DEEP_SUPPORT = "deep_support"
    CRISIS = "crisis"
    EMERGENCY = "emergency"
    MINOR_SUPPORT = "minor_support"


def route_policy(risk_assessment: RiskAssessment, age: int | None = None) -> ConversationMode:
    if risk_assessment.level == RiskLevel.EMERGENCY:
        return ConversationMode.EMERGENCY

    if risk_assessment.level == RiskLevel.HIGH:
        return ConversationMode.CRISIS

    if age is not None and age < 18:
        return ConversationMode.MINOR_SUPPORT

    if risk_assessment.level == RiskLevel.MEDIUM:
        return ConversationMode.DEEP_SUPPORT

    return ConversationMode.SUPPORT
