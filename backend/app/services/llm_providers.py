from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

from app.core.settings import Settings, get_settings
from app.services.llm_contract import LLMGenerationRequest, LLMGenerationResult, LLMProvider


class LLMPreflightResult(BaseModel):
    passed: bool
    provider_name: str
    model: str | None = None
    issues: list[str] = Field(default_factory=list)


class LLMProviderError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class OpenAILLMProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 10.0,
        max_output_chars: int = 1200,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._max_output_chars = max_output_chars
        self._client = client

    def preflight(self) -> LLMPreflightResult:
        return LLMPreflightResult(
            passed=True,
            provider_name=self.name,
            model=self.model,
        )

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        client = self._client or self._build_client()
        response = client.responses.create(
            model=self.model,
            instructions=request.prompt_policy,
            input=request.message,
            store=False,
        )
        return LLMGenerationResult(
            text=_limit_text(_extract_output_text(response), self._max_output_chars),
            provider_name=self.name,
            model=self.model,
        )

    def _build_client(self) -> Any:
        from openai import OpenAI

        return OpenAI(api_key=self._api_key, timeout=self._timeout_seconds)


class OllamaLLMProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_output_chars: int = 1200,
        num_predict: int = 384,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._timeout_seconds = timeout_seconds
        self._max_output_chars = max_output_chars
        self._num_predict = num_predict
        self._client = client

    def preflight(self) -> LLMPreflightResult:
        created_client = self._client is None
        client = self._client or httpx.Client(timeout=self._timeout_seconds)
        try:
            response = client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
        except (httpx.TimeoutException, TimeoutError):
            return LLMPreflightResult(
                passed=False,
                provider_name=self.name,
                model=self.model,
                issues=["ollama_timeout"],
            )
        except Exception:
            return LLMPreflightResult(
                passed=False,
                provider_name=self.name,
                model=self.model,
                issues=["ollama_endpoint_unreachable"],
            )
        finally:
            if created_client:
                client.close()

        available_models = _extract_ollama_model_names(payload)
        if self.model not in available_models:
            return LLMPreflightResult(
                passed=False,
                provider_name=self.name,
                model=self.model,
                issues=["ollama_model_missing"],
            )
        return LLMPreflightResult(
            passed=True,
            provider_name=self.name,
            model=self.model,
        )

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        created_client = self._client is None
        client = self._client or httpx.Client(timeout=self._timeout_seconds)
        try:
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": request.message,
                    "system": request.prompt_policy,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": self._num_predict,
                    },
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise LLMProviderError("llm_provider_timeout") from exc
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError("llm_provider_http_error") from exc
        except httpx.RequestError as exc:
            raise LLMProviderError("llm_provider_connection_error") from exc
        except ValueError as exc:
            raise LLMProviderError("llm_provider_invalid_json") from exc
        except Exception as exc:
            raise LLMProviderError("llm_provider_error") from exc
        finally:
            if created_client:
                client.close()

        try:
            text = _extract_ollama_response_text(payload)
        except ValueError as exc:
            raise LLMProviderError(str(exc)) from exc
        return LLMGenerationResult(
            text=_limit_text(text, self._max_output_chars),
            provider_name=self.name,
            model=self.model,
        )


def get_configured_llm_provider(settings: Settings | None = None) -> LLMProvider | None:
    settings = settings or get_settings()
    if not settings.sana_llm_enabled:
        return None
    if settings.sana_llm_provider == "openai":
        if not settings.sana_openai_api_key:
            return None
        return OpenAILLMProvider(
            api_key=settings.sana_openai_api_key,
            model=settings.sana_llm_model,
            timeout_seconds=settings.sana_llm_timeout_seconds,
            max_output_chars=settings.sana_llm_max_output_chars,
        )
    if settings.sana_llm_provider == "ollama":
        if not is_ollama_base_url_allowed(
            settings.sana_ollama_base_url,
            allow_private_network=settings.sana_ollama_allow_private_network,
        ):
            return None
        return OllamaLLMProvider(
            base_url=settings.sana_ollama_base_url,
            model=settings.sana_llm_model,
            timeout_seconds=settings.sana_llm_timeout_seconds,
            max_output_chars=settings.sana_llm_max_output_chars,
            num_predict=settings.sana_ollama_num_predict,
        )
    return None


def is_ollama_base_url_allowed(base_url: str, allow_private_network: bool = False) -> bool:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.hostname
    if host is None:
        return False
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True

    try:
        host_ip = ip_address(host)
    except ValueError:
        return False
    if host_ip.is_loopback:
        return True
    return allow_private_network and host_ip.is_private


def _extract_ollama_response_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ValueError("ollama_response_must_be_object")

    text = payload.get("response", "")
    if not isinstance(text, str):
        raise ValueError("ollama_response_must_be_string")
    return text


def _extract_ollama_model_names(payload: Any) -> set[str]:
    if not isinstance(payload, dict):
        raise ValueError("ollama_tags_must_be_object")

    models = payload.get("models", [])
    if not isinstance(models, list):
        raise ValueError("ollama_tags_models_must_be_list")

    model_names: set[str] = set()
    for model in models:
        if not isinstance(model, dict):
            continue
        name = model.get("name")
        if isinstance(name, str):
            model_names.add(name)
    return model_names


def _limit_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return output_text

    output = getattr(response, "output", None)
    if not output:
        return ""

    chunks: list[str] = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)
