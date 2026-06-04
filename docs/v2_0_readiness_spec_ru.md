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
- Persisted expert review artifacts:
  - `evaluation_reports/v0_5_expert_review_queue.json`;
  - `evaluation_reports/v0_5_expert_review_queue.md`.
- Reviewer decision ingestion:
  - `approved`;
  - `rejected`;
  - `needs_revision`;
  - duplicate/unknown scenario guard;
  - safety-critical approval does not unlock training eligibility.
- Approved low/medium instruction training example schema:
  - user_message;
  - assistant_response;
  - risk/mode/protocol labels;
  - reviewer_decision;
  - no crisis/emergency/minor/failed cases.
- Draft training manifest:
  - base_model;
  - LoRA/QLoRA method;
  - hyperparameters;
  - required gates;
  - status `blocked_until_readiness`.
- Training dry-run:
  - validates manifest and dataset;
  - blocks duplicate/unapproved/minor/crisis/emergency training examples;
  - records dataset fingerprint;
  - records deterministic train/validation split ids and fingerprints;
  - computes train/validation split;
  - estimates optimizer steps;
  - estimates VRAM/RAM and hardware risk;
  - records profiler evidence source;
  - does not modify model weights.

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
5. Есть clinician/expert review queue design, кодовый контракт, persisted artifacts и decision ingestion
6. Есть baseline local model comparison минимум по 2-3 моделям
7. Есть повторяемые evaluation reports
8. Есть approved low/medium instruction example schema
9. Есть draft training manifest
10. Есть dry-run training report без изменения весов модели, с dataset manifest, deterministic split, hardware estimate и profiler evidence source
11. Есть rollback plan после fine-tuning
```

Проверка deep-learning readiness должна запускаться отдельным строгим профилем:

```bash
SANA_READINESS_PROFILE=v2_training make evaluate-readiness
```

Обычный `make evaluate-readiness` отвечает на вопрос "стабилен ли текущий release/evaluation layer?". Профиль `v2_training` отвечает на другой вопрос: "можно ли уже начинать обучение модели?". Для текущего этапа `v2_training` должен возвращать `not_ready`, пока не закрыты dataset scale, per-protocol coverage, clinician-authored coverage, baseline comparison и training artifacts.

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
- расширить approved low/medium examples через clinician-authored сценарии;
- расширить profiler evidence до real training profiler после установки training dependencies;
