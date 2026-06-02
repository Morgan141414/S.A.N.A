# S.A.N.A. v1.3 Release Readiness

## Статус

v1.3 готова, если LLM smoke report содержит агрегированную сводку по candidate/fallback и причинам блокировки.

## Область версии

- Smoke report summary fields.
- Markdown `Blocked Reasons` section.
- Tests for success and fallback reports.
- No changes to crisis/minor/provider safety boundaries.

## Проверки

Перед релизом должны проходить:

```bash
make dev-cycle
make evaluate
make evaluate-readiness
```

`make llm-smoke` без ручных gate-флагов должен завершаться кодом `2`.

## Blocking Conditions

v1.3 не готова, если:

- report теряет scenario-level results;
- fallback не считается в summary;
- blocked reasons не агрегируются;
- report раскрывает raw exception или sensitive prompt data;
- smoke может запуститься без manual gates;
- safety/quality checks ослаблены.

## Известные ограничения

- Preflight failures пока печатаются в stderr и не пишутся в JSON report.
- Summary не измеряет latency.
- Summary не сравнивает модели между собой.
