from typing import Any

import httpx

from app.core.settings import Settings, get_settings
from app.services.llm_contract import LLMGenerationRequest, LLMGenerationResult, LLMProvider


class OpenAILLMProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 10.0,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = client

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        client = self._client or self._build_client()
        response = client.responses.create(
            model=self.model,
            instructions=request.prompt_policy,
            input=request.message,
            store=False,
        )
        return LLMGenerationResult(
            text=_extract_output_text(response),
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
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._timeout_seconds = timeout_seconds
        self._client = client

    def generate(self, request: LLMGenerationRequest) -> LLMGenerationResult:
        client = self._client or httpx.Client(timeout=self._timeout_seconds)
        response = client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": request.message,
                "system": request.prompt_policy,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        return LLMGenerationResult(
            text=str(payload.get("response", "")),
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
        )
    if settings.sana_llm_provider == "ollama":
        return OllamaLLMProvider(
            base_url=settings.sana_ollama_base_url,
            model=settings.sana_llm_model,
            timeout_seconds=settings.sana_llm_timeout_seconds,
        )
    return None



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
