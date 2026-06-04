# S.A.N.A. v2.0 Readiness Release Notes

Дата: 2026-06-02.

## Статус

Начат v2.0 readiness track.

## Сделано

- Добавлен `language_artifact` quality check.
- Добавлен `protocol_summary` в LLM smoke report.
- Добавлен `protocol_summary` в основной evaluation report.
- Добавлен кодовый контракт clinician/expert review queue.
- Добавлены persisted expert review artifacts для `make evaluate-report` и `make evaluate-readiness`.
- Добавлен reviewer decision ingestion с защитой от ошибочного approval safety-critical/failed cases.
- Добавлена schema approved low/medium instruction training examples.
- Добавлен draft training manifest для будущего LoRA/QLoRA без запуска обучения.
- Добавлен `make training-dry-run` без изменения весов модели.
- Добавлен hardware/memory estimate в training dry-run.
- Добавлен profiler evidence contract в training dry-run: отчет показывает, основан ли hardware блок на эвристике или на фактическом снимке окружения через `nvidia-smi`.
- Добавлен dataset manifest в training dry-run: fingerprint датасета, deterministic split seed, train/validation ids и id fingerprints.
- Усилена dataset safety validation: duplicate ids, `reviewer_decision != approved`, crisis/emergency/minor modes блокируют dry-run.
- Добавлен строгий readiness profile `v2_training`: отдельный gate для deep learning, который блокирует обучение до `>=200` сценариев, baseline comparison, clinician-authored coverage и per-protocol coverage.
- `v2_training` profile теперь проверяет evidence artifacts: approved examples, training manifest, dry-run report, local model comparison и rollback plan.
- Добавлен `docs/training_rollback_plan_ru.md` как черновой rollback contract для будущих adapter-based training runs.
- Зафиксированы gates перед deep learning.

## Не готово

- Fine-tuning.
- Deep learning.
- Real-user testing.
- Clinical validation.

## Следующий шаг

Расширить synthetic/red-team dataset, approved low/medium examples и добавить real training profiler после установки training dependencies.
