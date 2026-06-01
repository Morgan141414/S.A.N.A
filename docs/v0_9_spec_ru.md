# Техническое задание S.A.N.A. v0.9

Статус: implementation slice for Local LLM Provider.

Дата среза: 2026-06-01.

v0.9 переводит основной путь развития S.A.N.A. с платного API на локальный provider. Цель версии - добавить Ollama-compatible адаптер для open-weight моделей, сохранив все safety/fallback ограничения v0.6-v0.8.

## 1. Цели

- Поддержать `SANA_LLM_PROVIDER=ollama`.
- Использовать локальный endpoint `SANA_OLLAMA_BASE_URL`, по умолчанию `http://127.0.0.1:11434`.
- Не требовать API key для локального provider.
- Передавать prompt policy как `system`, пользовательское сообщение как `prompt`.
- Использовать только guarded response path.
- Оставить LLM выключенной по умолчанию.
- Сохранить запрет provider path для crisis, emergency, minors и неизвестного возраста.
- Проверять local provider через mock/fake client в automated tests.

## 2. Не входит

- Обучение модели.
- Fine-tuning, LoRA, QLoRA.
- RAG, embeddings, memory.
- Streaming.
- Production traffic.
- Использование реальных пользовательских данных.
- Клиническая валидация качества локальной модели.
- Гарантия уровня ChatGPT 5.5 на текущем сервере.

## 3. Env Settings

Минимальная локальная конфигурация:

```text
SANA_LLM_ENABLED=true
SANA_LLM_PROVIDER=ollama
SANA_LLM_MODEL=llama3.1:8b
SANA_OLLAMA_BASE_URL=http://127.0.0.1:11434
SANA_LLM_TIMEOUT_SECONDS=30
```

Для ручного smoke:

```text
SANA_PROVIDER_SMOKE_ENABLED=true
SANA_PROVIDER_SMOKE_ALLOW_NETWORK=true
SANA_PROVIDER_SMOKE_ACK_NO_USER_DATA=true
SANA_PROVIDER_SMOKE_DATASET=synthetic_only
```

## 4. Safety Rules

Local provider output is never authoritative.

Модель не может:

- менять `risk_level`;
- менять `conversation_mode`;
- менять `support_protocol`;
- отвечать напрямую без `safety_check`;
- обходить `quality_check`;
- использоваться для несовершеннолетних;
- использоваться для crisis/emergency.

Любая ошибка provider, пустой ответ, unsafe output или low-quality output ведет к deterministic fallback.

## 5. Hardware Reality

Текущий сервер с RTX 3050 8GB подходит для экспериментов с маленькими quantized моделями. Он не подходит для обучения или инференса моделей уровня frontier.

Практичный локальный старт:

```text
7B/8B quantized model
Ollama or llama.cpp-compatible runtime
synthetic smoke only
manual review
```

Для серьезного обучения или более сильных моделей желательно:

```text
24GB+ VRAM
64GB+ RAM
1-2TB NVMe
```

## 6. Release Gates

v0.9 считается готовой, если:

- `make dev-cycle` проходит;
- `make evaluate` проходит;
- `make evaluate-readiness` проходит;
- Ollama provider покрыт unit tests без реального network call;
- smoke без env gates блокируется безопасно;
- локальный provider не требует API key;
- docs фиксируют ограничения текущего сервера.
