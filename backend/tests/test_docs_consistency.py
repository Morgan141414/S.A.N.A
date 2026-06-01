from pathlib import Path

from app.services.policy_router import ConversationMode
from app.services.risk_classifier import RiskLevel
from app.services.support_protocols import SupportProtocol


ROOT_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT_DIR / "docs"


def test_risk_levels_are_documented() -> None:
    docs_text = (DOCS_DIR / "technical_spec_ru.md").read_text(encoding="utf-8")

    for level in RiskLevel:
        assert level.value in docs_text


def test_conversation_modes_are_documented() -> None:
    docs_text = (DOCS_DIR / "architecture.md").read_text(encoding="utf-8")

    for mode in ConversationMode:
        assert mode.value in docs_text


def test_support_protocols_are_documented() -> None:
    docs_text = (DOCS_DIR / "architecture.md").read_text(encoding="utf-8")

    for protocol in SupportProtocol:
        assert protocol.value in docs_text


def test_architecture_uses_current_response_module_name() -> None:
    docs_text = (DOCS_DIR / "architecture.md").read_text(encoding="utf-8")

    assert "support_response" in docs_text
    assert "`response_generator`" not in docs_text
