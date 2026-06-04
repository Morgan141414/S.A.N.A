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

Если `training_runs/draft_training_manifest.json` еще не существует, команда создает безопасный draft manifest со статусом `blocked_until_readiness`. Если approved dataset еще не создан, отчет все равно создается, но остается заблокированным с причиной `dataset_empty`.

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
- duplicate training example ids;
- reviewer decision: only approved;
- dataset fingerprint;
- train/validation ids fingerprint;
- deterministic split seed;
- low/medium only;
- отсутствие crisis/emergency/minor_support/minor_safety;
- train/validation split;
- estimated optimizer steps.
- approximate VRAM/RAM estimate;
- hardware risk;
- GPU availability.
- profiler evidence source.

Если manifest имеет `status=blocked_until_readiness`, dry-run должен быть `blocked=true`.

Hardware estimate является эвристикой, а не разрешением на обучение. Если estimate близок к лимиту VRAM, dry-run должен явно показать warning. На RTX 3050 8GB 8B QLoRA считается tight/risky target, а full LoRA для 8B должен блокироваться по памяти.

Profiler evidence показывает, есть ли фактический снимок окружения или отчет основан только на эвристике. По умолчанию evidence имеет `source=not_collected`, чтобы dry-run не зависел от драйверов и training dependencies. Для ручной проверки сервера можно включить сбор:

```bash
SANA_TRAINING_COLLECT_PROFILER=true make training-dry-run
```

Сейчас profiler evidence может собрать базовые данные через `nvidia-smi`: имя GPU, общий VRAM, свободный VRAM и версию драйвера. Это все еще не заменяет реальный profiler первого training run.

## Минимальная training manifest schema

```text
run_id
base_model
method
dataset_path
output_dir
status
dataset_manifest
hyperparameters
adapter_config
hardware_profile
required_gates
allowed_risk_levels
forbidden_conversation_modes
metrics_to_compare
notes
```

## Dataset manifest

Каждый dry-run должен сохранять проверяемую сводку датасета:

```text
dataset_path
dataset_fingerprint
example_ids_fingerprint
split_seed
split_algorithm
total_examples
train_example_ids
validation_example_ids
train_ids_fingerprint
validation_ids_fingerprint
risk_level_counts
conversation_mode_counts
support_protocol_counts
notes
```

Если в approved training examples есть повторяющиеся `id`, dry-run должен быть `blocked=true`. Если example имеет `reviewer_decision != approved` или относится к minor/crisis/emergency mode, dry-run тоже должен блокироваться. Это защищает будущий fine-tuning от неявного дублирования, нечестного train/validation split и обхода expert review.

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
adapter_rank = 16
quantization_bits = 4
gradient_checkpointing = true
```

Этот эксперимент должен быть synthetic/clinician-authored only и не должен включать real-user data.
