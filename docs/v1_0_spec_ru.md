# S.A.N.A. v1.0 - Local LLM Runtime Guardrails

## Цель версии

v1.0 закрепляет направление S.A.N.A. без обязательной покупки внешнего API key: локальная модель может подключаться через Ollama-compatible endpoint, но остается под контролем safety-first pipeline.

Эта версия не является обучением модели с нуля. Цель v1.0 - сделать локальный runtime предсказуемым, ограниченным по ресурсам и безопасным при сбоях.

## Что добавлено

- Лимит длины ответа модели через `SANA_LLM_MAX_OUTPUT_CHARS`.
- Лимит генерации Ollama через `SANA_OLLAMA_NUM_PREDICT`.
- Проверка формата ответа Ollama: payload должен быть JSON object, поле `response` должно быть строкой.
- Закрытие временного HTTP client после локального запроса к Ollama.
- Allowlist для `SANA_OLLAMA_BASE_URL`:
  - по умолчанию разрешены только `localhost`, `127.0.0.1`, `::1`;
  - приватные IP разрешаются только при `SANA_OLLAMA_ALLOW_PRIVATE_NETWORK=true`;
  - публичные внешние URL не используются для Ollama provider.
- Smoke gates теперь блокируют небезопасный Ollama URL до сетевого вызова.

## Переменные окружения

```bash
SANA_LLM_ENABLED=true
SANA_LLM_PROVIDER=ollama
SANA_LLM_MODEL=llama3.1:8b
SANA_OLLAMA_BASE_URL=http://127.0.0.1:11434
SANA_LLM_TIMEOUT_SECONDS=10
SANA_LLM_MAX_OUTPUT_CHARS=1200
SANA_OLLAMA_NUM_PREDICT=384
```

Для осознанного подключения Ollama на другом сервере в приватной сети:

```bash
SANA_OLLAMA_ALLOW_PRIVATE_NETWORK=true
SANA_OLLAMA_BASE_URL=http://192.168.1.10:11434
```

Этот режим нельзя включать случайно: он нужен только когда инфраструктура уже контролируется нами.

## Safety contract

Локальная модель используется только для взрослых пользователей и только в режимах `support` и `deep_support`.

S.A.N.A. не отправляет в LLM:

- несовершеннолетних пользователей;
- crisis и emergency сценарии;
- high-risk сценарии;
- immediate danger сценарии.

Если локальная модель не отвечает, возвращает пустой текст, возвращает кривой JSON или нарушает правила безопасности/качества, система возвращается к deterministic support response.

## Почему это важно

Текущий сервер подходит для разработки и запуска небольших локальных моделей, но не для обучения большой модели с нуля. Поэтому v1.0 усиливает контролируемый запуск inference: меньше риска зависаний, лишнего расхода CPU/RAM, случайной отправки prompt на внешний endpoint и непредсказуемых ответов.

## Следующие шаги

1. Preflight-проверка Ollama endpoint и наличия модели до генерации.
2. Более точная таксономия ошибок provider: timeout, model missing, invalid JSON, HTTP error.
3. Streaming позже, только после safety strategy для частичных ответов.
4. Локальный RAG по проверенным материалам психологической поддержки.
5. Подготовка датасета для будущего LoRA/QLoRA fine-tuning на отдельной более мощной машине.
