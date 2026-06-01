# Release readiness S.A.N.A. v0.4

Статус: quality evidence + evaluation reporting release candidate.

## Что входит

- Coverage metrics в `EvaluationSummary`.
- Расширенный P0 evaluation fixture: 40+ сценариев.
- Метаданные сценариев: `priority`, `source_type`, `case_family`, `review_required`, `max_response_chars`.
- Проверка уникальности scenario id.
- Защита evaluation dataset от raw identifiers.
- Обязательный manual review flag для high, emergency и minor safety cases.
- JSON report writer.
- Markdown report writer.
- `make evaluate-report`.
- `evaluation_reports/.gitkeep`.
- Защита от коммита generated JSON reports через `.gitignore`.

## Release Gate

```bash
make check
make evaluate
make evaluate-report
```

Минимальный критерий готовности:

```text
all tests pass
all evaluation scenarios pass
evaluation report generated
coverage includes low/medium/high/emergency
coverage includes crisis/emergency/minor_safety
```

## Не входит

- LLM.
- Fine-tuning.
- Human reviewer UI.
- Полный dataset governance workflow.
