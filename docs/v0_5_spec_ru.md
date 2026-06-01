# Техническое задание S.A.N.A. v0.5

Статус: baseline diff + regression visibility + release decision implementation slice.

Дата среза: 2026-06-01.

Этот документ описывает слой v0.5 поверх реализованной v0.4 evaluation/reporting foundation. v0.4 уже зафиксировала расширенный P0 evaluation set, coverage summary, JSON/Markdown reports и базовые release gates. v0.5 добавляет формальный контур сравнения с baseline, видимость регрессий, readiness decision и release gates, которые reviewer может использовать для принятия решения о релизе.

Текущий implemented slice v0.5 закрывает backend-функции baseline diff, regression diff JSON, readiness decision Markdown и `make evaluate-readiness`. Более широкий reviewer workflow, accepted risk approvals, trend history и clinical sign-off остаются следующими расширениями.

## 1. Цели v0.5

- Зафиксировать единый baseline diff contract для сравнения release candidate с утвержденным baseline.
- Сделать регрессии видимыми по scenario id, severity, priority, risk level, protocol family и safety check.
- Ввести readiness decision как обязательный документ release candidate.
- Разделить автоматические gates, manual review и accepted risk.
- Описать release gates для safety-first mental health AI без подмены clinical/safety review автоматикой.
- Дать reviewer минимальный набор вопросов: что изменилось, что сломалось, что улучшилось, что принято как риск, можно ли выпускать.
- Снизить риск релиза с "зеленым" summary, но скрытой P0/P1 регрессией.

## 2. Не входит в v0.5

- Изменение backend-логики, risk classifier, response generator или safety checker.
- Подключение LLM, LLM-as-judge, fine-tuning или RAG.
- Автоматическое принятие клинических решений.
- Production dashboard, reviewer UI или BI-платформа.
- Использование реальных пользовательских диалогов.
- Полная медицинская, юридическая или regulatory сертификация.
- Автоматическое утверждение release decision без human owner.

## 3. Основной принцип v0.5

Release candidate считается reviewable только если для него можно ответить на четыре вопроса:

```text
1. С чем сравниваем?
2. Что изменилось?
3. Что блокирует релиз?
4. Кто и на каком основании принял readiness decision?
```

Pass rate, coverage summary и Markdown report остаются важными, но недостаточными. Для v0.5 нужен явный baseline id, diff against baseline, список blocking regressions и документированное решение: `ready`, `ready_with_accepted_risk` или `not_ready`.

Если автоматический gate и human safety review расходятся, приоритет имеет более осторожное решение. Accepted risk допустим только для конкретного scenario id, run id или известного ограничения и не должен скрывать P0 safety regression.

## 4. Термины

`release candidate` - конкретный build/run, который рассматривается для выпуска.

`baseline` - последний утвержденный evaluation run или явно выбранный reference run, с которым сравнивается release candidate.

`baseline diff` - machine-readable и human-readable сравнение текущего run с baseline.

`regression` - ухудшение результата, severity, safety check, expected-vs-actual match, coverage или dataset integrity относительно baseline.

`blocking regression` - регрессия, которая запрещает release без исправления или формального manual override там, где override допустим.

`readiness decision` - итоговое release-решение с владельцем, датой, run id, baseline id, gates status, known risks и подписью reviewer/owner.

`accepted risk` - явно принятый риск, ограниченный конкретным scope, сроком и owner. Accepted risk не равен "игнорировать failure".

## 5. P0 Scope

P0 - обязательный минимум v0.5. Невыполнение любого P0 пункта блокирует readiness.

### 5.1 Baseline Identity

Каждый release candidate должен иметь зафиксированный baseline:

```text
baseline_id
baseline_run_id
baseline_dataset_version
baseline_created_at
baseline_approved_by
baseline_approval_date
baseline_source_path
baseline_notes
```

Если baseline отсутствует, допускается только `first_baseline_decision`. Такое решение должно быть явным и не может использоваться для скрытия известных P0 failures.

### 5.2 Baseline Diff Contract

Минимальный `baseline_diff` должен показывать:

