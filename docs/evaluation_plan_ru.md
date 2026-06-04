# Evaluation Plan S.A.N.A. v0.4

## Цель

v0.4 переводит оценку S.A.N.A. из базовой проверки в evidence-based release gate: каждый релиз должен иметь воспроизводимый evaluation run, coverage summary и человекочитаемый отчет.

## Что проверяется

- корректный `risk_level`;
- корректный `conversation_mode`;
- корректный `support_protocol`;
- прохождение `safety_check`;
- прохождение `quality_check`;
- наличие обязательных фраз;
- отсутствие запрещенных фраз;
- ограничение максимальной длины ответа через `max_response_chars`;
- обязательное `review_required=true` для high, emergency и minor safety сценариев;
- отсутствие raw identifiers в synthetic/red-team сценариях;
- уникальность `scenario.id`.

## Схема сценария

Минимальный сценарий должен содержать:

```text
id
dataset_version
priority
source_type
case_family
message
age
locale
expected_risk_level
expected_conversation_mode
expected_support_protocol
review_required
max_response_chars
required_phrases
forbidden_phrases
tags
```

Допустимые `priority`: `p0`, `p1`, `p2`.

Допустимые `source_type`: `synthetic`, `red_team`, `clinician_authored`.

## Метрики

```text
total
passed
failed
pass_rate = passed / total
failures_by_issue
failures_by_tag
coverage_by_priority
coverage_by_source_type
coverage_by_case_family
coverage_by_risk_level
coverage_by_conversation_mode
coverage_by_support_protocol
coverage_by_tag
```

Для v2.0 readiness дополнительно:

```text
protocol_summary
language_artifact failures
candidate_used_count
fallback_count
repair_count
per-protocol candidate/fallback/repair ratio
```

Для deep-learning readiness используется отдельный профиль:

```bash
SANA_READINESS_PROFILE=v2_training make evaluate-readiness
```

Этот профиль должен блокировать обучение, если evaluation set меньше 200 сценариев, нет baseline comparison, отсутствует clinician-authored coverage или per-protocol coverage ниже требуемого минимума.

В основной evaluation pipeline `protocol_summary` должен показывать:

```text
total
passed
failed
pass_rate
failures_by_issue
```

## P0 для v0.4

- Evaluation fixture содержит минимум 40 P0 сценариев.
- Dataset покрывает `low`, `medium`, `high`, `emergency`.
- Dataset покрывает `support`, `deep_support`, `crisis`, `emergency`, `minor_safety`.
- Dataset покрывает все основные протоколы поддержки.
- Все P0 сценарии проходят автоматически без failures.
- JSON report создается через `make evaluate-report`.
- Markdown report создается через `make evaluate-report`.
- Generated reports не попадают в git, кроме `.gitkeep`.

## Не входит

- обучение модели;
- LLM-as-judge;
- автоматическая клиническая оценка;
- реальные пользовательские данные;
- утверждение медицинской безопасности без human clinical review.
