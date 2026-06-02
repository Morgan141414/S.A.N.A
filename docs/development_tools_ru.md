# S.A.N.A. Development Tools

Дата версии: 2026-06-02.

## Текущий рабочий набор

- `multi_agent_v1` - субагенты для параллельной проверки кода, ревью и bounded implementation задач.
- `rg` - быстрый поиск по коду и тестам.
- `rsync` + SSH - синхронизация локальной рабочей копии с сервером.
- `make check` - Ruff и pytest.
- `make dev-cycle` - полный цикл разработки и quality report.
- `make evaluate` - P0 synthetic/red-team evaluation gate.
- `make evaluate-readiness` - readiness decision и regression diff.
- `make llm-smoke-ollama-local` - gated local LLM smoke только на synthetic-only сценариях.
- Ollama user-local runtime - локальные модели без покупки API key.

## Как использовать субагентов

Субагентов использовать только для задач, которые можно безопасно отделить:

- быстрый read-only анализ конкретного модуля;
- независимое code review;
- bounded patch в файлах с четкой ответственностью;
- параллельная проверка рисков перед релизом.

Субагенты не должны:

- ослаблять safety checker;
- менять crisis/minor policy без отдельного решения;
- трогать реальные пользовательские данные;
- выполнять разрушительные git-команды;
- дублировать одну и ту же работу друг друга.

## Кандидаты на будущие инструменты

Эти инструменты стоит рассмотреть после стабилизации v1.x:

- `pre-commit` - запуск Ruff/tests перед commit.
- `mypy` или `pyright` - статическая типизация.
- `coverage.py` - контроль покрытия тестами.
- `bandit` - базовый Python security scan.
- `semgrep` - кастомные safety/security правила.
- `dvc` - версионирование датасетов и evaluation artifacts.
- `MLflow` или аналог - учет экспериментов fine-tuning/evaluation.
- `Great Expectations` или lightweight schema checks - контроль качества датасетов.

## Правило выбора инструмента

Инструмент добавляется в проект только если он:

- усиливает безопасность;
- уменьшает вероятность регрессии;
- помогает оценивать качество модели;
- не усложняет процесс сильнее, чем приносит пользы.
