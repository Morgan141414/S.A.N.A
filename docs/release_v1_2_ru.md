# S.A.N.A. v1.2 Release Readiness

## Статус

v1.2 готова, если локальные provider failures имеют понятный `blocked_reason` и не раскрывают сырые исключения пользователю.

## Область версии

- `LLMProviderError`.
- Categorized generation failures for Ollama provider.
- Categorized preflight timeout.
- Guarded response preserves safe provider error reason.
- Automated tests cover timeout, HTTP error, connection error, invalid JSON and malformed payload.

## Проверки

Перед релизом должны проходить:

```bash
make dev-cycle
make evaluate
make evaluate-readiness
```

`make llm-smoke` без ручных gate-флагов должен завершаться кодом `2`.

## Blocking Conditions

v1.2 не готова, если:

- provider exception может попасть в user-facing response;
- provider failure не приводит к deterministic fallback;
- categorized reason теряется в guarded response;
- тесты требуют реальную Ollama;
- crisis, emergency или minors начинают вызывать provider;
- smoke может запуститься без manual gates.

## Известные ограничения

- Error taxonomy пока используется в `blocked_reason`, но еще не агрегируется в smoke report summary.
- Provider retry/circuit breaker пока не реализованы.
- Streaming остается отключенным.
