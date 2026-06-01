# Техническое задание S.A.N.A. v0.7

Статус: implementation slice for OpenAI Provider Skeleton.

Дата среза: 2026-06-01.

Этот документ описывает слой v0.7 поверх v0.6 LLM Contract Layer. v0.6 добавила `LLMProvider`, `MockLLMProvider`, prompt policy и guarded response path без подключения реальной LLM. v0.7 добавляет минимальный OpenAI provider skeleton: env settings, disabled-by-default режим, отсутствие secrets в коде, fallback при ошибках/таймаутах provider и тестирование только через mocks.

v0.7 не включает production-подключение реальной модели и не включает OpenAI по умолчанию. OpenAI provider skeleton нужен как адаптер за существующим `LLMProvider`, который можно включить только явной конфигурацией и только после прохождения safety/release gates.

## 1. Цели v0.7

- Описать `OpenAIProvider` skeleton как реализацию существующего `LLMProvider` contract.
- Зафиксировать env-based конфигурацию без secrets в коде, fixtures, docs examples или test artifacts.
- Сделать real provider disabled by default во всех окружениях.
- Сохранить `MockLLMProvider` как обязательный provider для unit, contract и evaluation tests.
- Описать fallback при provider errors, timeouts, malformed responses, empty responses и unsupported configuration.
- Запретить использование real provider для crisis и minors scenarios в v0.7.
- Зафиксировать release gates, которые не позволяют real provider output попасть пользователю без guarded response path.

## 2. Не входит в v0.7

- Включение OpenAI provider по умолчанию.
- Хранение API keys, organization ids, project ids или других secrets в коде.
- Подключение реальной LLM к crisis, high/emergency или minors flows.
- Изменение risk classifier, crisis protocol, safety checker или baseline evaluation logic.
- Замена `MockLLMProvider` реальным provider в automated tests.
- Streaming, tool calling, vision, embeddings, RAG или memory layer.
- Fine-tuning, model routing, cost dashboard или billing automation.
- Clinical validation качества реальной модели.
- Production rollout, canary traffic или reviewer UI.

## 3. Основной принцип v0.7

OpenAI provider может существовать только как выключенный по умолчанию adapter за v0.6 `LLMProvider`.

```text
configured provider
  -> LLMProvider contract
  -> guarded response path
  -> safety wrapper
  -> fallback decision
  -> final response
```

Если OpenAI provider не настроен, выключен, вернул ошибку, превысил timeout или дал unsafe output, S.A.N.A. должна использовать существующий fallback. Для пользователя это не должно выглядеть как технический сбой, особенно в high/emergency контексте.

## 4. Термины

`OpenAIProvider` - skeleton provider adapter, который реализует `LLMProvider` и преобразует `LLMRequest` в запрос к OpenAI API только при явном включении.

`provider enabled flag` - env setting, который разрешает использование real provider. По умолчанию значение должно быть equivalent to disabled.

`provider configuration` - набор env settings для model id, timeout, base URL при необходимости и прочих не-secret параметров.

`secret` - API key, token или credential. Secret нельзя коммитить, логировать, включать в docs examples как реальное значение или сохранять в artifacts.

`real provider path` - execution path, который делает сетевой вызов к OpenAI API.

`mock-only tests` - тесты, которые используют `MockLLMProvider` или test doubles и не требуют network/secrets.

## 5. P0 Scope

P0 - обязательный минимум v0.7. Невыполнение любого P0 пункта блокирует переход от skeleton к runtime use.

### 5.1 OpenAIProvider Skeleton

Минимальный skeleton должен:

- реализовывать существующий `LLMProvider` interface без расширения пользовательского API;
- принимать только `LLMRequest` и возвращать только `LLMResponse`;
- заполнять `provider_name`, `provider_version`, `status`, `latency_ms`, token fields если они доступны, и `raw_error` без secrets;
- маппить provider exceptions в documented statuses из v0.6;
- не менять `risk_level`, `conversation_mode`, `support_protocol` или crisis decision;
- не обходить prompt policy и safety wrapper;
- не иметь hardcoded model response, API key или endpoint secret.

Допустимые статусы для provider failures:

```text
timeout
rate_limited
provider_error
malformed_response
unsafe_response
fallback_used
```

### 5.2 Env Settings

Все параметры real provider должны приходить из environment или безопасного runtime config.

Минимальный набор:

```text
SANA_LLM_ENABLED=false|true
SANA_LLM_PROVIDER=none|openai
SANA_LLM_MODEL=<model_id>
SANA_LLM_TIMEOUT_SECONDS=<positive_number>
SANA_OPENAI_API_KEY=<secret_from_environment>
```

Правила:

- default provider должен быть `none` или internal fallback, не `openai`;
- `SANA_LLM_ENABLED` по умолчанию считается `false`;
- отсутствие `SANA_OPENAI_API_KEY` не должно ломать приложение и должно вести к provider-disabled/fallback path;
- secrets нельзя логировать, включать в reports или возвращать через API;
- docs examples должны использовать placeholder вроде `<set-in-environment>`, а не реальный ключ;
- конфигурация должна быть валидирована до первого real provider call.

### 5.3 Disabled By Default

Real provider path не должен выполняться, если явно не выполнены все условия:

```text
SANA_LLM_ENABLED=true
SANA_LLM_PROVIDER=openai
SANA_OPENAI_API_KEY is present
SANA_LLM_MODEL is present
scenario is not crisis/high/emergency/minor-disabled
```

