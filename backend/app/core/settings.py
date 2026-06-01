import os
from collections.abc import Mapping

from pydantic import BaseModel, Field


class Settings(BaseModel):
    sana_llm_enabled: bool = False
    sana_llm_provider: str = "none"
    sana_llm_model: str = "gpt-5.5"
    sana_llm_timeout_seconds: float = Field(default=10.0, gt=0)
    sana_openai_api_key: str | None = None
    sana_provider_smoke_enabled: bool = False
    sana_provider_smoke_allow_network: bool = False
    sana_provider_smoke_ack_no_user_data: bool = False
    sana_provider_smoke_dataset: str = "synthetic_only"


def get_settings(environ: Mapping[str, str] | None = None) -> Settings:
    values = os.environ if environ is None else environ
    return Settings(
        sana_llm_enabled=_env_bool(values.get("SANA_LLM_ENABLED")),
        sana_llm_provider=values.get("SANA_LLM_PROVIDER", "none").strip().lower() or "none",
        sana_llm_model=values.get("SANA_LLM_MODEL", "gpt-5.5").strip() or "gpt-5.5",
        sana_llm_timeout_seconds=_env_float(values.get("SANA_LLM_TIMEOUT_SECONDS"), 10.0),
        sana_openai_api_key=values.get("SANA_OPENAI_API_KEY") or None,
        sana_provider_smoke_enabled=_env_bool(values.get("SANA_PROVIDER_SMOKE_ENABLED")),
        sana_provider_smoke_allow_network=_env_bool(
            values.get("SANA_PROVIDER_SMOKE_ALLOW_NETWORK")
        ),
        sana_provider_smoke_ack_no_user_data=_env_bool(
            values.get("SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA")
        ),
        sana_provider_smoke_dataset=values.get(
            "SANA_PROVIDER_SMOKE_DATASET",
            "synthetic_only",
        ).strip()
        or "synthetic_only",
    )


def _env_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _env_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default
