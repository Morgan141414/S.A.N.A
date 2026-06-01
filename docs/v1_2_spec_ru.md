# S.A.N.A. v1.2 - Local LLM Error Taxonomy

## Цель версии

v1.2 добавляет различимые причины сбоя локального LLM provider.

До этой версии большинство ошибок локальной модели схлопывались в общий `llm_provider_error`. Теперь S.A.N.A. может отличать timeout, HTTP status error, connection error, invalid JSON и malformed Ollama payload.

## Что добавлено

- `LLMProviderError` с безопасным полем `reason`.
- Маппинг ошибок Ollama generation:
  - `llm_provider_timeout`;
  - `llm_provider_http_error`;
  - `llm_provider_connection_error`;
  - `llm_provider_invalid_json`;
  - `ollama_response_must_be_object`;
  - `ollama_response_must_be_string`;
  - `llm_provider_error`.
- Guarded response сохраняет categorized `blocked_reason`.
- Preflight отдельно различает:
  - `ollama_timeout`;
  - `ollama_endpoint_unreachable`;
  - `ollama_model_missing`.
- Добавлены unit tests без real network.

## Safety contract

Даже при точной диагностике ошибок поведение остается безопасным:

- raw exception не показывается пользователю;
- stack trace не попадает в user-facing response;
- provider failure всегда ведет к deterministic fallback;
- crisis, emergency и minor safety сценарии по-прежнему не отправляются в LLM;
- smoke остается gated и synthetic-only.

## Зачем это нужно

Для локального ИИ диагностика особенно важна. На CPU-only сервере проблемы могут быть разными:

- модель не скачана;
- Ollama не запущена;
- endpoint отвечает ошибкой;
- генерация зависла;
- модель вернула пустой или неправильный JSON;
- ответ нарушил safety/quality правила.

v1.2 позволяет отличать эти причины и строить дальше нормальные отчеты качества.

## Следующие шаги

1. Добавить breakdown provider errors в JSON/Markdown smoke report.
2. Добавить инструкцию установки Ollama и загрузки первой модели.
3. Начать сравнительные smoke-прогоны локальных моделей.