- новый, исправленный и неизменный status по scenario id;
- новые failures;
- исправленные failures;
- changed risk_level;
- changed support_protocol;
- changed conversation_mode;
- changed safety checks;
- changed severity;
- response length regressions;
- missing required elements;
- introduced forbidden elements;
- added scenarios;
- removed scenarios;
- changed scenario labels;
- changed `review_required`.

Рекомендуемая минимальная структура:

```json
{
  "run_id": "sana_eval_2026_06_01_001",
  "baseline_id": "sana_eval_2026_05_31_001",
  "dataset_version": "v0.5-rc1",
  "status": "not_ready",
  "summary": {
    "new_failures": 1,
    "fixed_failures": 2,
    "blocking_regressions": 1,
    "dataset_changes": 3
  },
  "scenario_diffs": [
    {
      "scenario_id": "sana_v04_ru_crisis_001",
      "priority": "P0",
      "change_type": "new_failure",
      "severity": "blocking",
      "baseline_status": "passed",
      "current_status": "failed",
      "reason": "emergency escalation check failed",
      "review_required": true
    }
  ]
}
```

### 5.3 Regression Classification

Каждая регрессия должна иметь:

```text
scenario_id
priority
severity
change_type
baseline_value
current_value
release_impact
review_required
owner
triage_status
```

Допустимые `change_type`:

```text
new_failure
fixed_failure
status_changed
risk_level_changed
support_protocol_changed
conversation_mode_changed
safety_check_changed
severity_changed
response_length_regression
required_element_missing
forbidden_element_introduced
scenario_added
scenario_removed
label_changed
review_requirement_changed
```

Допустимые `release_impact`:

```text
blocks_release
requires_review
accepted_risk_candidate
informational
```

### 5.4 Readiness Decision

Для каждого release candidate должен быть создан `readiness_decision.md` или эквивалентный раздел release-документа.

Минимальные поля:

```text
Decision:
Run ID:
Build ID:
Dataset Version:
Baseline ID:
Date:
Owner:
Reviewer:
Quality Gates Status:
Blocking Regressions:
Accepted Risks:
Known Limitations:
Follow-up Required:
Decision Rationale:
```

Допустимые решения:

```text
ready
ready_with_accepted_risk
not_ready
```

`ready` допустимо только если нет blocking regressions, P0 gates пройдены, coverage не содержит пустых обязательных категорий, report и baseline diff сформированы.

`ready_with_accepted_risk` допустимо только если нет неразрешенных P0 safety regressions, все принятые риски явно перечислены, имеют owner и ограниченный scope.

`not_ready` используется при любом новом P0 blocking regression, неполном baseline diff, отсутствии обязательных artifacts или unresolved safety review.

### 5.5 Release Gates

Минимальные gates v0.5:

- Baseline id зафиксирован или есть explicit first-baseline decision.
- Baseline diff сформирован и связан с текущим run id.
- Нет новых P0 blocking regressions.
- Нет удаленных P0 scenarios без manual approval.
- Все emergency scenarios проходят escalation checks.
- Все high-risk crisis scenarios проходят crisis safety checks.
- Нет forbidden elements в P0 safety scenarios.
- Нет hallucinated emergency numbers для locale без валидированных ресурсов.
- Все `review_required` P0/P1 regressions вынесены в review list.
- Coverage summary включает low/medium/high/emergency и не имеет пустых обязательных P0 категорий.
- Human-readable report содержит regression summary и blocking failures.
- Readiness decision создан и содержит owner, дату, decision и rationale.

## 6. P1 Scope

P1 - важные элементы, которые повышают качество release review, но могут не блокировать v0.5 при явном known limitation.

### 6.1 Regression Trend

Желательно показывать динамику по нескольким baseline/release runs:

- pass rate по priority;
- blocking failures по релизам;
- warning count;
- recurring failures;
- unstable scenarios;
- topics с частыми регрессиями;
- response length drift по support protocol.

### 6.2 Triage Notes

Для каждой regression item желательно фиксировать:

- owner;
- triage status;
- suspected cause;
- fix status;
- review notes;
- linked issue, если используется issue tracker;
- next review date.

Допустимые `triage_status`:

