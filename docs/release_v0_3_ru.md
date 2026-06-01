# Release readiness S.A.N.A. v0.3

Статус: dataset + evaluation foundation release candidate.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.3.
- Data strategy.
- Evaluation plan.
- JSON fixture с v0.3 evaluation scenarios.
- Evaluation runner без внешних моделей.
- `make evaluate` как отдельный evaluation gate.
- Проверка схемы на базовые raw identifiers: email, URL, username, phone-like strings.
- Метрики: `total`, `passed`, `failed`, `pass_rate`, `failures_by_issue`, `failures_by_tag`.

## Не входит

- Реальные пользовательские данные.
- Training dataset для fine-tuning.
- LLM-as-judge.
- Автоматическая клиническая оценка.
- RAG или локализованный resource recommender.

## Release Gate

Перед переходом дальше должны проходить:

```bash
make check
make evaluate
```

## Known Limitations

- Evaluation dataset пока маленький и synthetic-only.
- Схема PII/PHI защиты минимальная и не заменяет полноценный de-identification pipeline.
- Нет JSONL-разделения на core/red-team/minor-safety наборы; это P1.
- Нет human reviewer approval workflow; это P1/P2.

