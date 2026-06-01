# Release readiness S.A.N.A. v0.6

Статус: implementation-slice release candidate for LLM Contract Layer.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.6: `docs/v0_6_spec_ru.md`.
- Backend `LLMProvider` interface contract.
- Backend `MockLLMProvider` для deterministic tests.
- Prompt policy v0.6 builder.
- Guarded response wrapper для проверки LLM output до показа пользователю.
- Fallback behavior для unsafe/low-quality output.
- API и evaluation runner используют один guarded response path.
- Artifacts для будущего LLM contract report.
- Release gates для будущей реализации LLM layer.
- Явное разделение documentation layer, mock contract и real provider integration.

## Что не входит

- Реальное подключение LLM API или локальной модели.
- Secrets, billing, credentials или provider accounts.
- Fine-tuning, RAG, embeddings или memory layer.
- LLM-as-judge для release decision.
- Clinical validation реальной генерации.

## Release Gate

v0.6 implementation slice считается готовой, если:

```text
docs/v0_6_spec_ru.md exists
docs/release_v0_6_ru.md exists
docs/technical_spec_ru.md references v0.6
LLMProvider interface implemented
mock provider implemented
prompt policy builder implemented
safety wrapper implemented
fallback behavior tested
API contract unchanged by default
release gates documented
non-scope documented
```

Для будущего implementation slice, который использует v0.6 процесс, минимальный gate:

```text
mock provider contract tests pass
prompt_policy_version present
safety wrapper checks every provider response
fallback exists for timeout/provider_error/malformed/unsafe output
no unsafe LLM output reaches user directly
high/emergency scenarios pass crisis safety checks
llm_contract_report generated
baseline diff generated against approved baseline
readiness decision signed by owner/reviewer
```

## Readiness Decision Template

```text
# S.A.N.A. LLM Contract Readiness Decision

Decision: ready | ready_with_accepted_risk | not_ready
Run ID:
Build ID:
Dataset Version:
Baseline ID:
Provider Name:
Provider Version:
Prompt Policy Version:
Date:
Owner:
Reviewer:

LLM Contract Gates Status:
Safety Wrapper Status:
Fallback Status:
Blocking Regressions:
Unsafe Outputs:
Accepted Risks:
Known Limitations:
Follow-up Required:

Decision Rationale:
```

## Blocking Conditions

Release decision must be `not_ready`, если найдено хотя бы одно условие:

- LLMProvider contract не определен или несовместим с documented request/response fields;
- mock provider отсутствует для contract tests;
- prompt policy не имеет версии;
- real provider output может попасть пользователю без safety wrapper;
- fallback отсутствует для timeout, malformed response или unsafe response;
- high/emergency scenario зависит только от LLM output без crisis checks;
- provider может менять risk level или отменять crisis mode;
- response содержит окончательный диагноз, назначение лекарств или unsafe advice;
- hallucinated emergency numbers появились в P0 safety scenario;
- LLM contract report отсутствует в readiness package;
- baseline diff показывает новый P0 blocking regression.

## Accepted Risk Rules

`ready_with_accepted_risk` допустим только если:

- риск не связан с прямым unsafe output в P0 high/emergency scenarios;
- affected provider, scenario id или prompt policy scope явно указан;
- owner указан;
- rationale указан;
- follow-up action указан;
- accepted risk ограничен конкретным release candidate или сроком.

Accepted risk не должен использоваться для обхода safety wrapper, fallback или crisis checks.

## Known Limitations

- v0.6 не подключает реальную LLM.
- v0.6 не измеряет качество реальной модели.
- v0.6 не добавляет reviewer UI.
- v0.6 не заменяет v0.5 baseline diff/readiness, а расширяет его для будущего LLM layer.
- Mock provider проверяет контракт и fallback paths, но не является evidence of therapeutic quality.

## Decision

Документационный слой v0.6 готов к использованию как release/process specification после появления:

- `docs/v0_6_spec_ru.md`;
- `docs/release_v0_6_ru.md`;
- ссылки на v0.6 в `docs/technical_spec_ru.md`.

Итоговый статус для текущего implementation slice: `ready`, если `make dev-cycle`, `make evaluate` и `make evaluate-readiness` проходят без failures.
