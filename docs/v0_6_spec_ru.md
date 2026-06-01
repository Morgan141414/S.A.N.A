# Техническое задание S.A.N.A. v0.6

Статус: implementation slice for LLM Contract Layer.

Дата среза: 2026-06-01.

Этот документ описывает слой v0.6 поверх v0.5 baseline diff/readiness. v0.5 сделала release candidate reviewable: baseline id, regression diff, readiness decision и release gates. v0.6 подготавливает контрактный слой для будущего подключения LLM: интерфейс провайдера, mock provider, prompt policy, safety wrapper, fallback behavior и release gates.

Текущий implemented slice v0.6 добавляет backend-контракт `LLMProvider`, `MockLLMProvider`, prompt policy builder и guarded response path, но не подключает реальную LLM. Цель v0.6 - заранее определить контракт, по которому LLM можно будет подключить без размывания safety-first поведения S.A.N.A.

## 1. Цели v0.6

- Зафиксировать `LLMProvider` interface как стабильную границу между S.A.N.A. и внешней/локальной моделью.
- Описать mock provider для deterministic evaluation, regression tests и fallback dry-run.
- Ввести prompt policy: что можно передавать модели, какие инструкции обязательны, какие выходные свойства проверяются.
- Описать safety wrapper вокруг LLM response до показа пользователю.
- Зафиксировать fallback behavior при ошибке провайдера, timeout, unsafe output или низкой уверенности.
- Разделить LLM contract tests, safety evaluation и human release review.
- Подготовить release gates для будущей реализации без внесения runtime-изменений в v0.6.

## 2. Не входит в v0.6

- Подключение реального LLM API, локальной модели или routing layer.
- Подключение LLM к production runtime по умолчанию.
- Изменение risk classifier, response generator или safety checker.
- Хранение API keys, secrets, billing или provider credentials.
- Fine-tuning, RAG, embeddings, vector storage или memory layer.
- LLM-as-judge для release decision.
- Использование реальных пользовательских диалогов.
- Автоматическое clinical sign-off или замена human safety review.
- Production observability, tracing dashboard или reviewer UI.

## 3. Основной принцип v0.6

LLM может быть подключена только как ограниченный provider за контрактом S.A.N.A., а не как самостоятельный источник решений о риске, диагнозе или кризисной маршрутизации.

```text
user input
  -> risk/context analysis
  -> prompt policy
  -> LLMProvider
  -> safety wrapper
  -> fallback decision
  -> final response
```

Если LLM output конфликтует с risk classifier, safety checker, crisis protocol или запрещенным поведением, приоритет имеет safety layer. Для high/emergency сценариев fallback должен быть безопаснее и короче, а не "более креативным".

## 4. Термины

`LLMProvider` - интерфейс, через который S.A.N.A. запрашивает кандидатный ответ у модели.

`mock provider` - deterministic provider, который возвращает заранее заданные ответы для тестов, evaluation и contract validation.

`prompt policy` - правила сборки system/developer/user context, ограничений, locale данных и запрещенных инструкций.

`safety wrapper` - слой после LLMProvider, который проверяет response до показа пользователю и может заменить его fallback-ответом.

`fallback response` - безопасный ответ, выбранный без доверия к LLM output, если provider недоступен или ответ небезопасен.

`provider error` - timeout, rate limit, malformed response, empty response, policy violation, network error или unsupported locale.

## 5. P0 Scope

P0 - обязательный минимум v0.6. Невыполнение любого P0 пункта блокирует переход к реализации LLM layer.

### 5.1 LLMProvider Interface

Минимальный контракт:

```text
generate(request: LLMRequest) -> LLMResponse
```

Минимальный `LLMRequest`:

```text
request_id
locale
conversation_mode
risk_level
support_protocol
user_message
conversation_summary
prompt_policy_version
safety_constraints
timeout_ms
metadata
```

Минимальный `LLMResponse`:

```text
request_id
provider_name
provider_version
status
text
finish_reason
latency_ms
input_tokens
output_tokens
safety_notes
raw_error
```

Допустимые `status`:

```text
ok
timeout
rate_limited
provider_error
malformed_response
unsafe_response
fallback_used
```

Provider не должен самостоятельно менять `risk_level`, отменять crisis mode, ставить диагноз или выбирать emergency policy.

### 5.2 Mock Provider

Mock provider должен быть обязательным первым provider для contract tests.

Минимальные требования:

- deterministic output для одинакового `LLMRequest`;
- поддержка success, timeout, malformed response, unsafe response и empty response;
- возможность вернуть scripted response по scenario id или request fixture;
- отсутствие сетевых вызовов;
- отсутствие secrets;
- пригодность для baseline diff и readiness workflow v0.5.

Mock provider нужен не для имитации качества реальной модели, а для проверки границ: request schema, response schema, safety wrapper, fallback и release gates.

### 5.3 Prompt Policy

Prompt policy должна быть версионирована:

```text
prompt_policy_version = v0.6
```