Если хотя бы одно условие не выполнено, используется mock/fallback path без сетевого вызова.

### 5.4 Fallback On Provider Errors And Timeouts

Fallback обязателен для:

- OpenAI provider disabled;
- missing or invalid env settings;
- missing API key;
- timeout;
- rate limit;
- network error;
- provider API error;
- malformed response;
- empty response;
- unexpected finish reason;
- unsafe response после safety wrapper;
- crisis/high/emergency scenario;
- minors scenario.

Fallback должен быть совместим с v0.6 categories:

```text
low_support_fallback
medium_support_fallback
high_risk_fallback
emergency_fallback
provider_error_fallback
```

Provider error не должен раскрывать пользователю внутренние детали, model id, endpoint, key status или stack trace.

### 5.5 Tests Use Mocks

Automated tests v0.7 должны использовать только mocks/test doubles.

Минимальные требования:

- unit tests не делают network calls;
- contract tests используют `MockLLMProvider`;
- OpenAI provider tests mock the OpenAI client/API boundary;
- tests проходят без `SANA_OPENAI_API_KEY`;
- CI не требует secrets;
- failure cases покрывают timeout, rate limit, malformed response, empty response и provider error;
- safety wrapper/fallback tests проверяют итоговый response, а не качество реальной модели.

Реальный provider call допустим только в отдельном manual smoke script или future gated workflow, который не является частью default test suite.

### 5.6 Crisis And Minors Disabled

В v0.7 OpenAI provider skeleton не должен использоваться для:

- `risk_level=high`;
- `risk_level=emergency`;
- minors scenarios;
- abuse/exploitation scenarios involving minors;
- immediate danger or active self-harm;
- cases where locale-specific emergency resources are required but not validated.

Для этих сценариев real provider path должен быть bypassed, а итоговый ответ должен идти через existing crisis/minors-safe fallback or deterministic guarded path.

### 5.7 Artifacts

Будущая реализация v0.7 должна добавлять к readiness package:

```text
openai_provider_config_report.md
openai_provider_contract_report.json
provider_fallback_report.json
```

Минимальные поля:

```text
run_id
provider_name
provider_enabled
provider_selected
model_configured
api_key_present_boolean_only
network_calls_allowed
mock_tests_used
timeout_ms
fallback_count
provider_error_count
crisis_provider_bypass_count
minors_provider_bypass_count
secrets_detected
blocking_failures
known_limitations
```

`api_key_present_boolean_only` означает только true/false без значения, префикса, suffix или fingerprint.

## 6. P1 Scope

P1 - полезные расширения после P0:

- allowlist поддерживаемых OpenAI model ids;
- configurable max output tokens;
- provider capability matrix;
- manual smoke test с явным локальным opt-in;
- redaction checks для prompt/report artifacts;
- cost/latency budget report без billing secrets;
- provider version changelog;
- canary design для будущего controlled rollout.

## 7. Release Gates v0.7

Документационный слой v0.7 считается готовым, если:

```text
docs/v0_7_spec_ru.md exists
docs/release_v0_7_ru.md exists
docs/technical_spec_ru.md references v0.7
OpenAI provider skeleton documented
env settings documented
disabled-by-default behavior documented
no-secrets rule documented
fallback on provider errors/timeouts documented
tests-use-mocks rule documented
crisis/minors disabled documented
scope and non-scope documented
```

Будущая implementation slice не может считаться ready, если:

- OpenAI provider включается по умолчанию;
- automated tests требуют real API key или network;
- secret попадает в код, лог, report или docs example;
- provider error может попасть пользователю как stack trace/technical leak;
- timeout/rate limit/provider error не ведет к fallback;
- real provider используется для high/emergency или minors scenarios;
- real provider output может миновать safety wrapper;
- readiness package не содержит provider config/contract/fallback evidence.

## 8. Readiness Decision

Для v0.7 documentation layer допустимое решение `ready`, если созданы документы v0.7 и общая technical spec ссылается на них.

Для будущей implementation slice допустимые решения:

```text
ready
ready_with_accepted_risk
not_ready
```

`ready` допустимо только если provider disabled-by-default, secrets отсутствуют в repository/artifacts, mock-only tests проходят, fallback покрывает provider failures, crisis/minors bypass подтвержден, а baseline diff не показывает P0 regressions.

`ready_with_accepted_risk` не допускается для secret exposure, missing fallback, direct unsafe output, real provider in crisis/minors flows или tests requiring secrets.

`not_ready` обязательно при любом нарушении no-secrets, disabled-by-default, mock-only tests, guarded response path или crisis/minors disabled rules.

## 9. Known Limitations

- v0.7 описывает skeleton, но не доказывает качество OpenAI model output.
- v0.7 не включает real provider в default runtime.
- v0.7 не разрешает crisis/minors generation через real provider.
- Mock tests проверяют contract/fallback, а не терапевтическое качество модели.
- Clinical/safety review остается обязательным перед любым расширением real provider scope.

## 10. Следующий шаг после v0.7

Следующий implementation slice может реализовать `OpenAIProvider` skeleton за env flag, сохранив default mock/fallback behavior, mock-only tests и запрет real provider для crisis/minors scenarios. Любой runtime rollout должен быть отдельным release decision с explicit owner, baseline diff и manual safety review.
