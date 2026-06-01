# Architecture

S.A.N.A. starts as a modular safety-first assistant. The early prototype can use simple deterministic logic, then evolve toward specialized models and fine-tuning.

## Request Flow

```text
User message
  -> Input normalization
  -> Risk classifier with feature scoring
  -> Conversation policy router
  -> Response generator
  -> Safety checker
  -> Final answer
```

## Modules

- `risk_classifier`: estimates emotional and safety risk.
- `policy_router`: selects support, deep support, minor support, crisis, or emergency mode.
- `response_generator`: creates the assistant response according to the selected mode.
- `safety_checker`: blocks unsafe claims, diagnoses, medication advice, and weak crisis handling.
- `resource_recommender`: later provides localized professional and emergency resources.

## Current Prototype Response Contract

The chat endpoint returns:

```text
risk_level          low | medium | high | emergency
risk_score          numeric score from 0 to 1
conversation_mode   selected dialog policy
risk_assessment     features, matched terms, and rationale
safety_check        final validation result
response            safe user-facing answer
```

## Training Path

1. Start with expert-written behavior rules and test scenarios.
2. Build a synthetic dataset of safe and unsafe support dialogs.
3. Add clinician or psychologist review.
4. Fine-tune an open-source model with LoRA or QLoRA.
5. Add preference evaluation and regression testing.

## Prototype Stack

- Python
- FastAPI
- Pydantic
- PostgreSQL later for accounts and sessions
- Redis later for queues and short-term state
- Qdrant later for retrieval over vetted support materials
