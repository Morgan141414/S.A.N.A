from app.services.llm_contract import (
    MockLLMProvider,
    build_guarded_response,
    build_prompt_policy,
    should_use_llm,
)
from app.services.policy_router import ConversationMode, route_policy
from app.services.risk_classifier import analyze_risk
from app.services.support_protocols import SupportProtocol, select_support_protocol
from app.services.support_response import build_support_response


class ExplodingProvider:
    name = "exploding"

    def generate(self, request):
        raise TimeoutError("provider timed out")


class CategorizedFailingProvider:
    name = "categorized"

    def generate(self, request):
        error = RuntimeError("invalid json")
        error.reason = "llm_provider_invalid_json"
        raise error


def _pipeline_inputs(message: str, age: int | None = 25):
    assessment = analyze_risk(message)
    mode = route_policy(assessment, age=age)
    protocol = select_support_protocol(message, assessment, mode)
    return assessment, mode, protocol


def test_llm_is_disabled_without_provider_and_preserves_fallback() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)

    result = build_guarded_response(message, assessment, mode, protocol, age=25)

    assert not result.provider_used
    assert not result.fallback_used
    assert result.response == expected
    assert result.safety_check.passed
    assert result.quality_check.passed


def test_llm_policy_allows_only_adult_low_or_medium_support() -> None:
    assert should_use_llm(ConversationMode.SUPPORT, age=25)
    assert should_use_llm(ConversationMode.DEEP_SUPPORT, age=25)
    assert not should_use_llm(ConversationMode.SUPPORT, age=None)
    assert not should_use_llm(ConversationMode.SUPPORT, age=15)
    assert not should_use_llm(ConversationMode.MINOR_SUPPORT, age=15)
    assert not should_use_llm(ConversationMode.MINOR_SAFETY, age=15)
    assert not should_use_llm(ConversationMode.CRISIS, age=25)
    assert not should_use_llm(ConversationMode.EMERGENCY, age=25)


def test_safe_llm_candidate_can_be_used_for_adult_support() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    provider = MockLLMProvider(
        "Я рядом. Похоже, день правда был тяжелым. Попробуй назвать одну вещь, "
        "которая давит сильнее всего, и один маленький шаг на ближайшие 10 минут. "
        "Что сейчас ощущается самым тяжелым?"
    )

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=provider,
    )

    assert result.provider_used
    assert result.provider_name == "mock"
    assert not result.fallback_used
    assert "Что сейчас ощущается самым тяжелым?" in result.response


def test_unsafe_llm_candidate_falls_back() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)
    provider = MockLLMProvider("У тебя депрессия. Все точно будет хорошо.")

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=provider,
    )

    assert result.provider_used
    assert result.fallback_used
    assert result.blocked_reason == "llm_safety_failed"
    assert "definitive_diagnosis" in result.llm_safety_issues
    assert result.response == expected


def test_low_quality_llm_candidate_falls_back() -> None:
    message = "Мне тревожно и страшно"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)
    provider = MockLLMProvider("Расскажи подробнее.")

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=provider,
    )

    assert result.provider_used
    assert result.fallback_used
    assert result.blocked_reason == "llm_quality_failed"
    assert "missing_empathic_reflection" in result.llm_quality_issues
    assert result.response == expected


def test_provider_error_falls_back_without_raising() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=ExplodingProvider(),
    )

    assert result.provider_used
    assert result.provider_name == "exploding"
    assert result.fallback_used
    assert result.blocked_reason == "llm_provider_error"
    assert result.response == expected


def test_provider_error_preserves_categorized_blocked_reason() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=CategorizedFailingProvider(),
    )

    assert result.provider_used
    assert result.provider_name == "categorized"
    assert result.fallback_used
    assert result.blocked_reason == "llm_provider_invalid_json"
    assert result.response == expected


def test_empty_llm_candidate_falls_back() -> None:
    message = "Мне грустно после тяжелого дня"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)
    provider = MockLLMProvider("   ")

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=provider,
    )

    assert result.provider_used
    assert result.fallback_used
    assert result.blocked_reason == "llm_empty_response"
    assert result.response == expected


def test_crisis_never_uses_llm_provider() -> None:
    message = "Я не хочу жить"
    assessment, mode, protocol = _pipeline_inputs(message, age=25)
    expected = build_support_response(message, assessment, mode, protocol, age=25)
    provider = MockLLMProvider("Расскажи подробнее.")

    result = build_guarded_response(
        message,
        assessment,
        mode,
        protocol,
        age=25,
        llm_provider=provider,
    )

    assert mode == ConversationMode.CRISIS
    assert not result.provider_used
    assert result.response == expected
    assert result.safety_check.passed


def test_prompt_policy_contains_safety_boundaries() -> None:
    policy = build_prompt_policy(
        ConversationMode.DEEP_SUPPORT,
        SupportProtocol.DEPRESSIVE_SUPPORT,
        locale="ru",
    )

    assert "Не ставь окончательный диагноз" in policy
    assert "Не назначай" in policy
    assert "Support protocol: depressive_support" in policy


def test_prompt_policy_contains_quality_contract_markers() -> None:
    policy = build_prompt_policy(
        ConversationMode.SUPPORT,
        SupportProtocol.GENERAL_SUPPORT,
        locale="ru",
    )

    assert "Я рядом" in policy
    assert "Похоже" in policy
    assert "один безопасный следующий шаг" in policy
    assert "одним коротким сфокусированным вопросом" in policy


def test_depressive_prompt_policy_requires_self_harm_screen() -> None:
    policy = build_prompt_policy(
        ConversationMode.DEEP_SUPPORT,
        SupportProtocol.DEPRESSIVE_SUPPORT,
        locale="ru",
    )

    assert "навредить себе" in policy
    assert "не жить" in policy
    assert "Я не могу ставить диагноз" in policy


def test_panic_prompt_policy_requires_medical_red_flag_screen() -> None:
    policy = build_prompt_policy(
        ConversationMode.DEEP_SUPPORT,
        SupportProtocol.PANIC_GROUNDING,
        locale="ru",
    )

    assert "боль в груди" in policy
    assert "обморок" in policy
    assert "сильная одышка" in policy
    assert "риск навредить себе" in policy
