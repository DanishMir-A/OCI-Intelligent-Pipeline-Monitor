# BlueVerse Strategy

## Integration Role
BlueVerse is the primary LLM layer for this solution and is embedded in two operator workflows:
- remediation generation for a selected anomalous pipeline
- support chat over the current telemetry snapshot

The goal is not to add a generic chatbot, but to give the operator an Oracle-aware assistant that works from structured pipeline context.

## Prompt Design
The prompts are intentionally constrained.

### Remediation Workflow
For remediation generation, the app sends:
- the selected pipeline as structured JSON
- the anomaly context
- instructions to produce an Oracle-specific root-cause hypothesis
- instructions to produce actionable remediation steps and code

This keeps the model focused on operational diagnosis rather than generic explanation.

### Support Chat Workflow
For support chat, the app sends:
- the current telemetry snapshot
- the user’s question
- instructions to answer using Oracle-specific operational language

This grounds the response in the current dashboard state rather than free-form speculation.

## Context And Token Discipline
The current implementation uses a token-conscious approach:
- remediation requests send only the selected pipeline, not the full fleet
- prompts are compact and task-oriented
- the telemetry payload is limited to the fields already shown in the dashboard
- Streamlit session state preserves chat history on the UI side without embedding unnecessary extra context in the client layer

The current prototype does not yet persist token usage metrics, but the prompt structure is intentionally narrow to control payload size.

## Reliability Choices
The BlueVerse client is built with graceful failure handling:
- AI features disable when required secrets are missing
- timeout handling returns a readable message
- HTTP failures return a readable message
- malformed or non-JSON responses return a readable message

This keeps the operational dashboard available even when the model layer is unavailable.

## Current Fallback Position
The current implementation supports graceful degradation rather than a second active model provider. If BlueVerse is unavailable, the system remains usable as a monitoring dashboard, but AI remediation and chat are disabled. That tradeoff is explicit and preferable to silently returning untrusted responses from an unconfigured fallback.

## Extension Path
The design leaves room for future enhancements:
- token logging per request
- per-interaction cost estimation
- alternate approved LLM provider
- summarized fleet context for longer chat sessions
- Oracle documentation retrieval for richer grounding
