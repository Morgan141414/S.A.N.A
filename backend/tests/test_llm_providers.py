from types import SimpleNamespace

from app.core.settings import get_settings
from app.services.llm_contract import LLMGenerationRequest, build_prompt_policy
from app.services.llm_providers import OllamaLLMProvider, OpenAILLMProvider, get_configured_llm_provider
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


class FakeOllamaResponse:
    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return self._payload


class FakeOllamaClient:
    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, json: dict[str, object]):
        self.calls.append({"url": url, "json": json})
        return FakeOllamaResponse(self._payload)


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
    assert settings.sana_llm_model == "llama3.1:8b"
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


def test_settings_create_ollama_provider_without_api_key() -> None:
    settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "ollama",
            "SANA_LLM_MODEL": "llama3.1:8b",
            "SANA_OLLAMA_BASE_URL": "http://localhost:11434/",
        }
    )

    provider = get_configured_llm_provider(settings)

    assert isinstance(provider, OllamaLLMProvider)
    assert provider.model == "llama3.1:8b"
    assert provider.base_url == "http://localhost:11434"


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


def test_ollama_provider_uses_generate_api_with_system_policy() -> None:
    client = FakeOllamaClient({"response": "Я рядом. Что сейчас тяжелее всего?"})
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    result = provider.generate(_request())

    assert result.provider_name == "ollama"
    assert result.model == "llama3.1:8b"
    assert result.text == "Я рядом. Что сейчас тяжелее всего?"
    assert client.calls == [
        {
            "url": "http://localhost:11434/api/generate",
            "json": {
                "model": "llama3.1:8b",
                "prompt": "Мне грустно после тяжелого дня",
                "system": _request().prompt_policy,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
        }
    ]