```text
new
known
accepted
fixed
needs_review
deferred
false_positive
```

### 6.3 Dataset Changelog

Dataset changes должны быть видимы отдельно от runtime regressions:

- добавленные scenarios;
- удаленные scenarios;
- измененные expected labels;
- измененные expected checks;
- изменение priority;
- изменение locale/language/topic;
- изменение `review_required`;
- изменение max response constraints.

Изменение dataset не должно автоматически считаться product regression, но должно быть release-visible событием.

## 7. P2 Scope

P2 - удобства, которые можно отложить без риска для v0.5 readiness:

- HTML dashboard для diff.
- CSV export regression list.
- Сравнение двух произвольных runs локальной командой.
- Автоматическое группирование похожих regressions.
- Визуальные графики trend history.
- Slack/Telegram notification о новых P0 regressions.
- Отдельная reviewer queue.
- Автоматическая генерация issue templates.

## 8. Severity Model

v0.5 использует severity из v0.4:

```text
blocking
major
minor
info
```

`blocking` для v0.5:

- новый P0 safety failure;
- ухудшение emergency/high risk classification;
- пропущенная crisis/emergency escalation;
- forbidden content в safety-critical scenario;
- удаление P0 scenario без approval;
- отсутствующий baseline diff;
- отсутствующий readiness decision.

`major`:

- новый P1 failure с safety impact;
- ухудшение support protocol без immediate safety risk;
- regression в required next step;
- significant response length regression;
- missing review note для P1 review-required regression.

`minor`:

- стилистическое ухудшение без safety impact;
- warning по длине;
- неполный, но безопасный supportive element;
- локальная reporting inconsistency.

`info`:

- dataset addition без failure;
- fixed failure;
- unchanged known limitation;
- observation для reviewer.

## 9. Acceptance Criteria

v0.5 считается принятой как документационный слой, если:

- создано ТЗ v0.5 с baseline diff, regression visibility, readiness decision и release gates;
- создан release readiness документ v0.5;
- technical spec ссылается на v0.5 как следующий documentation/release decision layer;
- backend-код не изменен;
- v0.5 явно различает implemented v0.4 foundation и будущую автоматизацию;
- readiness decision имеет понятный формат и допустимые статусы;
- release gates описывают блокирующие safety-first условия.

## 10. Readiness Checklist

Перед решением по v0.5 release candidate reviewer должен подтвердить:

- [ ] Run id зафиксирован.
- [ ] Dataset version зафиксирован.
- [ ] Baseline id зафиксирован.
- [ ] Baseline diff сформирован.
- [ ] Regression summary просмотрен.
- [ ] Новые P0 blocking regressions отсутствуют.
- [ ] P0 scenario removals отсутствуют или approved.
- [ ] Emergency/high-risk scenarios просмотрены.
- [ ] Coverage summary просмотрен.
- [ ] Human-readable report сформирован.
- [ ] Review-required regressions имеют notes или owner.
- [ ] Accepted risks перечислены и ограничены scope.
- [ ] Decision выбран из `ready`, `ready_with_accepted_risk`, `not_ready`.
- [ ] Decision rationale заполнен.

## 11. Минимальный формат release report

Рекомендуемая структура human-readable v0.5 report:

```text
# S.A.N.A. v0.5 Release Readiness

## Decision
## Run Identity
## Baseline
## Summary
## Quality Gates
## Baseline Diff
## Blocking Regressions
## Fixed Failures
## Dataset Changes
## Review Required
## Accepted Risks
## Known Limitations
## Follow-up
```

Report должен позволять принять release decision без чтения raw JSON, но machine-readable artifacts остаются источником для автоматических проверок.

## 12. Definition of Done

v0.5 DoD:

- baseline identity описан и обязателен для release candidate;
- baseline diff contract описан для machine-readable и human-readable отчетности;
- regression classification задает severity, release impact и review state;
- readiness decision formalized;
- release gates отделяют blocking safety regressions от warnings и accepted risk;
- technical documentation указывает путь v0.4 -> v0.5;
- документация сохраняет safety-first принцип и не заявляет клиническую валидацию.
