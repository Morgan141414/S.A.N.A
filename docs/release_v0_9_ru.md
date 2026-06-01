# Release readiness S.A.N.A. v0.9

Статус: implementation-slice release candidate for Local LLM Provider.

Дата среза: 2026-06-01.

## Что входит

- Ollama-compatible local provider.
- `SANA_LLM_PROVIDER=ollama`.
- `SANA_OLLAMA_BASE_URL`.
- Локальный provider без API key.
- Mocked tests без real network.
- Manual smoke через существующий `make llm-smoke`.
- Safety/fallback wrapper остается обязательным.
- Crisis, emergency, minors и unknown age bypass provider path.

## Что не входит

- Покупка или использование OpenAI API key.
- Обучение модели.
- Fine-tuning.
- RAG/memory.
- Production rollout.
- Clinical validation.
- Автоматический запуск local provider в CI/dev-cycle.

## Release Gate

```text
make dev-cycle
make evaluate
make evaluate-readiness
```

Manual local smoke допустим только отдельно:

```bash
SANA_LLM_ENABLED=true \
SANA_LLM_PROVIDER=ollama \
SANA_LLM_MODEL=llama3.1:8b \
SANA_OLLAMA_BASE_URL=http://127.0.0.1:11434 \
SANA_PROVIDER_SMOKE_ENABLED=true \
SANA_PROVIDER_SMOKE_ALLOW_NETWORK=true \
SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA=true \
SANA_PROVIDER_SMOKE_DATASET=synthetic_only \
make llm-smoke
```

## Blocking Conditions

Release decision must be `not_ready`, если:

- local provider требует API key;
- local provider включается по умолчанию;
- automated tests делают real network call;
- provider output минует safety wrapper;
- provider вызывается для crisis/emergency/minors;
- smoke использует real user data;
- reports содержат secrets или чувствительные данные.

## Known Limitations

- RTX 3050 8GB ограничивает размер и качество локальных моделей.
- Local model latency может быть высокой.
- Нет streaming/concurrency/rate-limit слоя.
- v0.9 проверяет provider path, а не терапевтическое качество модели.

## Decision

v0.9 готова, если локальный provider работает через контракт, тесты зеленые, smoke остается manual-only, а safety/fallback gates не ослаблены.
