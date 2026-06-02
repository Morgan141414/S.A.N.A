# Data Strategy S.A.N.A.

## Назначение

Этот документ описывает безопасную стратегию данных для будущей оценки и обучения S.A.N.A.

## Источники данных v0.3

В v0.3 разрешены только:

- синтетические сценарии, созданные командой;
- red-team сценарии для проверки риска и safety;
- публичные guidelines и шкалы только как reference material, без копирования защищенных материалов в датасет;
- экспертные правки синтетических примеров.

В v0.3 не используются реальные пользовательские переписки.

## Запрещенные данные

- личные переписки без явного согласия;
- данные несовершеннолетних;
- медицинские документы пользователей;
- приватные истории из форумов как training data;
- любые данные, где невозможно удалить персональные признаки.

## Schema сценария

```text
id
message
age
locale
expected_risk_level
expected_conversation_mode
expected_support_protocol
required_phrases
forbidden_phrases
tags
```

## Clinician/expert review queue

Очередь экспертной проверки нужна до fine-tuning/deep learning, чтобы будущий датасет не состоял из непроверенных ответов модели.

В очередь попадают:

- все сценарии с `review_required=true`;
- все failed evaluation results;
- high/emergency risk cases;
- minor safety cases;
- ответы с quality issues.

Минимальная schema элемента очереди:

```text
scenario_id
priority
source_type
case_family
risk_level
conversation_mode
support_protocol
passed
issues
review_reasons
reviewer_decision
training_eligibility
```

Допустимые `reviewer_decision`:

```text
pending
approved
rejected
needs_revision
```

Допустимые `training_eligibility`:

```text
blocked_pending_review
blocked_safety_critical
blocked_failed_evaluation
blocked_review_rejected
blocked_needs_revision
eligible_after_approval
```

Даже если пример прошел automated checks, он не должен попадать в training dataset без отдельного approval workflow.

`make evaluate-report` и `make evaluate-readiness` должны сохранять:

```text
evaluation_reports/v0_5_expert_review_queue.json
evaluation_reports/v0_5_expert_review_queue.md
```

JSON используется для будущей автоматизации review/dataset pipeline, Markdown - для ручной проверки.

Reviewer decision ingestion принимает JSON со следующей минимальной schema:

```text
scenario_id
reviewer_decision
reviewer_notes
```

Правила ingestion:

- `approved` может открыть training eligibility только для passed low/medium review cases;
- `approved` не снимает блокировку с high/emergency/minor safety cases;
- `approved` не снимает блокировку с failed evaluation cases;
- `rejected` и `needs_revision` всегда оставляют пример заблокированным для training dataset;
- unknown или duplicate `scenario_id` в decision-файле блокируют ingestion.

## Instruction training example schema

Будущий instruction tuning dataset может собираться только из `eligible_after_approval` элементов.

Минимальная schema:

```text
id
dataset_version
source_type
locale
user_message
assistant_response
risk_level
conversation_mode
support_protocol
reviewer_decision
tags
```

Правила отбора:

- `reviewer_decision=approved`;
- `training_eligibility=eligible_after_approval`;
- только passed evaluation results;
- только `risk_level=low|medium`;
- только `conversation_mode=support|deep_support`;
- crisis, emergency, minor safety и failed cases не попадают в instruction training examples.

## Будущие реальные данные

Если в будущих версиях появятся реальные данные, нужны:

- явное согласие;
- минимизация сбора;
- анонимизация;
- удаление имен, телефонов, адресов, школ, рабочих мест и редких идентификаторов;
- отдельная политика хранения и удаления;
- запрет использовать кризисные диалоги для обучения без отдельного review.

## Когда начинать обучение модели

Fine-tuning или deep learning нельзя начинать только потому, что локальная модель уже отвечает.

Минимальные условия:

- synthetic/red-team dataset минимум 200 сценариев;
- labels для risk level, conversation mode и support protocol;
- per-protocol quality metrics;
- отдельная политика consent/anonymization для любых real-user data;
- clinician/expert review queue;
- baseline comparison минимум 2-3 локальных моделей;
- повторяемый evaluation report до и после обучения.

До выполнения этих условий обучение считается преждевременным.
