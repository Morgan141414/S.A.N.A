# S.A.N.A. Training Rollback Plan

Дата версии: 2026-06-04.

## Статус

Черновой rollback contract для будущего LoRA/QLoRA fine-tuning.

Этот документ не разрешает обучение модели. Он фиксирует, как остановить или откатить training result, если post-training evaluation ухудшит safety, качество языка или protocol adherence.

## Когда rollback обязателен

Rollback обязателен, если после fine-tuning появляется хотя бы одно условие:

- новый P0 safety failure;
- новый crisis/emergency/minor routing failure;
- рост `safety_failure_count`;
- рост `language_artifact_count`;
- падение protocol pass rate;
- рост fallback из-за unsafe/low-quality LLM candidate;
- ухудшение на baseline local model comparison;
- reviewer помечает tuned response как unsafe, misleading или непрофессиональный.

## Что откатываем

Первый training experiment должен быть adapter-based:

```text
method = qlora или lora
base_model = immutable local base model
adapter = отдельный output_dir внутри training_runs/
```

Rollback означает:

```text
disable tuned adapter
return inference to approved base model path
keep artifacts for audit
do not delete failed adapter before review
```

## Минимальные artifacts

Перед accept/reject решением должны существовать:

```text
pre_training_evaluation_report
post_training_evaluation_report
training_manifest
training_dry_run_report
dataset_manifest
adapter_output_dir
rollback_decision
```

## Accept criteria

Tuned model можно принять только если:

- P0 failures = 0;
- new blocking regressions = 0;
- crisis/emergency/minor deterministic guardrails не изменились;
- safety_failure_count не вырос;
- language_artifact_count не вырос;
- protocol pass rate не упал;
- expert review не выявил safety-critical degradation;
- rollback path проверен вручную.

## Reject criteria

Tuned model отклоняется, если любое обязательное условие accept criteria не выполнено.

## Решение

Каждый training run должен получить одно из решений:

```text
accepted
rejected_rollback_required
needs_revision
```

Решение должно указывать:

```text
run_id
base_model
adapter_path
dataset_fingerprint
pre_training_report
post_training_report
decision
reason
reviewer
date
```
