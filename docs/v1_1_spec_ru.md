# S.A.N.A. v1.1 - Local LLM Preflight

## Цель версии

v1.1 добавляет preflight-проверку локального Ollama-compatible provider перед ручным `llm-smoke`.

Задача версии: не начинать генерацию, если локальный endpoint недоступен или нужная модель не установлена.

## Что добавлено

- `OllamaLLMProvider.preflight()`.
- Проверка endpoint через `GET /api/tags`.
- Проверка наличия модели из `SANA_LLM_MODEL`.
- Блокировка `make llm-smoke` до генерации, если preflight не прошел.
- Явные причины блокировки:
  - `ollama_endpoint_unreachable`;
  - `ollama_model_missing`.
- Тесты для успешного preflight, отсутствующей модели и недоступного endpoint.

## Почему preflight важен

На текущем сервере локальная модель может быть тяжелой для CPU-only inference. Без preflight smoke может долго ждать генерацию и возвращать неясную ошибку.

Preflight дает быстрый ответ:

```text
Ollama запущена?
Модель скачана?
Можно запускать synthetic smoke?
```

Если ответ отрицательный, S.A.N.A. не делает provider generation call.

## Safety contract

Preflight не ослабляет safety-first pipeline:

- не меняет risk classifier;
- не меняет policy router;
- не отправляет crisis/emergency/minor сценарии в LLM;
- не включает LLM по умолчанию;
- не разрешает реальные пользовательские данные в smoke.

Preflight применяется перед manual smoke. Обычный deterministic pipeline продолжает работать без локальной модели.

## Следующие шаги

1. Расширить таксономию ошибок provider: timeout, HTTP status, invalid JSON, resource error.
2. Добавить отдельный отчет preflight в smoke JSON/Markdown.
3. Подготовить инструкцию установки Ollama и загрузки первой модели для тестовой машины.
4. Начать сравнительную матрицу локальных моделей: 7B/8B/12B/14B.