Минимальные правила:

- system instructions всегда содержат роль S.A.N.A. как supportive assistant, а не врача, психолога, психиатра или emergency service;
- high/emergency risk добавляет crisis constraints и короткий формат ответа;
- запрещено просить модель ставить диагноз, назначать лекарства или отменять лечение;
- запрещено просить модель скрывать риски, обходить safety checker или игнорировать risk level;
- locale-specific emergency resources передаются только если они валидированы;
- conversation history передается минимально необходимым summary, без лишних персональных данных;
- prompt должен отделять user content от instructions;
- prompt injection со стороны пользователя не должен менять safety constraints.

### 5.4 Safety Wrapper

Каждый LLM response должен пройти safety wrapper до показа пользователю.

Минимальные проверки:

- нет окончательного диагноза;
- нет назначения или отмены лекарств;
- нет обесценивания, давления, стыда или обвинения;
- нет unsafe advice для self-harm, violence, abuse или emergency;
- нет hallucinated emergency numbers;
- для high/emergency есть проверка физической безопасности и безопасный следующий шаг;
- crisis response не уходит в длинный анализ;
- response соответствует expected locale и conversation mode;
- forbidden elements из evaluation scenarios не появились в output.

Если проверка не пройдена, итоговый ответ должен быть fallback, а artifact должен фиксировать reason.

### 5.5 Fallback Behavior

Fallback обязателен для:

- provider timeout;
- provider unavailable или rate limited;
- malformed/empty response;
- unsafe response;
- policy violation;
- unsupported locale;
- high/emergency scenario, где LLM output не прошел crisis checks.

Минимальные fallback категории:

```text
low_support_fallback
medium_support_fallback
high_risk_fallback
emergency_fallback
provider_error_fallback
```

Fallback не должен выглядеть как техническая ошибка для пользователя в кризисе. Для high/emergency он должен сохранять тепло, краткость, safety check и предложение обратиться к экстренной помощи или доверенному человеку, если есть непосредственная опасность.

### 5.6 Artifacts

Будущая реализация LLM layer должна создавать artifacts, совместимые с v0.5 readiness:

```text
llm_contract_report.json
llm_contract_report.md
fallback_report.json
prompt_policy_report.md
```

Минимальные поля:

```text
run_id
provider_name
provider_version
prompt_policy_version
request_count
success_count
fallback_count
unsafe_response_count
timeout_count
malformed_response_count
blocking_failures
known_limitations
```

## 6. P1 Scope

P1 - важные элементы, которые повышают качество LLM integration, но не являются обязательными для документационного слоя v0.6.

- Provider capability matrix: streaming, locale support, max tokens, timeout, safety mode.
- Structured output schema для safety notes.
- Redaction policy для sensitive context.
- Provider cost/latency budget.
- Multi-provider routing policy.
- Canary evaluation для ограниченного набора сценариев.
- Prompt changelog и diff между prompt policy versions.
- Manual review form для unsafe/fallback cases.

## 7. Release Gates v0.6

Документационный слой v0.6 считается готовым, если:

```text
docs/v0_6_spec_ru.md exists
docs/release_v0_6_ru.md exists
docs/technical_spec_ru.md references v0.6
LLMProvider contract documented
mock provider behavior documented
prompt policy documented
safety wrapper documented
fallback behavior documented
release gates documented
scope and non-scope documented
```

Будущая реализация LLM layer не может считаться ready, если:

- нет mock provider contract tests;
- real provider используется без safety wrapper;
- prompt policy не версионирована;
- fallback отсутствует для provider errors;
- unsafe LLM output может попасть пользователю напрямую;
- high/emergency сценарии проходят только за счет LLM без crisis checks;
- readiness decision не содержит LLM contract report;
- есть новые P0 blocking regressions относительно baseline.

## 8. Readiness Decision

Для v0.6 documentation layer допустимое решение `ready`, если созданы документы v0.6 и общая technical spec ссылается на них.

Для будущей implementation slice допустимые решения остаются совместимыми с v0.5:

```text
ready
ready_with_accepted_risk
not_ready
```

`ready` допустимо только если mock provider tests, safety wrapper tests, fallback tests, evaluation gates и baseline diff проходят без P0 blocking regressions.

`ready_with_accepted_risk` не допускается для unresolved unsafe output в P0 high/emergency scenarios.

`not_ready` обязательно при любом прямом показе unsafe LLM output, отсутствии fallback или отсутствии prompt policy version.

## 9. Known Limitations

- v0.6 фиксирует контракт, но не доказывает качество реальной модели.
- Mock provider не заменяет model evaluation.
- Safety wrapper должен быть реализован и протестирован отдельно.
- Prompt policy может потребовать обновления после выбора конкретного provider.
- Clinical/safety review остается обязательным для high-risk behavior.

## 10. Следующий шаг после v0.6

Следующий implementation slice должен начинаться с mock provider и contract tests, затем подключать safety wrapper и fallback, и только после этого рассматривать real provider adapter.
