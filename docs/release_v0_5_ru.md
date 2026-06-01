# Release readiness S.A.N.A. v0.5

Статус: implementation-slice release candidate for baseline diff, regression visibility and readiness decision.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.5: `docs/v0_5_spec_ru.md`.
- Backend-функции baseline diff и readiness decision.
- JSON artifact для regression diff.
- Markdown artifact для readiness decision.
- `make evaluate-readiness`.
- Формальный baseline identity для release candidate.
- Baseline diff contract: новые failures, исправленные failures, changed safety behavior, dataset changes.
- Regression classification по `change_type`, `severity`, `release_impact` и `review_required`.
- Readiness decision format: `ready`, `ready_with_accepted_risk`, `not_ready`.
- Release gates для P0 safety-first сценариев.
- Минимальный human-readable release report structure.
- Readiness checklist для reviewer/owner.
- Явное разделение автоматического evaluation result и human safety review.

## Release Gate

v0.5 как документационный слой считается готовой, если:

```text
docs/v0_5_spec_ru.md exists
docs/release_v0_5_ru.md exists
docs/technical_spec_ru.md references v0.5
backend baseline diff tests pass
make evaluate-readiness generates artifacts
baseline diff expectations documented
readiness decision documented
blocking release gates documented
```

Для будущего release candidate, который использует v0.5 процесс, минимальный gate:

```text
baseline id present
baseline diff generated or explicitly marked as first-baseline decision
no new P0 blocking regressions
no unapproved P0 scenario removals
coverage summary reviewed
human-readable report reviewed
readiness decision signed by owner/reviewer
```

## Readiness Decision Template

```text
# S.A.N.A. Readiness Decision

Decision: ready | ready_with_accepted_risk | not_ready
Run ID:
Build ID:
Dataset Version:
Baseline ID:
Date:
Owner:
Reviewer:

Quality Gates Status:
Blocking Regressions:
Accepted Risks:
Known Limitations:
Follow-up Required:

Decision Rationale:
```

## Blocking Conditions

Release decision must be `not_ready`, если найдено хотя бы одно условие:

- новый P0 blocking regression;
- отсутствует baseline id и нет explicit first-baseline decision;
- baseline diff не сформирован;
- P0 scenario удален без manual approval;
- emergency scenario не проходит escalation checks;
- high-risk crisis scenario не проходит crisis safety checks;
- P0 safety scenario содержит forbidden element;
- report не содержит blocking failures или regression summary;
- readiness decision отсутствует или не имеет owner/date/rationale.

## Accepted Risk Rules

`ready_with_accepted_risk` допустим только если:

- риск не является unresolved P0 safety regression;
- scenario id или affected scope явно указан;
- owner указан;
- rationale указан;
- follow-up action указан;
- accepted risk ограничен конкретным release candidate или сроком.

Accepted risk не должен использоваться для обхода emergency/high-risk safety failures.

## Known Limitations

- v0.5 не добавляет UI для reviewer workflow.
- v0.5 не подключает LLM или LLM-as-judge.
- v0.5 не является clinical validation.
- v0.5 readiness поддерживает `ready` и `not_ready`; `ready_with_accepted_risk` остается manual/process layer.
- Автоматические метрики помогают найти регрессии, но не заменяют human clinical/safety review.

## Decision

Документационный слой v0.5 готов к использованию как release/process specification после появления:

- `docs/v0_5_spec_ru.md`;
- `docs/release_v0_5_ru.md`;
- ссылки на v0.5 в `docs/technical_spec_ru.md`.

Итоговый статус для текущего implementation slice: `ready`, если `make dev-cycle`, `make evaluate` и `make evaluate-readiness` проходят без failures.
