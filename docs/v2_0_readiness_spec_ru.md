# S.A.N.A. v2.0 Readiness Track

## Цель

v2.0 readiness track готовит проект к более серьезной оценке локальной модели и будущему fine-tuning/deep learning этапу.

v2.0 не означает real-user testing и не означает клиническую готовность.

## Что добавлено в начале трека

- `language_artifact` quality issue для русскоязычных ответов с явными языковыми артефактами.
- `protocol_summary` в LLM smoke report:
  - total;
  - passed;
  - candidate_used;
  - fallback;
  - repair.
- `protocol_summary` в основной evaluation report:
  - total;
  - passed;
  - failed;
  - pass_rate;
  - failures_by_issue.
- Clinician/expert review queue contract:
  - review_reasons;
  - reviewer_decision;
  - training_eligibility;
  - блокировка safety-critical и failed evaluation cases от прямого попадания в training dataset.

## Почему это важно

После v1.9 система стала проходить expanded smoke без fallback, но часть LLM-кандидатов все еще может звучать непрофессионально из-за языковых артефактов.

Для психологического ассистента качество языка является safety-adjacent требованием: небрежная речь снижает доверие и может ощущаться как отсутствие внимательности.

## Deep Learning Gate

Глубокое обучение модели разрешено начинать только после следующих условий:

```text
1. Synthetic/red-team dataset >= 200 сценариев
2. Все сценарии имеют expected risk/mode/protocol labels
3. Есть per-protocol quality scoring
4. Есть политика данных и запрет real-user data без consent/anonymization
5. Есть clinician/expert review queue design и кодовый контракт
6. Есть baseline local model comparison минимум по 2-3 моделям
7. Есть повторяемые evaluation reports
8. Есть rollback plan после fine-tuning
```

## Ожидаемый момент fine-tuning

Первый эксперимент LoRA/QLoRA можно планировать после v2.x readiness gates, когда:

- локальная inference path стабильна;
- evaluation set достаточно широкий;
- quality failures классифицированы;
- есть dataset для instruction tuning;
- есть понятный способ сравнить base model и tuned model.

До этого обучение будет преждевременным: модель может выучить слабые или небезопасные паттерны, а мы не сможем доказать улучшение.

## Следующие задачи v2.0

- расширить synthetic/red-team set;
- добавить language artifact coverage;
- расширить clinician review queue до persisted artifact/report;
- подготовить dataset schema для будущего tuning.
