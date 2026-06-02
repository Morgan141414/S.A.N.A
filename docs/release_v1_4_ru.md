# S.A.N.A. v1.4 Release Readiness

## Статус

v1.4 готова, если первый локальный smoke можно провести по документированному протоколу без реальных пользовательских данных и без случайного provider call.

## Область версии

- Local LLM smoke protocol.
- Local model comparison matrix.
- Recommended first model list.
- Manual gate command template.
- Decision values for model comparison.
- Documentation that Ollama is not installed yet on the current server.

## Проверки

Перед релизом должны проходить:

```bash
make dev-cycle
make evaluate
make evaluate-readiness
```

`make llm-smoke` без ручных gate-флагов должен завершаться кодом `2`.

## Blocking Conditions

v1.4 не готова, если:

- протокол предлагает использовать реальные пользовательские данные;
- smoke может быть принят как clinical validation;
- provider можно запустить без manual gates;
- comparison matrix не фиксирует fallback и blocked reasons;
- recommended model list включает только тяжелые модели, непрактичные для текущего сервера;
- документация скрывает факт, что Ollama еще не установлена.

## Известные ограничения

- Ollama еще не установлена.
- Модели еще не скачаны.
- Реальный local smoke еще не выполнен.
- Latency пока не измерена.
- Никакая локальная модель пока не принята даже для расширенных тестов.

## Решение

v1.4 считается подготовительным релизом. Следующий этап должен быть отдельным controlled runtime этапом: установка Ollama, загрузка модели и ручной smoke.
