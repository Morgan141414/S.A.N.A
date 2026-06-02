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
- Зафиксированы gates перед deep learning.

## Не готово

- Fine-tuning.
- Deep learning.
- Real-user testing.
- Clinical validation.

## Следующий шаг

Расширить synthetic/red-team dataset и approved low/medium examples через clinician-authored сценарии.
