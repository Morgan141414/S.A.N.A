# Release readiness S.A.N.A. v0.2

Статус: deterministic protocol + response quality release candidate.

Дата среза: 2026-06-01.

## Что входит

- ТЗ v0.2 без LLM, fine-tuning и RAG.
- Выбор `support_protocol` поверх `risk_classifier` и `policy_router`.
- Протоколы: `general_support`, `depressive_support`, `anxiety_grounding`, `panic_grounding`, `grief_loneliness`, `conflict_stress`, `minor_support`, `minor_safety`, `crisis`, `emergency`.
- `quality_check` в API-ответе.
- Проверки качества: эмпатическое отражение, следующий шаг, фокусный вопрос, длина кризисного ответа, self-harm screen для депрессивных признаков, medical red flag check для паники.
- Regression tests для v0.1 и новых v0.2 сценариев.

## Не входит

- Обученная модель.
- LLM-генерация.
- Clinical validation как medical device.
- Локализованные кризисные ресурсы.
- Долговременная память и хранение сессий.

## Response Contract v0.2

```text
risk_level
risk_score
conversation_mode
support_protocol
risk_assessment
safety_check
quality_check
response
```

`response` должен равняться `safety_check.safe_response`.

## Quality Gate

Последний dev-cycle:

```text
65 passed
ruff: All checks passed
```

Остаточное предупреждение:

```text
StarletteDeprecationWarning from FastAPI TestClient/httpx
```

Это не блокирует v0.2, но стоит вынести в P1 технический cleanup.

## Known Limitations

- Протоколы остаются deterministic и шаблонными.
- Распознавание сценариев основано на словарях и может ошибаться при сарказме, смешанных состояниях или коротких сообщениях.
- Английские ответы пока менее развиты, чем русские.
- Нет экспертной клинической валидации.

## Следующий backlog

- Добавить shame/guilt и burnout как отдельные протоколы.
- Перенести QA-сценарии в fixture JSON.
- Улучшить English parity.
- Подготовить dataset/evaluation plan для будущей v0.3.

