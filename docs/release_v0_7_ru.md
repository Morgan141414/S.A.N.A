# Release readiness S.A.N.A. v0.7

Статус: implementation-slice release candidate for OpenAI Provider Skeleton.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.7: `docs/v0_7_spec_ru.md`.
- OpenAI provider skeleton как реализация существующего `LLMProvider`.
- Env settings для выбора provider, model id, timeout и API key через environment.
- Disabled-by-default правило для real provider.
- No-secrets правило для кода, docs examples, logs, reports и tests.
- Fallback behavior при provider errors, timeouts, rate limits, malformed/empty responses и invalid config.
- Mock-only правило для automated tests и CI.
- Явный запрет real provider для crisis/high/emergency и minors scenarios в v0.7.
- Release gates для safe/off-by-default runtime use.

## Что не входит

- Включение OpenAI provider по умолчанию.
- Production traffic, canary rollout или real-user generation.
- Secrets, billing credentials или provider accounts в repository.
- Использование real provider в automated tests.
- Подключение real provider к crisis/minors flows.
- Streaming, tools, RAG, embeddings, memory или fine-tuning.
- Clinical validation реальной генерации.

## Release Gate

v0.7 implementation slice считается готовой, если:

```text
docs/v0_7_spec_ru.md exists
docs/release_v0_7_ru.md exists
docs/technical_spec_ru.md references v0.7
OpenAI provider skeleton documented
env settings documented
disabled-by-default documented
no-secrets rule documented
fallback on provider errors/timeouts documented
tests use mocks documented
crisis/minors disabled documented
OpenAIProvider implements LLMProvider
all automated tests pass without API key
default runtime keeps provider disabled
non-scope documented
```

Для будущей implementation slice минимальный gate:

```text
OpenAIProvider implements LLMProvider
OpenAIProvider disabled by default
default provider remains mock/fallback
all automated tests pass without API key
all automated tests avoid network calls
provider errors and timeouts use fallback
malformed/empty responses use fallback
real provider output always passes safety wrapper
high/emergency scenarios bypass real provider
minors scenarios bypass real provider
no secrets in code/logs/reports/docs examples
provider config report generated
provider fallback report generated
baseline diff generated against approved baseline
readiness decision signed by owner/reviewer
```

## Readiness Decision Template

```text
# S.A.N.A. OpenAI Provider Skeleton Readiness Decision

Decision: ready | ready_with_accepted_risk | not_ready
Run ID:
Build ID:
Dataset Version:
Baseline ID:
Provider Name:
Provider Enabled:
Provider Selected:
Model Configured:
Network Calls Allowed:
Prompt Policy Version:
Date:
Owner:
Reviewer:

Disabled-by-default Status:
No-secrets Status:
Mock-only Tests Status:
Fallback Status:
Crisis Bypass Status:
Minors Bypass Status:
Safety Wrapper Status:
Blocking Regressions:
Provider Errors:
Timeouts:
Accepted Risks:
Known Limitations:
Follow-up Required:

Decision Rationale:
```

## Blocking Conditions

Release decision must be `not_ready`, если найдено хотя бы одно условие:

- OpenAI provider может быть выбран без explicit enable flag;
- default runtime использует `openai` вместо mock/fallback;
- automated tests требуют `SANA_OPENAI_API_KEY`;
- automated tests делают network calls к real provider;
- secret найден в коде, docs examples, logs, reports или artifacts;
- provider error, timeout, malformed response или empty response не ведет к fallback;
- raw provider error показывается пользователю;
- real provider output может миновать guarded response path или safety wrapper;
- real provider используется для `risk_level=high` или `risk_level=emergency`;
- real provider используется для minors scenarios;
- provider может менять risk level, support protocol или crisis decision;
- readiness package не содержит provider config/fallback evidence;
- baseline diff показывает новый P0 blocking regression.

## Accepted Risk Rules

`ready_with_accepted_risk` допустим только если:

- риск не связан с secrets exposure;
- риск не связан с real provider in crisis/minors flows;
- риск не связан с direct unsafe output или bypass safety wrapper;
- affected provider config, scenario id или test scope явно указан;
- owner указан;
- rationale указан;
- follow-up action указан;
- accepted risk ограничен конкретным release candidate или сроком.

Accepted risk не должен использоваться для обхода disabled-by-default, no-secrets, fallback, mock-only tests или crisis/minors bypass.

## Known Limitations

- v0.7 не подключает реальную LLM к default runtime.
- v0.7 не оценивает терапевтическое качество OpenAI model output.
- v0.7 не разрешает real provider для crisis/minors scenarios.
- v0.7 не заменяет v0.6 guarded response path и fallback behavior.
- Mock-only tests подтверждают contract и failure handling, но не качество реальной генерации.

## Decision

Implementation slice v0.7 готов к использованию как safe/off-by-default provider skeleton после появления:

- `docs/v0_7_spec_ru.md`;
- `docs/release_v0_7_ru.md`;
- ссылки на v0.7 в `docs/technical_spec_ru.md`;
- backend settings/provider/tests;
- зеленых `make dev-cycle`, `make evaluate`, `make evaluate-readiness`.

Итоговый статус для текущего implementation slice: `ready`, если OpenAI provider остается disabled-by-default, automated tests не требуют API key, API schema не расширяется provider metadata, а safety/fallback gates проходят.
