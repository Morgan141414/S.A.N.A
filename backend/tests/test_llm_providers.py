from types import SimpleNamespace

from app.core.settings import get_settings
from app.services.llm_contract import LLMGenerationRequest, build_prompt_policy
from app.services.llm_providers import OpenAILLMProvider, get_configured_llm_provider
from app.services.policy_router import ConversationMode
from app.services.risk_classifier import analyze_risk
from app.services.support_protocols import SupportProtocol


class FakeOpenAIResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text: str) -> None:
        self.responses = FakeOpenAIResponses(output_text)


def _request() -> LLMGenerationRequest:
    assessment = analyze_risk("Мне грустно после тяжелого дня")
    return LLMGenerationRequest(
        message="Мне грустно после тяжелого дня",
        risk_assessment=assessment,
        conversation_mode=ConversationMode.SUPPORT,
        support_protocol=SupportProtocol.GENERAL_SUPPORT,
        age=25,
        locale="ru",
        prompt_policy=build_prompt_policy(
            ConversationMode.SUPPORT,
            SupportProtocol.GENERAL_SUPPORT,
            locale="ru",
        ),
    )


def test_settings_disable_llm_by_default() -> None:
    settings = get_settings({})

    assert not settings.sana_llm_enabled
    assert settings.sana_llm_provider == "none"
    assert get_configured_llm_provider(settings) is None


def test_settings_create_openai_provider_only_when_enabled_with_key() -> None:
    settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "openai",
            "SANA_LLM_MODEL": "gpt-5.5",
            "SANA_OPENAI_API_KEY": "test-key",
        }
    )

    provider = get_configured_llm_provider(settings)

    assert isinstance(provider, OpenAILLMProvider)
    assert provider.model == "gpt-5.5"


def test_settings_do_not_create_openai_provider_without_key() -> None:
    settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "openai",
        }
    )

    assert get_configured_llm_provider(settings) is None


def test_openai_provider_uses_responses_api_without_storing_state() -> None:
    client = FakeOpenAIClient("Я рядом. Попробуй назвать, что тяжелее всего?")
    provider = OpenAILLMProvider(
        api_key="test-key",
        model="gpt-5.5",
        client=client,
    )

    result = provider.generate(_request())

    assert result.provider_name == "openai"
    assert result.model == "gpt-5.5"
    assert result.text == "Я рядом. Попробуй назвать, что тяжелее всего?"
    assert client.responses.calls == [
        {
            "model": "gpt-5.5",
            "instructions": _request().prompt_policy,
            "input": "Мне грустно после тяжелого дня",
            "store": False,
        }
    ]
