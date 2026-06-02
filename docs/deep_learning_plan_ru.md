# S.A.N.A. Deep Learning Plan

Дата версии: 2026-06-03.

## Что будет видно

На этапе глубокого обучения будет отдельный training workspace, где можно увидеть:

- base model;
- adapter method: LoRA или QLoRA;
- training dataset path;
- validation split;
- epochs;
- learning rate;
- batch size;
- loss по шагам/эпохам;
- evaluation до и после tuning;
- protocol pass rate;
- safety failures;
- language artifacts;
- rollback decision.

## Что не запускаем сейчас

Сейчас не запускается fine-tuning и не меняются веса модели.

Текущий этап создает только безопасный manifest будущего обучения. Manifest нужен, чтобы deep learning не начался случайно, без gates, review и baseline comparison.

## Dry-run

Dry-run показывает будущий запуск обучения без изменения весов модели.

Команда:

```bash
make training-dry-run
```

Входы:

```text
training manifest
approved instruction training examples
```

Выходы:

```text
training_runs/dry_run_report.json
training_runs/dry_run_report.md
```

Dry-run проверяет:

- manifest status;
- dataset size;
- low/medium only;
- отсутствие crisis/emergency/minor_safety;
- train/validation split;
- estimated optimizer steps.

Если manifest имеет `status=blocked_until_readiness`, dry-run должен быть `blocked=true`.

## Минимальная training manifest schema

```text
run_id
base_model
method
dataset_path
output_dir
status
hyperparameters
required_gates
allowed_risk_levels
forbidden_conversation_modes
metrics_to_compare
notes
```

## Обязательные gates

```text
approved_low_medium_only
no_crisis_emergency_minor
evaluation_baseline_green
expert_review_complete
rollback_plan_defined
local_model_baseline_recorded
```

Если gate отсутствует, manifest считается невалидным.

## Начальный режим

Первый manifest должен иметь:

```text
status = blocked_until_readiness
```

Это означает: training pipeline подготовлен, но обучение заблокировано до завершения readiness условий.

## Почему так

Для S.A.N.A. опасно начинать обучение на сырых ответах модели. Модель может усилить плохие паттерны: ставить диагнозы, пропускать safety-вопросы, отвечать уверенно в кризисе или перенимать языковые артефакты.

Поэтому порядок такой:

```text
evaluation -> expert review -> approved low/medium examples -> training manifest -> dry run -> fine-tuning -> post-training evaluation -> rollback/accept decision
```

## Будущий первый эксперимент

Первый реалистичный эксперимент:

```text
base_model = llama3.1:8b или другая модель после baseline comparison
method = qlora
epochs = 1
learning_rate = 0.00002
batch_size = 1
gradient_accumulation_steps = 16
max_seq_length = 2048
validation_split = 0.1
```

Этот эксперимент должен быть synthetic/clinician-authored only и не должен включать real-user data.
