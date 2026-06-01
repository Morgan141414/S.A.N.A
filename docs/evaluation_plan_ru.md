# Evaluation Plan S.A.N.A. v0.3

## Цель

v0.3 вводит воспроизводимую оценку поведения S.A.N.A. на сценариях.

## Что проверяется

- корректный `risk_level`;
- корректный `conversation_mode`;
- корректный `support_protocol`;
- прохождение `safety_check`;
- прохождение `quality_check`;
- наличие обязательных фраз;
- отсутствие запрещенных фраз.

## Метрики

```text
total
passed
failed
pass_rate = passed / total
failures_by_issue
failures_by_tag
```

## P0 для v0.3

- JSON fixture с eval-сценариями.
- Evaluation runner.
- Тесты загрузки сценариев.
- Тесты успешного прохождения базовой матрицы.
- Тесты, что runner ловит mismatch.

## Не входит

- обучение модели;
- LLM-as-judge;
- автоматическая клиническая оценка;
- реальные пользовательские данные.

