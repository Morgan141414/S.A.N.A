# Техническое задание S.A.N.A. v0.8

Статус: implementation slice for Controlled Provider Smoke and LLM Evaluation Harness.

Дата среза: 2026-06-01.

Этот документ описывает слой v0.8 поверх v0.7 OpenAI Provider Skeleton. v0.7 добавила выключенный по умолчанию provider adapter за `LLMProvider`. v0.8 не включает provider в обычный runtime: она добавляет ручной controlled provider smoke и LLM evaluation harness на синтетических prompts.

v0.8 существует, чтобы безопасно проверить, что provider path может быть вызван в строго ограниченном ручном режиме, а результаты можно оценить и сохранить как JSON/Markdown evidence. Реальные пользовательские данные, crisis/minors сценарии и default dev-cycle остаются вне scope.

## 1. Цели v0.8

- Описать manual-only controlled provider smoke для OpenAI provider skeleton.
- Зафиксировать LLM evaluation harness для синтетических prompts без real user data.
- Требовать JSON и Markdown reports для каждого smoke/evaluation run.
- Ввести env gates, которые явно отделяют manual smoke от default runtime, CI и dev-cycle.
- Подтвердить, что smoke/evaluation не запускаются через `make dev-cycle` и не являются release shortcut.
- Исключить crisis, high, emergency и minors scenarios из real provider smoke.
- Зафиксировать readiness gates для перехода от skeleton к ограниченной ручной проверке.

## 2. Не входит в v0.8

- Включение OpenAI provider по умолчанию.
- Production traffic, canary rollout или real-user generation.
- Использование реальных пользовательских сообщений, logs, transcripts или support cases.
- Автоматический запуск real provider smoke в CI, pre-commit, default test suite или `make dev-cycle`.
- Подключение real provider к crisis, high, emergency или minors flows.
- Clinical validation, diagnosis quality claims или medical safety approval.
- LLM-as-judge как единственный release gate.
- Обновление backend/scripts в рамках этого documentation slice.
- Включение smoke в `make dev-cycle`, `make evaluate` или default CI.
- Streaming, tools, RAG, embeddings, memory, fine-tuning или model routing.

## 3. Основной принцип v0.8

Real provider smoke допустим только как ручной, явно включенный, одноразовый evaluation path:

```text
manual operator
  -> env gates
  -> synthetic prompt set
  -> LLMProvider contract
  -> guarded response path
  -> safety/readiness checks
  -> JSON/Markdown reports
  -> human review decision
```

Если отсутствует любой env gate, prompt set содержит запрещенный сценарий, обнаружены реальные пользовательские данные или provider пытается обойти guarded response path, smoke/evaluation должен завершиться как blocked без real provider call.

## 4. Термины

`controlled provider smoke` - короткая ручная проверка real provider path на заранее утвержденном синтетическом наборе prompts.

`LLM evaluation harness` - future/manual evaluation runner, который вызывает provider через существующий `LLMProvider` contract, применяет safety/readiness checks и сохраняет evidence reports.

`synthetic prompt` - искусственно созданный prompt без реальных пользовательских данных, identifiers, transcripts или production-derived content.

`manual-only run` - запуск, который требует явных env gates и human operator intent, не вызывается default командами разработки и не запускается автоматически в CI.

`readiness gate` - проверка, которая может разрешить или заблокировать ручной smoke/evaluation run и итоговый release decision.

## 5. P0 Scope

P0 - обязательный минимум v0.8. Невыполнение любого P0 пункта блокирует controlled provider smoke.

### 5.1 Manual-Only Provider Smoke

Controlled provider smoke должен:

- запускаться только вручную;
- требовать отдельный explicit smoke flag;
- использовать только synthetic prompts;
- иметь малый фиксированный prompt set;
- вызывать provider только через `LLMProvider` contract;
- сохранять provider disabled-by-default вне smoke run;
- проходить через prompt policy, guarded response path, safety wrapper и fallback logic;
- завершаться blocked при отсутствии любого required env gate;
- не раскрывать пользователю или report raw provider errors, secrets, endpoint internals или stack traces.

Минимальные env gates:

```text
SANA_LLM_ENABLED=true
SANA_LLM_PROVIDER=openai
SANA_LLM_MODEL=<model_id>
SANA_OPENAI_API_KEY=<secret_from_environment>
SANA_PROVIDER_SMOKE_ENABLED=true
SANA_PROVIDER_SMOKE_ALLOW_NETWORK=true
SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA=true
SANA_PROVIDER_SMOKE_DATASET=synthetic_only
```

Default values должны быть equivalent to disabled/blocked. Отсутствие любого gate должно вести к no-network blocked result.

### 5.2 Synthetic Prompts Only

Prompt set для v0.8 smoke/evaluation должен содержать только synthetic prompts.

Запрещено использовать:

- реальные пользовательские сообщения;
- production logs;
- support transcripts;
- analytics events;
- raw identifiers;
- email, phone, address, username или account data;
- prompt fragments, скопированные из реальных обращений;
- crisis/high/emergency/minors prompts для real provider call.

Каждый prompt должен иметь metadata:

```text
id
dataset_version
source_type=synthetic
case_family
locale
expected_risk_level
expected_conversation_mode
expected_support_protocol
provider_call_allowed
exclusion_reason
```

Для v0.8 `provider_call_allowed=true` допустим только для low/medium non-minor support scenarios.

