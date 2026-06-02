# S.A.N.A. v1.3 - LLM Smoke Report Summary

## Цель версии

v1.3 добавляет сводку в LLM smoke report, чтобы ручные прогоны локальных моделей было проще анализировать.

До этой версии каждый scenario result содержал `blocked_reason`, но общая сводка не показывала, сколько раз модель была использована и сколько раз система ушла в fallback.

## Что добавлено

- `candidate_used_count` - сколько сценариев приняли LLM candidate.
- `fallback_count` - сколько сценариев вернулись к deterministic fallback.
- `blocked_reasons` - агрегированная сводка причин блокировки.
- Markdown-раздел `Blocked Reasons`.
- Тесты для успешного smoke и smoke с fallback.

## Зачем это нужно

Когда мы начнем сравнивать локальные модели, одного pass/fail будет мало.

Нам нужно видеть:

- модель реально дала usable candidate или почти всегда ушла в fallback;
- какие причины блокировки повторяются;
- проблема в safety, quality, provider runtime или malformed response;
- стоит ли модель дальше улучшать prompt/policy, менять модель или усиливать runtime.

## Safety contract

Сводка не содержит реальные пользовательские данные и не раскрывает raw provider errors.

В report попадают только безопасные диагностические коды:

```text
llm_safety_failed
llm_quality_failed
llm_provider_timeout
llm_provider_http_error
llm_provider_connection_error
llm_provider_invalid_json
ollama_response_must_be_object
ollama_response_must_be_string
llm_empty_response
```

## Следующие шаги

1. Добавить отдельный preflight summary в report.
2. Подготовить инструкцию установки Ollama.
3. Начать controlled smoke-прогоны первой локальной модели.
