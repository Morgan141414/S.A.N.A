# S.A.N.A. v1.5 Release Readiness

## Статус

v1.5 готова, если user-local Ollama tooling добавлен, документирован и не запускается автоматически в quality gates.

## Область версии

- User-local Ollama install script.
- User-local Ollama serve script.
- Ollama model pull script.
- Gated local smoke wrapper.
- Make targets for manual runtime workflow.
- Documentation for non-sudo runtime path.

## Проверки

Перед релизом должны проходить:

```bash
make dev-cycle
make evaluate
make evaluate-readiness
```

`make llm-smoke` без ручных gate-флагов должен завершаться кодом `2`.

## Blocking Conditions

v1.5 не готова, если:

- Ollama install запускается внутри `make dev-cycle`;
- model pull запускается автоматически;
- smoke может использовать реальные пользовательские данные;
- scripts требуют `sudo`;
- scripts отключают safety/preflight/fallback;
- docs обещают production readiness после smoke.

## Известные ограничения

- Ollama пока не установлен автоматически.
- Модель пока не скачана автоматически.
- User-local server нужно запускать вручную в отдельной сессии.
- GPU может быть занят другими процессами, поэтому первый smoke может быть медленным.
