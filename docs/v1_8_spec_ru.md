# S.A.N.A. v1.8 - Expanded Local LLM Evaluation Set

## Цель версии

v1.8 расширяет local LLM smoke за пределы трех базовых сценариев.

Цель: проверить не только первый удачный core smoke, но и устойчивость локальной модели на более широком adult low/medium synthetic наборе.

## Что добавлено

- `EXPANDED_SAFE_SMOKE_SCENARIOS` в `llm_smoke.py`.
- Выбор набора через `SANA_LLM_SMOKE_SET`:
  - `core` - 3 быстрых сценария;
  - `expanded` - 15 adult low/medium сценариев.
- Повторные прогоны через `SANA_LLM_SMOKE_REPEATS`.
- Поля отчета:
  - `scenario_set`;
  - `repeats`.
- Скрипт:
  - `scripts/llm_smoke_ollama_expanded.sh`.
- Make target:
  - `make llm-smoke-ollama-expanded`.

## Состав expanded-набора

Expanded set покрывает:

```text
general_support: 3
anxiety_grounding: 3
depressive_support: 3
panic_grounding: 2
grief_loneliness: 2
conflict_stress: 2
```

Все сценарии:

- synthetic-only;
- adult only;
- low/medium risk only;
- не включают crisis, emergency, high-risk или minors.

## Результат `llama3.1:8b`

После v1.7 hard prompt rule expanded smoke дал:

```text
total: 15
passed: 15
failed: 0
candidate_used_count: 10
fallback_count: 5
blocked_reasons:
  llm_quality_failed: 5
runtime: 44 seconds
```

## Интерпретация

Системный результат безопасен: все 15 финальных ответов прошли.

Но локальная модель как candidate нестабильна:

- depressive-сценарии иногда пропускают self-harm screen;
- panic-сценарии иногда пропускают medical red flag check;
- отдельные ответы теряют focused question;
- встречаются языковые артефакты в mixed-language сценариях.

## Решение

```text
llama3.1:8b expanded -> needs_protocol_repair
```

Это означает:

- модель остается пригодной для инженерных экспериментов;
- expanded-набор не допускает ее к real-user testing;
- следующий шаг должен быть не ослабление quality checker, а protocol repair/scaffold.

## Следующий шаг

v1.9 должна добавить guarded protocol repair:

```text
safe LLM candidate
  -> detect missing protocol-required element
  -> append or repair deterministic protocol sentence
  -> rerun safety checker
  -> rerun quality checker
  -> use repaired candidate only if both pass
```

Это позволит сохранять живой LLM-тон, но не терять обязательные safety/protocol элементы.
