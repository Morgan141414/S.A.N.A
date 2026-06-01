from enum import StrEnum
from math import exp

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class RiskFeatures(BaseModel):
    suicidal_ideation: float = Field(ge=0.0, le=1.0)
    depressive_signs: float = Field(ge=0.0, le=1.0)
    anxiety_signs: float = Field(ge=0.0, le=1.0)
    self_harm_signs: float = Field(ge=0.0, le=1.0)
    isolation_signs: float = Field(ge=0.0, le=1.0)
    immediate_plan: float = Field(ge=0.0, le=1.0)


class RiskAssessment(BaseModel):
    level: RiskLevel
    score: float = Field(ge=0.0, le=1.0)
    features: RiskFeatures
    matched_terms: list[str]
    rationale: str


FEATURE_TERMS: dict[str, tuple[str, ...]] = {
    "suicidal_ideation": (
        "не хочу жить",
        "хочу умереть",
        "лучше умереть",
        "суицид",
        "самоубий",
        "убить себя",
        "want to die",
        "kill myself",
        "suicide",
    ),
    "depressive_signs": (
        "депресс",
        "безнад",
        "нет смысла",
        "ничего не чувствую",
        "нет сил",
        "не могу встать",
        "depress",
        "hopeless",
        "nothing matters",
    ),
    "anxiety_signs": (
        "паничес",
        "паника",
        "тревог",
        "тревожно",
        "задыхаюсь",
        "сердце бьется",
        "не могу спать",
        "panic",
        "anxiety",
        "anxious",
        "can't sleep",
    ),
    "self_harm_signs": (
        "порезать себя",
        "режу себя",
        "порезал себе",
        "навредить себе",
        "самоповреж",
        "self harm",
        "hurt myself",
        "cut myself",
    ),
    "isolation_signs": (
        "никому не нужен",
        "никто не понимает",
        "совсем один",
        "одиноко",
        "некому сказать",
        "no one cares",
        "alone",
        "lonely",
    ),
    "immediate_plan": (
        "сейчас убью себя",
        "сегодня покончу",
        "есть план",
        "есть способ",
        "есть таблетки",
        "выпил много таблеток",
        "уже порезал",
        "есть нож",
        "стою на крыше",
        "не могу оставаться в безопасности",
        "убить кого-то",
        "навредить кому-то",
        "сделаю это сегодня",
        "i have a plan",
        "i overdosed",
        "overdosed on pills",
        "i have a gun",
        "cannot stay safe",
        "can't stay safe",
        "kill someone right now",
    ),
}

WEIGHTS = {
    "suicidal_ideation": 3.0,
    "depressive_signs": 1.5,
    "anxiety_signs": 1.0,
    "self_harm_signs": 3.0,
    "isolation_signs": 1.0,
    "immediate_plan": 5.0,
}

BIAS = -1.5


def classify_risk(message: str) -> RiskLevel:
    return analyze_risk(message).level


def analyze_risk(message: str) -> RiskAssessment:
    normalized = message.casefold()
    features, matched_terms = _extract_features(normalized)

    if features.immediate_plan >= 0.5:
        return RiskAssessment(
            level=RiskLevel.EMERGENCY,
            score=1.0,
            features=features,
            matched_terms=matched_terms,
            rationale="Найдены признаки немедленной опасности: план, срок, средство или действие.",
        )

    score = _score_features(features)
    level = _level_from_score(score)

    if features.suicidal_ideation >= 0.5 or features.self_harm_signs >= 0.5:
        level = max(level, RiskLevel.HIGH, key=_risk_order)
    elif _has_non_crisis_distress(features):
        level = max(RiskLevel.MEDIUM, level, key=_risk_order)
        if level == RiskLevel.HIGH:
            level = RiskLevel.MEDIUM

    return RiskAssessment(
        level=level,
        score=score,
        features=features,
        matched_terms=matched_terms,
        rationale=_build_rationale(level=level, matched_terms=matched_terms),
    )


def _extract_features(normalized_message: str) -> tuple[RiskFeatures, list[str]]:
    values: dict[str, float] = {}
    matched_terms: list[str] = []

    for feature_name, terms in FEATURE_TERMS.items():
        matches = [term for term in terms if term in normalized_message]
        matched_terms.extend(matches)
        values[feature_name] = min(1.0, len(matches) / 2) if matches else 0.0

    return RiskFeatures(**values), matched_terms


def _score_features(features: RiskFeatures) -> float:
    z = (
        WEIGHTS["suicidal_ideation"] * features.suicidal_ideation
        + WEIGHTS["depressive_signs"] * features.depressive_signs
        + WEIGHTS["anxiety_signs"] * features.anxiety_signs
        + WEIGHTS["self_harm_signs"] * features.self_harm_signs
        + WEIGHTS["isolation_signs"] * features.isolation_signs
        + WEIGHTS["immediate_plan"] * features.immediate_plan
        + BIAS
    )
    return round(_sigmoid(z), 4)


def _sigmoid(value: float) -> float:
    return 1 / (1 + exp(-value))


def _level_from_score(score: float) -> RiskLevel:
    if score >= 0.85:
        return RiskLevel.EMERGENCY
    if score >= 0.60:
        return RiskLevel.HIGH
    if score >= 0.30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _has_non_crisis_distress(features: RiskFeatures) -> bool:
    return any(
        value >= 0.5
        for value in (
            features.depressive_signs,
            features.anxiety_signs,
            features.isolation_signs,
        )
    )


def _risk_order(level: RiskLevel) -> int:
    return {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.EMERGENCY: 3,
    }[level]


def _build_rationale(level: RiskLevel, matched_terms: list[str]) -> str:
    if not matched_terms:
        return "Явных высокорисковых маркеров не найдено."

    if level == RiskLevel.HIGH:
        return "Найдены маркеры высокого риска, связанные с самоповреждением или смертью."

    if level == RiskLevel.MEDIUM:
        return "Найдены маркеры устойчивого эмоционального неблагополучия."

    return "Найдены отдельные признаки эмоционального напряжения."
