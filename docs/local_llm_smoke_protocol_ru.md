# S.A.N.A. Local LLM Smoke Protocol

Дата версии: 2026-06-02.

## Назначение

Этот документ описывает первый controlled smoke-прогон локальной модели S.A.N.A. через Ollama-compatible provider.

Цель smoke-прогона: проверить, может ли локальная модель дать безопасный candidate response на синтетических low/medium adult сценариях, не затрагивая реальные пользовательские данные.

## Что smoke не делает

- Не обучает модель.
- Не запускает real-user testing.
- Не использует реальные переписки, логи, обращения или production data.
- Не проверяет crisis, emergency и minors через provider.
- Не доказывает клиническую готовность модели.

## Предусловия

На машине оператора должны быть:

- S.A.N.A. repository;
- Python backend dependencies;
- установленный Ollama runtime;
- загруженная локальная модель;
- свободная RAM/VRAM для выбранной модели.

Ollama на Linux ставится по официальной документации Ollama. После установки нужно проверить, что локальный endpoint отвечает на loopback:

```bash
curl http://127.0.0.1:11434/api/tags
```

## Рекомендуемый первый набор моделей

Для текущего сервера без подтвержденного GPU начинать нужно с небольших моделей:

```text
llama3.1:8b
mistral:7b
qwen2.5:7b
gemma2:9b
```

Первая модель по умолчанию:

```bash
ollama pull llama3.1:8b
```

Если CPU-only inference слишком медленный, допускается временно проверить более легкую модель, но результат нельзя считать целевым качеством S.A.N.A.

## Ручной smoke запуск

Запуск разрешается только с явными gate-флагами:

```bash
SANA_LLM_ENABLED=true \
SANA_LLM_PROVIDER=ollama \
SANA_LLM_MODEL=llama3.1:8b \
SANA_OLLAMA_BASE_URL=http://127.0.0.1:11434 \
SANA_LLM_TIMEOUT_SECONDS=30 \
SANA_LLM_MAX_OUTPUT_CHARS=1200 \
SANA_OLLAMA_NUM_PREDICT=384 \
SANA_PROVIDER_SMOKE_ENABLED=true \
SANA_PROVIDER_SMOKE_ALLOW_NETWORK=true \
SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA=true \
SANA_PROVIDER_SMOKE_DATASET=synthetic_only \
make llm-smoke
```

## Ожидаемые отчеты

По умолчанию smoke пишет:

```text
evaluation_reports/llm_smoke_latest.json
evaluation_reports/llm_smoke_latest.md
```

Можно передать свои пути:

```bash
make llm-smoke -- evaluation_reports/ollama_llama31_8b.json evaluation_reports/ollama_llama31_8b.md
```

Если shell не поддерживает такой формат через `make`, можно вызвать скрипт напрямую:

```bash
./scripts/llm_smoke.sh evaluation_reports/ollama_llama31_8b.json evaluation_reports/ollama_llama31_8b.md
```

## Что смотреть в отчете

Главные поля:

```text
total
passed
failed
provider_name
model
candidate_used_count
fallback_count
blocked_reasons
results
```

Интерпретация:

- `candidate_used_count` высокий: модель чаще дает usable candidate.
- `fallback_count` высокий: safety/quality wrapper часто не принимает ответ модели.
- `llm_safety_failed`: модель нарушает safety contract.
- `llm_quality_failed`: модель безопасна, но не выполняет нужный support protocol.
- `llm_provider_timeout`: модель слишком медленная или сервер перегружен.
- `ollama_model_missing`: модель не скачана или имя модели указано неверно.

## Минимальное решение после smoke

После каждого smoke нужно записать решение в comparison matrix:

```text
accept_for_more_tests
needs_prompt_tuning
too_slow
unsafe
not_ready
```

`accept_for_more_tests` не означает production readiness. Это означает только, что модель можно проверять дальше на расширенном synthetic/red-team наборе.

## Запрещено

- Подставлять реальные сообщения людей в smoke prompts.
- Включать provider для minors/crisis/emergency.
- Публиковать raw candidate responses из sensitive тестов.
- Считать smoke клинической валидацией.
- Отключать safety checker ради прохождения smoke.
