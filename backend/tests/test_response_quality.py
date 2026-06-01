from app.services.policy_router import ConversationMode, route_policy
from app.services.response_quality import check_response_quality
from app.services.risk_classifier import RiskLevel, analyze_risk
from app.services.support_protocols import SupportProtocol, select_support_protocol
from app.services.support_response import build_support_response


def test_depressive_response_asks_self_harm_screen() -> None:
    assessment = analyze_risk("У меня депрессия и нет сил")
    mode = route_policy(assessment, age=25)
    protocol = select_support_protocol("У меня депрессия и нет сил", assessment, mode)
    response = build_support_response("У меня депрессия и нет сил", assessment, mode, protocol)

    quality = check_response_quality(response, assessment.level, mode, protocol)

    assert protocol == SupportProtocol.DEPRESSIVE_SUPPORT
    assert "навредить себе" in response
    assert quality.passed


def test_panic_response_checks_medical_red_flags() -> None:
    assessment = analyze_risk("У меня паническая атака и сердце бьется")
    mode = route_policy(assessment, age=25)
    protocol = select_support_protocol("У меня паническая атака и сердце бьется", assessment, mode)
    response = build_support_response(
        "У меня паническая атака и сердце бьется",
        assessment,
        mode,
        protocol,
    )

    quality = check_response_quality(response, assessment.level, mode, protocol)

    assert protocol == SupportProtocol.PANIC_GROUNDING
    assert "боль в груди" in response
    assert quality.passed


def test_quality_checker_rejects_generic_response() -> None:
    quality = check_response_quality(
        response="Расскажи подробнее.",
        risk_level=RiskLevel.MEDIUM,
        conversation_mode=ConversationMode.DEEP_SUPPORT,
        support_protocol=SupportProtocol.ANXIETY_GROUNDING,
    )

    assert not quality.passed
    assert "missing_empathic_reflection" in quality.issues
    assert "missing_next_step" in quality.issues


def test_quality_checker_rejects_long_crisis_response() -> None:
    response = " ".join(["слово"] * 95) + " Ты сейчас в физической безопасности?"
    quality = check_response_quality(
        response=response,
        risk_level=RiskLevel.HIGH,
        conversation_mode=ConversationMode.CRISIS,
        support_protocol=SupportProtocol.CRISIS,
    )

    assert not quality.passed
    assert "crisis_response_too_long" in quality.issues
