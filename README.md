# S.A.N.A.

**S.A.N.A. - Supportive Adaptive Neuro Assistant**

S.A.N.A. is an AI-assisted mental and emotional support system. Its purpose is to listen carefully, offer structured support, detect risk signals, and guide people toward safe next steps.

S.A.N.A. is not a replacement for licensed medical, psychological, psychiatric, emergency, or crisis care. The system is designed to support people, not to diagnose, prescribe medication, or handle life-threatening situations alone.

## Initial Goals

- Provide warm, professional, psychologically informed support.
- Detect possible signs of emotional distress, depression, anxiety, crisis, and self-harm risk.
- Use safe escalation flows for urgent and high-risk situations.
- Support multiple age groups with age-appropriate language and safeguards.
- Build a reliable foundation for future model training and evaluation.

## Project Structure

```text
backend/        FastAPI service and safety pipeline
docs/           Product, clinical behavior, and architecture notes
```

## Core Documents

- [Technical specification](docs/technical_spec_ru.md)
- [Clinical behavior specification](docs/clinical_behavior_spec.md)
- [Architecture](docs/architecture.md)
- [Development process](docs/development_process_ru.md)
- [Automation process](docs/automation_process_ru.md)
- [v0.1 readiness checklist](docs/v0_1_readiness_ru.md)
- [v0.1 release readiness](docs/release_v0_1_ru.md)
- [v0.2 specification](docs/v0_2_spec_ru.md)
- [v0.2 release readiness](docs/release_v0_2_ru.md)
- [v0.3 specification](docs/v0_3_spec_ru.md)
- [Data strategy](docs/data_strategy_ru.md)
- [Evaluation plan](docs/evaluation_plan_ru.md)
- [v0.3 release readiness](docs/release_v0_3_ru.md)
- [v0.4 specification](docs/v0_4_spec_ru.md)
- [v0.4 release readiness](docs/release_v0_4_ru.md)
- [v1.0 local LLM runtime guardrails](docs/v1_0_spec_ru.md)
- [v1.0 release readiness](docs/release_v1_0_ru.md)

## First Milestone

The first milestone is a safe prototype:

1. Accept a user message.
2. Classify the emotional risk level.
3. Generate a supportive response according to safety rules.
4. Run a final safety check before returning the answer.

## Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Quality Gate

Run all local checks before committing:

```bash
make check
```

This installs backend development dependencies, runs Ruff, and runs pytest.

Run the full development cycle and generate a quality report:

```bash
make dev-cycle
```

Run the v0.3 evaluation gate:

```bash
make evaluate
```

Generate an evaluation report:

```bash
make evaluate-report
```
