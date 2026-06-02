# S.A.N.A. v1.4 - Controlled Local Model Smoke Preparation

## Цель версии

v1.4 готовит первый controlled smoke-прогон локальной модели.

Эта версия не устанавливает Ollama, не скачивает модель и не запускает real provider call. Она фиксирует безопасную процедуру, чтобы следующий тяжелый этап проходил не хаотично, а по протоколу.

## Что добавлено

- `docs/local_llm_smoke_protocol_ru.md` - инструкция controlled smoke-прогона.
- `docs/local_model_comparison_matrix_ru.md` - матрица сравнения локальных моделей.
- Рекомендуемый первый набор моделей:
  - `llama3.1:8b`;
  - `mistral:7b`;
  - `qwen2.5:7b`;
  - `gemma2:9b`.
- Явные smoke gates для локального запуска.
- Правила интерпретации `candidate_used_count`, `fallback_count` и `blocked_reasons`.
- Decision values для дальнейшего тестирования моделей.

## Текущий сервер

На 2026-06-02 Ollama на сервере не установлена.

Текущие характеристики сервера достаточны для разработки, тестов и пробного CPU-only inference небольших моделей. Они не подходят для обучения большой модели с нуля.

## Safety contract

Controlled local smoke:

- использует только synthetic-only сценарии;
- не использует реальные пользовательские данные;
- не отправляет minors, crisis, emergency и high-risk сценарии в provider;
- не отключает safety checker;
- не считается клинической валидацией;
- не означает production readiness.

## Почему это важно

Нам нужна не просто локальная модель, а управляемый процесс отбора модели.

v1.4 делает следующий шаг измеримым:

```text
install runtime
pull model
preflight
manual gated smoke
read summary
fill comparison matrix
decide next test stage
```

## Следующие шаги

1. Установить Ollama на сервер или отдельную тестовую машину.
2. Скачать первую модель `llama3.1:8b`.
3. Запустить manual gated smoke.
4. Заполнить comparison matrix.
5. Решить, какую модель проверять следующей.
