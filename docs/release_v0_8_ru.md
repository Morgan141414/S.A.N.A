# Release readiness S.A.N.A. v0.8

Статус: implementation-slice release candidate for Controlled Provider Smoke and LLM Evaluation Harness.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.8: `docs/v0_8_spec_ru.md`.
- Manual-only controlled provider smoke для OpenAI provider skeleton.
- LLM evaluation harness для synthetic prompts.
- JSON и Markdown report requirements.
- Env gates для ручного smoke и явного network allow.
- Synthetic-only правило без real user data.
- Запрет crisis/high/emergency/minors scenarios для real provider smoke.
- Явное исключение smoke/evaluation из `make dev-cycle`, default tests и default CI.
- Readiness gates для controlled manual smoke.

## Что не входит

- Включение OpenAI provider по умолчанию.
- Production traffic, canary rollout или real-user generation.
- Реальные пользовательские сообщения, logs, transcripts или production-derived prompts.
- Автоматический real provider smoke в dev-cycle или CI.
- Real provider для crisis, high, emergency или minors flows.
- Clinical validation качества реальной модели.
- LLM-as-judge как обязательный или единственный release gate.

## Release Gate

v0.8 implementation slice считается готовой, если:

```text
docs/v0_8_spec_ru.md exists
docs/release_v0_8_ru.md exists
docs/technical_spec_ru.md references v0.8
manual-only provider smoke documented
synthetic-only prompts documented
no real user data rule documented
JSON/Markdown reports documented
env gates documented
not part of dev-cycle documented
crisis/minors excluded documented
manual smoke runner implemented
manual smoke tests pass without API key
make llm-smoke is gated and manual-only
readiness gates documented
non-scope documented
```

Для будущей implementation slice минимальный gate:

```text
OpenAI provider remains disabled by default
manual smoke requires explicit env gates
manual smoke requires explicit network allow
default dev-cycle remains mock/fallback-only
automated tests pass without API key
synthetic prompt set is reviewed
no real user data detected
crisis/high/emergency scenarios bypass real provider
minors scenarios bypass real provider
provider output passes guarded response path
safety wrapper cannot be bypassed
fallback works for provider error/timeout/malformed/unsafe output
JSON report generated
Markdown report generated
reports contain no secrets
human reviewer assigned
readiness decision recorded
```

## Readiness Decision Template

```text
# S.A.N.A. Controlled Provider Smoke Readiness Decision

Decision: ready | ready_with_accepted_risk | not_ready
Run ID:
Run Type:
Run Mode:
Build ID:
Dataset Version:
Prompt Set ID:
Provider Name:
Provider Enabled:
Provider Selected:
Model Configured:
Network Calls Allowed:
Synthetic Only:
Real User Data Detected:
Prompt Policy Version:
Date:
Operator:
Reviewer:

Env Gates Status:
Synthetic Prompt Status:
Crisis Exclusion Status:
Minors Exclusion Status:
Dev-Cycle Exclusion Status:
Guarded Response Path Status:
Safety Wrapper Status:
Fallback Status:
JSON Report Status:
Markdown Report Status:
No-Secrets Status:
Blocking Failures:
Provider Errors:
Timeouts:
Accepted Risks:
Known Limitations:
Follow-up Required:

Decision Rationale:
```

## Blocking Conditions

Release decision must be `not_ready`, если найдено хотя бы одно условие:

- real provider может быть вызван без `SANA_PROVIDER_SMOKE_ENABLED=true`;
- network call возможен без `SANA_PROVIDER_SMOKE_ALLOW_NETWORK=true`;
- smoke/evaluation запускается через `make dev-cycle`;
- default tests или CI требуют `SANA_OPENAI_API_KEY`;
- prompt set содержит real user data или production-derived content;
- prompt set содержит raw identifiers;
- crisis/high/emergency scenario reaches real provider;
- minors scenario reaches real provider;
- provider output может миновать guarded response path;
- safety wrapper может быть отключен для smoke result;
- provider error, timeout, malformed response или unsafe response не ведет к fallback/blocking evidence;
- raw provider error показывается user-facing output;
- report содержит API key, credential, stack trace с secret или raw sensitive payload;
- JSON или Markdown report отсутствует;
- human review decision отсутствует.

## Accepted Risk Rules

`ready_with_accepted_risk` допустим только если:

- риск не связан с secrets exposure;
- риск не связан с real user data;
- риск не связан с crisis/high/emergency/minors provider call;
- риск не связан с обходом safety wrapper или guarded response path;
- affected prompt id, report field или smoke configuration явно указан;
- owner указан;
- reviewer указан;
- rationale указан;
- follow-up action указан;
- accepted risk ограничен конкретным manual run.

Accepted risk не должен использоваться для обхода manual-only, synthetic-only, no-secrets, not-in-dev-cycle, fallback или crisis/minors exclusion gates.

## Known Limitations

- v0.8 не включает provider в default runtime.
- v0.8 не добавляет backend/scripts реализацию в текущем documentation slice.
- v0.8 не оценивает клиническую эффективность модели.
- v0.8 не разрешает real provider для crisis/minors scenarios.
- Synthetic smoke дает readiness evidence, но не является production validation.
- LLM-as-judge, если будет добавлен позже, остается вспомогательным сигналом.

## Decision

Implementation slice v0.8 готов, если появились:

- `docs/v0_8_spec_ru.md`;
- `docs/release_v0_8_ru.md`;
- ссылка на v0.8 в `docs/technical_spec_ru.md`;
- manual smoke runner;
- JSON/Markdown report writers;
- tests for env gates and synthetic smoke.

Итоговый статус для текущего implementation slice: `ready`, если `make dev-cycle`, `make evaluate`, `make evaluate-readiness` проходят без failures, а `make llm-smoke` без env gates безопасно блокируется без network call.
