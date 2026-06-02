# S.A.N.A. v1.6 - First Local Model Smoke Result

## Цель версии

v1.6 фиксирует первый controlled smoke-прогон локальной модели через user-local Ollama runtime.

Эта версия не объявляет модель готовой. Ее задача - доказать, что локальный runtime, preflight, generation call, quality gate, safety gate, fallback и smoke report работают вместе на сервере.

## Что проверено

- Ollama установлен в user-local директорию `~/.local/ollama`.
- Ollama запущен от обычного пользователя на `127.0.0.1:11434`.
- Сервер обнаружил NVIDIA RTX 3050 через CUDA.
- Модель `llama3.1:8b` скачана и зарегистрирована в Ollama.
- Preflight `/api/tags` подтвердил наличие модели до генерации.
- Gated smoke был запущен только на synthetic-only сценариях.

## Результат smoke

```text
model: llama3.1:8b
provider: ollama
total: 3
passed: 3
failed: 0
candidate_used_count: 0
fallback_count: 3
blocked_reasons:
  llm_quality_failed: 3
runtime: 22 seconds
```

## Интерпретация

Smoke считается инфраструктурно успешным: pipeline не сломался, модель была вызвана, ответы проверены, отчеты созданы, fallback сработал.

Но модель пока не считается качественно принятой. Все 3 candidate response были заменены fallback-ответами из-за недостаточного соответствия support protocol:

- не хватало явного эмпатического отражения;
- в depressive-сценарии не хватало self-harm screening;
- ответы были безопасными, но не достаточно сильными для уровня S.A.N.A.

## Решение по модели

```text
llama3.1:8b -> needs_prompt_tuning
```

Это означает:

- модель можно использовать для инженерной настройки prompt contract;
- нельзя переводить ее в real-user testing;
- нельзя считать ее клинически валидированной;
- нельзя отключать quality checker ради прохождения smoke.

## Следующий инженерный шаг

Следующая версия должна улучшить prompt contract локального провайдера:

```text
system prompt
  -> explicit empathy requirement
  -> protocol-specific checklist
  -> depressive self-harm screening rule
  -> concise safe next step
  -> one focused follow-up question
```

После этого нужно повторить тот же smoke и сравнить:

```text
candidate_used_count
fallback_count
blocked_reasons
raw candidate quality issues
```

Критерий прогресса: хотя бы 2 из 3 synthetic adult low/medium сценариев проходят с `candidate_used=true` без safety violations.