### 5.3 Crisis And Minors Excluded

Real provider path в v0.8 smoke/evaluation запрещен для:

- `risk_level=high`;
- `risk_level=emergency`;
- crisis mode;
- emergency mode;
- minors scenarios;
- abuse, exploitation, grooming or unsafe family scenarios involving minors;
- immediate danger, active self-harm or threat-to-others scenarios.

Такие сценарии могут присутствовать только в deterministic/mock evaluation как bypass evidence. Если они попадают в real provider smoke set, запуск должен завершиться blocked до network call.

### 5.4 LLM Evaluation Harness

LLM evaluation harness должен оценивать не "терапевтическое качество модели вообще", а controlled readiness evidence:

- provider call was gated correctly;
- no real user data was used;
- excluded scenarios were bypassed;
- response passed safety wrapper;
- fallback worked on provider errors/timeouts;
- report artifacts were generated;
- no secrets appeared in logs or reports;
- human review decision exists for any manual smoke result.

Минимальные automated checks:

```text
env_gates_valid
synthetic_only
no_real_user_data_detected
crisis_excluded
minors_excluded
network_allowed_only_for_manual_smoke
guarded_response_path_used
safety_wrapper_passed
fallback_verified
reports_generated
secrets_absent
human_review_required
```

LLM-as-judge может быть добавлен только как P1 assistive signal и не может заменять deterministic safety/readiness gates.

### 5.5 Reports

Каждый manual smoke/evaluation run должен создавать JSON и Markdown report.

Минимальные artifacts:

```text
provider_smoke_report.json
provider_smoke_report.md
llm_evaluation_report.json
llm_evaluation_report.md
```

Минимальные поля JSON:

```text
run_id
run_type
run_mode
timestamp_utc
operator
provider_name
provider_enabled
provider_selected
model_configured
api_key_present_boolean_only
network_calls_allowed
synthetic_only
prompt_set_id
prompt_count
provider_call_count
provider_bypass_count
crisis_excluded_count
minors_excluded_count
fallback_count
provider_error_count
timeout_count
malformed_response_count
unsafe_response_count
guarded_response_path_used
safety_wrapper_passed
secrets_detected
real_user_data_detected
blocking_failures
accepted_risks
known_limitations
readiness_decision
reviewer
```

Markdown report должен быть human-readable summary of the same evidence. Secrets, raw API keys, provider request payloads with sensitive content и stack traces запрещены.

### 5.6 Not Part Of Dev-Cycle

v0.8 smoke/evaluation не должен быть частью:

- `make dev-cycle`;
- default unit tests;
- default contract tests;
- default readiness evaluation;
- CI without explicit manual approval;
- pre-commit hooks;
- local startup path.

Default development loop должен оставаться mock/fallback-only и проходить без `SANA_OPENAI_API_KEY`.

### 5.7 Readiness Gates

Controlled provider smoke считается допустимым только если:

```text
v0.7 provider skeleton remains disabled by default
all required env gates are explicitly enabled
API key is present only in environment
network calls are explicitly allowed for manual smoke
prompt set is synthetic-only
prompt set excludes crisis/high/emergency/minors
guarded response path is enforced
safety wrapper is enforced
fallback behavior is available
JSON and Markdown reports are configured
human reviewer is assigned
run is not part of dev-cycle or default CI
```

Release decision must be `not_ready`, если найдено хотя бы одно условие:

- real provider can run without manual smoke gates;
- real provider runs during `make dev-cycle`;
- prompt set contains real user data;
- crisis/high/emergency/minors prompt reaches real provider;
- provider output bypasses safety wrapper;
- provider error reaches user-facing output raw;
- report contains secrets or raw credentials;
- JSON/Markdown report is missing;
- human review decision is missing;
- fallback is unavailable for provider error, timeout, malformed response or unsafe response.

## 6. P1 Scope

P1 - полезные расширения после P0:

- LLM-as-judge as assistive, non-blocking evaluator with deterministic guardrails.
- Cost and token summary with no prompt payload leakage.
- Multiple model comparison over the same synthetic prompt set.
- Locale coverage expansion for low/medium synthetic support prompts.
- Reviewer UI for comparing guarded response, fallback and provider metadata.
- Signed readiness bundle for manual smoke artifacts.

## 7. Security And Privacy Rules

- Secrets live only in environment or approved secret manager.
- Reports may store only `api_key_present_boolean_only=true|false`.
- Prompt sets must be synthetic-only and reviewed before manual smoke.
- Raw provider payload logging is disabled by default.
- Any accidental real user data detection blocks the run and requires artifact cleanup.
- Provider metadata must not expose credentials, account ids, organization ids or request signatures.

## 8. Compatibility With v0.7

v0.8 does not weaken v0.7:

- OpenAI provider remains disabled by default.
- Mock provider remains required for automated tests.
- Crisis/minors real provider path remains disabled.
- Fallback remains mandatory.
- No-secrets rule remains mandatory.
- Provider cannot change risk level, support protocol or crisis decision.

## 9. Итог

v0.8 добавляет документационный контракт для ограниченной ручной проверки real provider path и LLM evaluation evidence. Она не является production rollout и не разрешает использовать реальные пользовательские данные. Главный результат v0.8 - безопасная рамка, в которой можно получить первые JSON/Markdown evidence reports без ослабления кризисных, privacy и disabled-by-default гарантий.
