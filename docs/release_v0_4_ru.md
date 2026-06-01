# Release readiness S.A.N.A. v0.4

Статус: quality evidence + evaluation reporting release candidate.

## Что входит

- Coverage metrics в `EvaluationSummary`.
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

## Не входит

- LLM.
- Fine-tuning.
- Human reviewer UI.
- Полный dataset governance workflow.
