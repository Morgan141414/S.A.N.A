# Architecture

S.A.N.A. starts as a modular safety-first assistant. The early prototype can use simple deterministic logic, then evolve toward specialized models and fine-tuning.

## Request Flow

```text
User message
  -> Input normalization
  -> Risk classifier with feature scoring
  -> Conversation policy router
  -> Support protocol selector
  -> Response generator
  -> Safety checker
  -> Final answer
```

## Modules

- `risk_classifier`: estimates emotional and safety risk.
- `policy_router`: selects support, deep support, minor support, crisis, or emergency mode.
- `support_protocols`: selects the response protocol used by v0.2.
- `support_response`: creates the assistant response according to the selected mode.
- `safety_checker`: blocks unsafe claims, diagnoses, medication advice, and weak crisis handling.
- `response_quality`: validates empathy, next step, protocol-specific requirements, and crisis length.
- `llm_providers`: optional local or external LLM adapters behind the guarded response contract.
- `resource_recommender`: later provides localized professional and emergency resources.

## Conversation Modes

```text
support        ordinary emotional support
deep_support   stronger support with cautious diagnostic hypotheses
minor_support  age-aware support for minors when risk is not high
minor_safety   minor safety support for abuse, exploitation, or unsafe home signs
crisis         high-risk support with an explicit safety step
emergency      immediate danger protocol
```

## Support Protocols

```text
general_support      ordinary support when no specialized protocol is selected
depressive_support   possible depressive signs, low energy, hopelessness
anxiety_grounding    anxiety, worry, sleep disruption, anxious predictions
panic_grounding      panic-like body activation and grounding
grief_loneliness     grief, separation, loneliness, loss
conflict_stress      conflict, work stress, burnout-like pressure
minor_support        age-aware support for minors
minor_safety         abuse, exploitation, or unsafe home signs for minors
crisis               high-risk crisis support
emergency            immediate danger protocol
```

## Current Prototype Response Contract

The chat endpoint returns:

```text
risk_level          low | medium | high | emergency
risk_score          numeric score from 0 to 1
conversation_mode   selected dialog policy
support_protocol    selected v0.2 support protocol
risk_assessment     features, matched terms, and rationale
safety_check        final validation result
quality_check       v0.2 response quality result
response            safe user-facing answer
```

## Training Path

1. Start with expert-written behavior rules and test scenarios.
2. Build a synthetic dataset of safe and unsafe support dialogs.
3. Add clinician or psychologist review.
4. Fine-tune an open-source model with LoRA or QLoRA.
5. Add preference evaluation and regression testing.

## Local LLM Runtime

The current local path uses an Ollama-compatible provider. It is disabled by default and can be enabled only through environment variables.

Safety boundaries:

- local LLM is only a candidate generator;
- final output still passes safety and quality checks;
- minors, crisis, emergency, and high-risk flows stay deterministic;
- Ollama URL defaults to loopback-only;
- private network Ollama endpoints require an explicit opt-in flag;
- public remote Ollama URLs are rejected.

Runtime budgets:

```text
SANA_LLM_TIMEOUT_SECONDS
SANA_LLM_MAX_OUTPUT_CHARS
SANA_OLLAMA_NUM_PREDICT
```

Manual smoke runs perform a local provider preflight before generation:

```text
GET /api/tags
  -> endpoint reachable?
  -> configured model present?
  -> allow synthetic smoke generation
```

If preflight fails, smoke exits before any generation call.

Provider failures are normalized into safe internal reasons before fallback:

```text
llm_provider_timeout
llm_provider_http_error
llm_provider_connection_error
llm_provider_invalid_json
ollama_response_must_be_object
ollama_response_must_be_string
llm_provider_error
```

These reasons are diagnostic metadata, not user-facing raw errors.

LLM smoke reports aggregate the guarded response outcomes:

```text
candidate_used_count
fallback_count
blocked_reasons
```

This lets reviewers compare local models by safety and usefulness before any real-user testing.

The local model selection process is manual and staged:

```text
local runtime setup
  -> model pull
  -> provider preflight
  -> gated synthetic smoke
  -> smoke report summary
  -> model comparison matrix
  -> reviewer decision
```

No model moves to expanded synthetic/red-team tests until the comparison matrix records an explicit reviewer decision.

## Prototype Stack

- Python
- FastAPI
- Pydantic
- PostgreSQL later for accounts and sessions
- Redis later for queues and short-term state
- Qdrant later for retrieval over vetted support materials
