# S.A.N.A. v1.5 - User-Local Ollama Runtime Tooling

## Цель версии

v1.5 добавляет ручные инструменты для user-local Ollama runtime без системной установки через `sudo`.

Причина: на сервере `sudo` требует пароль, а системная установка Ollama как service является более рискованным этапом. User-local runtime позволяет подготовить controlled smoke без изменения системных служб.

## Что добавлено

- `scripts/ollama_user_install.sh` - скачать Ollama в `~/.local/ollama`.
- `scripts/ollama_user_serve.sh` - запустить `ollama serve` от текущего пользователя.
- `scripts/ollama_pull_model.sh` - скачать модель.
- `scripts/llm_smoke_ollama_local.sh` - запустить gated smoke с Ollama defaults.
- Make targets:
  - `make ollama-user-install`;
  - `make ollama-serve-user`;
  - `make ollama-pull-model`;
  - `make llm-smoke-ollama-local`.

## Почему не system service

System service требует `sudo` и меняет состояние сервера глобально.

v1.5 выбирает более осторожный подход:

```text
download to user home
  -> run serve manually
  -> pull one model
  -> gated synthetic smoke
  -> stop process manually
```

## Ручной порядок запуска

Окно 1:

```bash
make ollama-user-install
make ollama-serve-user
```

Окно 2:

```bash
make ollama-pull-model
make llm-smoke-ollama-local
```

Для другой модели:

```bash
./scripts/ollama_pull_model.sh mistral:7b
./scripts/llm_smoke_ollama_local.sh mistral:7b
```

## Safety contract

Эти инструменты:

- не входят в `make dev-cycle`;
- не запускают real-user testing;
- не используют реальные пользовательские данные;
- запускают smoke только через существующие gates;
- сохраняют preflight, safety checker, quality checker и fallback.

## Текущее состояние

На 2026-06-02 Ollama еще не установлен на сервере.

v1.5 готовит ручной runtime path, но не выполняет тяжелую загрузку модели автоматически.

## Следующие шаги

1. Запустить `make ollama-user-install`.
2. Запустить `make ollama-serve-user` в отдельной сессии.
3. Скачать `llama3.1:8b`.
4. Выполнить `make llm-smoke-ollama-local`.
5. Заполнить comparison matrix.
