from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


EMERGENCY_TERMS = (
    "сейчас убью себя",
    "сегодня покончу",
    "есть план",
    "есть способ",
    "прямо сейчас",
    "i have a plan",
    "right now",
)

HIGH_RISK_TERMS = (
    "не хочу жить",
    "хочу умереть",
    "суицид",
    "самоубий",
    "порезать себя",
    "навредить себе",
    "убить себя",
    "want to die",
    "kill myself",
    "suicide",
    "self harm",
)

MEDIUM_RISK_TERMS = (
    "депресс",
    "безнад",
    "нет смысла",
    "паничес",
    "тревог",
    "ничего не чувствую",
    "не могу спать",
    "depress",
    "hopeless",
    "panic",
    "anxiety",
)


def classify_risk(message: str) -> RiskLevel:
    normalized = message.casefold()

    if any(term in normalized for term in EMERGENCY_TERMS):
        return RiskLevel.EMERGENCY

    if any(term in normalized for term in HIGH_RISK_TERMS):
        return RiskLevel.HIGH

    if any(term in normalized for term in MEDIUM_RISK_TERMS):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW

