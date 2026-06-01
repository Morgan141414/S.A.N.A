from app.services.risk_classifier import RiskLevel, classify_risk


def test_low_risk_message() -> None:
    assert classify_risk("Мне грустно и я устал") == RiskLevel.LOW


def test_medium_risk_message() -> None:
    assert classify_risk("У меня тревога и я не могу спать") == RiskLevel.MEDIUM


def test_high_risk_message() -> None:
    assert classify_risk("Я не хочу жить") == RiskLevel.HIGH


def test_emergency_message() -> None:
    assert classify_risk("У меня есть план и я сделаю это прямо сейчас") == RiskLevel.EMERGENCY

