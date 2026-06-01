from types import SimpleNamespace

import httpx

from app.core.settings import get_settings
from app.services.llm_contract import LLMGenerationRequest, build_prompt_policy
from app.services.llm_providers import (
    LLMPreflightResult,
    LLMProviderError,
    OllamaLLMProvider,
    OpenAILLMProvider,
    get_configured_llm_provider,
    is_ollama_base_url_allowed,
)
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
    def __init__(
        self,
        payload: object,
        raises_status: bool = False,
        raises_json: bool = False,
    ) -> None:
        self._payload = payload
        self._raises_status = raises_status
        self._raises_json = raises_json

    def raise_for_status(self) -> None:
        if self._raises_status:
            request = httpx.Request("POST", "http://localhost:11434/api/generate")
            response = httpx.Response(500, request=request)
            raise httpx.HTTPStatusError("status error", request=request, response=response)
        return None

    def json(self) -> object:
        if self._raises_json:
            raise ValueError("invalid json")
        return self._payload


class FakeOllamaClient:
    def __init__(
        self,
        payload: object,
        tags_payload: object | None = None,
        raises_status: bool = False,
        raises_json: bool = False,
        raises_timeout: bool = False,
        raises_request: bool = False,
    ) -> None:
        self._payload = payload
        self._tags_payload = tags_payload or {"models": [{"name": "llama3.1:8b"}]}
        self._raises_status = raises_status
        self._raises_json = raises_json
        self._raises_timeout = raises_timeout
        self._raises_request = raises_request
        self.calls: list[dict[str, object]] = []
        self.closed = False

    def post(self, url: str, json: dict[str, object]):
        self.calls.append({"url": url, "json": json})
        if self._raises_timeout:
            raise httpx.TimeoutException("timed out")
        if self._raises_request:
            request = httpx.Request("POST", url)
            raise httpx.RequestError("connection failed", request=request)
        return FakeOllamaResponse(
            self._payload,
            raises_status=self._raises_status,
            raises_json=self._raises_json,
        )

    def get(self, url: str):
        self.calls.append({"url": url})
        if self._raises_timeout:
            raise httpx.TimeoutException("timed out")
        if self._raises_request:
            request = httpx.Request("GET", url)
            raise httpx.RequestError("connection failed", request=request)
        return FakeOllamaResponse(
            self._tags_payload,
            raises_status=self._raises_status,
            raises_json=self._raises_json,
        )

    def close(self) -> None:
        self.closed = True


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
    assert settings.sana_llm_max_output_chars == 1200
    assert settings.sana_ollama_num_predict == 384
    assert not settings.sana_ollama_allow_private_network
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
            "SANA_LLM_MAX_OUTPUT_CHARS": "900",
            "SANA_OLLAMA_NUM_PREDICT": "256",
        }
    )

    provider = get_configured_llm_provider(settings)

    assert isinstance(provider, OllamaLLMProvider)
    assert provider.model == "llama3.1:8b"
    assert provider.base_url == "http://localhost:11434"


def test_settings_reject_external_ollama_url_by_default() -> None:
    settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "ollama",
            "SANA_OLLAMA_BASE_URL": "https://example.com",
        }
    )

    assert get_configured_llm_provider(settings) is None


def test_settings_allow_private_ollama_ip_only_with_explicit_flag() -> None:
    denied_settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "ollama",
            "SANA_OLLAMA_BASE_URL": "http://192.168.1.10:11434",
        }
    )
    allowed_settings = get_settings(
        {
            "SANA_LLM_ENABLED": "true",
            "SANA_LLM_PROVIDER": "ollama",
            "SANA_OLLAMA_BASE_URL": "http://192.168.1.10:11434",
            "SANA_OLLAMA_ALLOW_PRIVATE_NETWORK": "true",
        }
    )

    assert get_configured_llm_provider(denied_settings) is None
    assert isinstance(get_configured_llm_provider(allowed_settings), OllamaLLMProvider)


