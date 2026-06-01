# S.A.N.A. v1.1 Release Readiness

## Статус

v1.1 готова, если локальный smoke не запускает генерацию при недоступной Ollama или отсутствующей модели.

## Область версии

- Preflight для Ollama-compatible provider.
- Проверка `/api/tags`.
- Блокировка manual smoke до генерации при ошибке preflight.
- Тесты без реального network call.
- Документация причин блокировки.

## Проверки

Перед релизом должны проходить:

```bash
make dev-cycle
make evaluate
make evaluate-readiness
```

`make llm-smoke` без ручных gate-флагов по-прежнему должен завершаться кодом `2`.

## Blocking Conditions

v1.1 не готова, если:

- smoke может вызвать генерацию до preflight;
- отсутствующая модель не блокирует smoke;
- недоступный endpoint не блокирует smoke;
- preflight требует реальную Ollama в automated tests;
- preflight обходит существующие smoke gates;
- preflight ослабляет crisis/minor exclusion.

## Известные ограничения

- Preflight пока проверяет только список моделей через `/api/tags`.
- Подробная диагностика HTTP status, timeout и invalid JSON будет вынесена в следующий этап.
- Preflight не измеряет скорость генерации и не оценивает качество модели.
