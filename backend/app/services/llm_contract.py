from typing import Protocol

from pydantic import BaseModel, Field

from app.services.policy_router import ConversationMode
from app.services.response_quality import ResponseQualityCheck, check_response_quality
from app.services.risk_classifier import RiskAssessment
from app.services.safety_checker import SafetyCheck, check_response_safety
from app.services.support_protocols import SupportProtocol
from app.services.support_response import build_support_response


class LLMGenerationRequest(BaseModel):
    message: str
    risk_assessment: RiskAssessment
    conversation_mode: ConversationMode
    support_protocol: SupportProtocol
    age: int | None = None
    locale: str = "ru"
    prompt_policy: str


class LLMGenerationResult(BaseModel):
    text: str
    provider_name: str
    model: str | None = None


class GuardedGenerationResult(BaseModel):
    response: str
    provider_used: bool
    provider_name: str | None = None
    candidate_response: str | None = None
    fallback_used: bool
    blocked_reason: str | None = None
    llm_safety_issues: list[str] = Field(default_factory=list)
    llm_quality_issues: list[str] = Field(default_factory=list)
    safety_check: SafetyCheck
    quality_check: ResponseQualityCheck


class LLMProvider(Protocol):
    name: str

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        raise NotImplementedError


class MockLLMProvider:
    name = "mock"

    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        return LLMGenerationResult(text=self._response, provider_name=self.name)


def build_prompt_policy(
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
    locale: str = "ru",
) -> str:
    language_rule = "Отвечай на русском языке." if locale == "ru" else "Answer in English."
    return "\n".join(
        [
            language_rule,
            "Ты S.A.N.A., ассистент эмоциональной поддержки, а не врач и не экстренная служба.",
            "Не ставь окончательный диагноз.",
            "Не назначай, не отменяй и не меняй дозировку лекарств.",
            "Не обещай полную безопасность, исцеление или гарантированный результат.",
            "Не проси скрывать опасность и не обещай абсолютную конфиденциальность.",
            "Дай эмпатичное отражение, один безопасный следующий шаг и один короткий вопрос.",
            f"Conversation mode: {conversation_mode.value}.",
            f"Support protocol: {support_protocol.value}.",
        ]
    )


def should_use_llm(conversation_mode: ConversationMode, age: int | None = None) -> bool:
    if age is None or age < 18:
        return False
    return conversation_mode in {ConversationMode.SUPPORT, ConversationMode.DEEP_SUPPORT}


def build_guarded_response(
    message: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
    age: int | None = None,
    locale: str = "ru",
    llm_provider: LLMProvider | None = None,
) -> GuardedGenerationResult:
    deterministic_response = build_support_response(
        message=message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        age=age,
        locale=locale,
    )

    if llm_provider is None or not should_use_llm(conversation_mode, age):
        return _finalize_response(
            response=deterministic_response,
            risk_assessment=risk_assessment,
            conversation_mode=conversation_mode,
            support_protocol=support_protocol,
            provider_used=False,
            provider_name=None,
            fallback_used=False,
            blocked_reason=None,
        )

    request = LLMGenerationRequest(
        message=message,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
        age=age,
        locale=locale,
        prompt_policy=build_prompt_policy(conversation_mode, support_protocol, locale),
    )
    try:
        llm_result = llm_provider.generate(request)
    except Exception:
        return _finalize_response(
            response=deterministic_response,
            risk_assessment=risk_assessment,
            conversation_mode=conversation_mode,
            support_protocol=support_protocol,
            provider_used=True,
            provider_name=getattr(llm_provider, "name", None),
            fallback_used=True,
            blocked_reason="llm_provider_error",
        )

    if not llm_result.text.strip():
        return _finalize_response(
            response=deterministic_response,
            risk_assessment=risk_assessment,
            conversation_mode=conversation_mode,
            support_protocol=support_protocol,
            provider_used=True,
            provider_name=llm_result.provider_name,
            candidate_response=llm_result.text,
            fallback_used=True,
            blocked_reason="llm_empty_response",
        )

    llm_safety_check = check_response_safety(
        response=llm_result.text,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    if not llm_safety_check.passed:
        return _finalize_response(
            response=deterministic_response,
            risk_assessment=risk_assessment,
            conversation_mode=conversation_mode,
            support_protocol=support_protocol,
            provider_used=True,
            provider_name=llm_result.provider_name,
            candidate_response=llm_result.text,
            fallback_used=True,
            blocked_reason="llm_safety_failed",
            llm_safety_issues=llm_safety_check.issues,
        )

    llm_quality_check = check_response_quality(
        response=llm_safety_check.safe_response,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
    )
    if not llm_quality_check.passed:
        return _finalize_response(
            response=deterministic_response,
            risk_assessment=risk_assessment,
            conversation_mode=conversation_mode,
            support_protocol=support_protocol,
            provider_used=True,
            provider_name=llm_result.provider_name,
            candidate_response=llm_result.text,
            fallback_used=True,
            blocked_reason="llm_quality_failed",
            llm_quality_issues=llm_quality_check.issues,
        )

    return GuardedGenerationResult(
        response=llm_safety_check.safe_response,
        provider_used=True,
        provider_name=llm_result.provider_name,
        candidate_response=llm_result.text,
        fallback_used=False,
        blocked_reason=None,
        llm_safety_issues=[],
        llm_quality_issues=[],
        safety_check=llm_safety_check,
        quality_check=llm_quality_check,
    )


def _finalize_response(
    response: str,
    risk_assessment: RiskAssessment,
    conversation_mode: ConversationMode,
    support_protocol: SupportProtocol,
    provider_used: bool,
    provider_name: str | None,
    fallback_used: bool,
    blocked_reason: str | None,
    candidate_response: str | None = None,
    llm_safety_issues: list[str] | None = None,
    llm_quality_issues: list[str] | None = None,
) -> GuardedGenerationResult:
    safety_check = check_response_safety(
        response=response,
        risk_assessment=risk_assessment,
        conversation_mode=conversation_mode,
    )
    quality_check = check_response_quality(
        response=safety_check.safe_response,
        risk_level=risk_assessment.level,
        conversation_mode=conversation_mode,
        support_protocol=support_protocol,
    )
    return GuardedGenerationResult(
        response=safety_check.safe_response,
        provider_used=provider_used,
        provider_name=provider_name,
        candidate_response=candidate_response,
        fallback_used=fallback_used,
        blocked_reason=blocked_reason,
        llm_safety_issues=llm_safety_issues or [],
        llm_quality_issues=llm_quality_issues or [],
        safety_check=safety_check,
        quality_check=quality_check,
    )
