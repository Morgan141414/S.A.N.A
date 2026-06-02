# S.A.N.A. v1.9 - Guarded Protocol Repair

## Цель версии

v1.9 добавляет guarded protocol repair для безопасных LLM-кандидатов, которым не хватает обязательного элемента support protocol.

Главная идея: не ослаблять quality checker и не доверять модели без проверки. Если candidate response уже прошел safety checker, но не прошел quality checker, система может deterministic-образом добавить недостающую protocol-фразу и затем снова прогнать safety + quality.

## Что добавлено

- `repair_protocol_response()` в LLM contract layer.
- Новые поля guarded result:
  - `repaired_response`;
  - `repair_used`.
- Новые поля LLM smoke report:
  - `repair_count`;
  - `repair_used`;
  - `repaired_response`.
- Тесты на depressive self-harm repair.
- Тесты на panic medical red-flag repair.
- Markdown smoke report теперь показывает `Repair used`.

## Repair Rules

Repair применяется только после успешного safety check исходного LLM-кандидата.

Текущие repair-правила:

```text
missing_empathic_reflection
  -> prepend empathic reflection

missing_next_step
  -> append one small safe next step

missing_focused_question
  -> append one focused question

missing_self_harm_screen + depressive_support
  -> append "Появлялись ли мысли навредить себе или не жить?"

missing_panic_medical_red_flag_check + panic_grounding
  -> append "Есть ли боль в груди, обморок, сильная одышка или риск навредить себе?"
```

После repair:

```text
repaired response
  -> safety checker
  -> quality checker
  -> use only if both pass
```

Если repair не проходит проверки, система использует deterministic fallback.

## Результат expanded smoke

До repair, v1.8:

```text
total: 15
passed: 15
candidate_used_count: 10
fallback_count: 5
blocked_reasons:
  llm_quality_failed: 5
```

После repair, v1.9 repeated run:

```text
total: 30
passed: 30
candidate_used_count: 30
fallback_count: 0
repair_count: 7
blocked_reasons: none
runtime: 83 seconds
```

## Интерпретация

v1.9 не делает модель клинически готовой.

Но v1.9 показывает, что safety-first architecture стала сильнее:

- LLM сохраняет живой тон ответа;
- deterministic repair закрывает обязательные protocol gaps;
- финальный ответ снова проверяется safety и quality;
- fallback остается последней защитой.

## Решение

```text
llama3.1:8b expanded + repair -> accept_for_repeated_synthetic_tests
```

Это означает:

- можно запускать более длинные repeated synthetic/red-team тесты;
- real-user testing все еще запрещен;
- minors/high/crisis/emergency остаются вне LLM path;
- clinical validation не пройдена.

## Следующий шаг

v2.0 readiness track должен добавить:

```text
larger synthetic/red-team set
  -> language artifact checks
  -> per-protocol quality scoring
  -> clinician review queue design
  -> dataset logging policy
  -> local model comparison across 2-3 models
```
