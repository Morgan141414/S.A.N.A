from enum import StrEnum

from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskAssessment


class SupportProtocol(StrEnum):
    GENERAL_SUPPORT = "general_support"
    DEPRESSIVE_SUPPORT = "depressive_support"
    ANXIETY_GROUNDING = "anxiety_grounding"
    PANIC_GROUNDING = "panic_grounding"
    GRIEF_LONELINESS = "grief_loneliness"
    CONFLICT_STRESS = "conflict_stress"
    MINOR_SUPPORT = "minor_support"
    MINOR_SAFETY = "minor_safety"
    CRISIS = "crisis"
    EMERGENCY = "emergency"


PROTOCOL_TERMS: dict[SupportProtocol, tuple[str, ...]] = {
    SupportProtocol.PANIC_GROUNDING: (
        "паническая атака",
        "паника",
        "задыхаюсь",
        "сердце бьется",
        "panic attack",
        "can't breathe",
    ),
    SupportProtocol.GRIEF_LONELINESS: (
        "умер",
        "умерла",
        "потерял",
        "потеряла",
        "расставание",
        "одиноко",
        "совсем один",
        "grief",
        "lost someone",
        "lonely",
    ),
    SupportProtocol.CONFLICT_STRESS: (
        "конфликт",
        "поссорился",
        "поссорилась",
        "стресс",
        "выгорание",
        "на работе",
        "ссора",
        "conflict",
        "burnout",
        "stress",
    ),
}


def select_support_protocol(
    message: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
) -> SupportProtocol:
    normalized = message.casefold()

    if conversation_mode == ConversationMode.EMERGENCY:
        return SupportProtocol.EMERGENCY

    if conversation_mode == ConversationMode.CRISIS:
        return SupportProtocol.CRISIS

    if conversation_mode == ConversationMode.MINOR_SAFETY:
        return SupportProtocol.MINOR_SAFETY

    if conversation_mode == ConversationMode.MINOR_SUPPORT:
        return SupportProtocol.MINOR_SUPPORT

    for protocol, terms in PROTOCOL_TERMS.items():
        if any(term in normalized for term in terms):
            return protocol

    features = risk_assessment.features
    if features.depressive_signs >= features.anxiety_signs and features.depressive_signs > 0:
        return SupportProtocol.DEPRESSIVE_SUPPORT

    if features.anxiety_signs > 0:
        return SupportProtocol.ANXIETY_GROUNDING

    if features.isolation_signs > 0:
        return SupportProtocol.GRIEF_LONELINESS

    return SupportProtocol.GENERAL_SUPPORT

