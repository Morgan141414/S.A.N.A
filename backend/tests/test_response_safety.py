from app.services.policy_router import ConversationMode
from app.services.risk_classifier import analyze_risk
from app.services.safety_checker import check_response_safety


def test_blocks_definitive_diagnosis() -> None:
    assessment = analyze_risk("Мне плохо")
    result = check_response_safety(
        response="У тебя депрессия.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.SUPPORT,
    )

    assert not result.passed
    assert "definitive_diagnosis" in result.issues


def test_blocks_english_definitive_diagnosis() -> None:
    assessment = analyze_risk("I feel empty")
    result = check_response_safety(
        response="You have depression.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.SUPPORT,
    )

    assert not result.passed
    assert "definitive_diagnosis" in result.issues


def test_blocks_medication_advice() -> None:
    assessment = analyze_risk("Мне тревожно")
    result = check_response_safety(
        response="Начни принимать таблетки и увеличь дозу через неделю.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.DEEP_SUPPORT,
    )

    assert not result.passed
    assert "medication_advice" in result.issues


def test_blocks_english_medication_advice() -> None:
    assessment = analyze_risk("I feel anxious")
    result = check_response_safety(
        response="Take Xanax tonight and double your dose if it does not work.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.DEEP_SUPPORT,
    )

    assert not result.passed
    assert "medication_advice" in result.issues


def test_blocks_secrecy_traps() -> None:
    assessment = analyze_risk("Мне страшно дома")
    result = check_response_safety(
        response="Это останется между нами, никому не говори.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.SUPPORT,
    )

    assert not result.passed
    assert "secrecy_or_confidentiality_trap" in result.issues


def test_crisis_response_requires_crisis_step() -> None:
    assessment = analyze_risk("Я не хочу жить")
    result = check_response_safety(
        response="Расскажи подробнее, почему тебе так тяжело.",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.CRISIS,
    )

    assert not result.passed
    assert "missing_crisis_step" in result.issues
    assert "экстренной" in result.safe_response
    assert "физической безопасности" in result.safe_response


def test_safe_crisis_response_passes() -> None:
    assessment = analyze_risk("Я не хочу жить")
    result = check_response_safety(
        response=(
            "Мне важно, чтобы ты не был один. Пожалуйста, позови доверенного человека "
            "сейчас. Ты в физической безопасности?"
        ),
        risk_assessment=assessment,
        conversation_mode=ConversationMode.CRISIS,
    )

    assert result.passed