def test_ollama_base_url_allowlist() -> None:
    assert is_ollama_base_url_allowed("http://localhost:11434")
    assert is_ollama_base_url_allowed("http://127.0.0.1:11434")
    assert is_ollama_base_url_allowed("http://[::1]:11434")
    assert not is_ollama_base_url_allowed("https://example.com")
    assert not is_ollama_base_url_allowed("http://192.168.1.10:11434")
    assert is_ollama_base_url_allowed(
        "http://192.168.1.10:11434",
        allow_private_network=True,
    )


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
                    "num_predict": 384,
                },
            },
        }
    ]


def test_ollama_provider_preflight_passes_when_model_exists() -> None:
    client = FakeOllamaClient(
        {"response": "ok"},
        tags_payload={"models": [{"name": "llama3.1:8b"}, {"name": "mistral:7b"}]},
    )
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    result = provider.preflight()

    assert result == LLMPreflightResult(
        passed=True,
        provider_name="ollama",
        model="llama3.1:8b",
    )
    assert client.calls == [{"url": "http://localhost:11434/api/tags"}]


def test_ollama_provider_preflight_fails_when_model_is_missing() -> None:
    client = FakeOllamaClient(
        {"response": "ok"},
        tags_payload={"models": [{"name": "mistral:7b"}]},
    )
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    result = provider.preflight()

    assert not result.passed
    assert result.issues == ["ollama_model_missing"]


def test_ollama_provider_preflight_fails_when_endpoint_is_unreachable() -> None:
    client = FakeOllamaClient(
        {"response": "ok"},
        tags_payload={"models": [{"name": "llama3.1:8b"}]},
        raises_status=True,
    )
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    result = provider.preflight()

    assert not result.passed
    assert result.issues == ["ollama_endpoint_unreachable"]


def test_ollama_provider_preflight_reports_timeout() -> None:
    client = FakeOllamaClient({"response": "ok"}, raises_timeout=True)
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    result = provider.preflight()

    assert not result.passed
    assert result.issues == ["ollama_timeout"]


def test_ollama_provider_limits_long_output() -> None:
    client = FakeOllamaClient({"response": "a" * 20})
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        max_output_chars=8,
        client=client,
    )

    result = provider.generate(_request())

    assert result.text == "a" * 8


def test_ollama_provider_rejects_malformed_response_text() -> None:
    client = FakeOllamaClient({"response": {"not": "text"}})
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert str(exc) == "ollama_response_must_be_string"
        assert exc.reason == "ollama_response_must_be_string"
    else:
        raise AssertionError("Expected malformed Ollama payload to raise ValueError")


def test_ollama_provider_rejects_non_object_response_payload() -> None:
    client = FakeOllamaClient(["response"])
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert str(exc) == "ollama_response_must_be_object"
        assert exc.reason == "ollama_response_must_be_object"
    else:
        raise AssertionError("Expected malformed Ollama payload to raise ValueError")


def test_ollama_provider_maps_timeout_error() -> None:
    client = FakeOllamaClient({"response": "ok"}, raises_timeout=True)
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert exc.reason == "llm_provider_timeout"
    else:
        raise AssertionError("Expected timeout to raise LLMProviderError")


def test_ollama_provider_maps_http_status_error() -> None:
    client = FakeOllamaClient({"response": "ok"}, raises_status=True)
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert exc.reason == "llm_provider_http_error"
    else:
        raise AssertionError("Expected HTTP status to raise LLMProviderError")


def test_ollama_provider_maps_connection_error() -> None:
    client = FakeOllamaClient({"response": "ok"}, raises_request=True)
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert exc.reason == "llm_provider_connection_error"
    else:
        raise AssertionError("Expected request error to raise LLMProviderError")


def test_ollama_provider_maps_invalid_json_error() -> None:
    client = FakeOllamaClient({"response": "ok"}, raises_json=True)
    provider = OllamaLLMProvider(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        client=client,
    )

    try:
        provider.generate(_request())
    except LLMProviderError as exc:
        assert exc.reason == "llm_provider_invalid_json"
    else:
        raise AssertionError("Expected invalid JSON to raise LLMProviderError")
