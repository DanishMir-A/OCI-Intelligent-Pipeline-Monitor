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
- the recent chat history from the active Streamlit session
- instructions to answer using Oracle-specific operational language

This grounds the response in the current dashboard state and preserves basic multi-turn continuity inside the session.

## Oracle Grounding
The current prototype includes a lightweight Oracle-grounding layer inside `blueverse.py`. It injects curated Oracle documentation snippets into the prompt to simulate how a future Oracle-document retrieval layer would enrich BlueVerse requests.

This allows the current version to demonstrate:
- Oracle-aware GoldenGate troubleshooting context
- Oracle database error handling cues such as `ORA-01438`
- Oracle Data Integrator operational guidance

## Context And Token Discipline
The current implementation uses a token-conscious approach:
- remediation requests send only the selected pipeline, not the full fleet
- support chat sends the fleet telemetry snapshot plus recent chat history
- prompts are compact and task-oriented
- the telemetry payload is limited to the fields already shown in the dashboard
- the BlueVerse client estimates token volume and displays an approximate per-request cost in the UI

The current prototype does not persist token analytics beyond the active session, but the prompt structure is intentionally narrow to control payload size and make per-interaction cost visible during demos.

## Reliability Choices
The BlueVerse client is built with graceful failure handling:
- AI features disable when required secrets are missing
- timeout, connection, and HTTP failures trigger a fallback response path
- malformed or non-JSON responses trigger the same fallback path
- the UI continues to function as an operational dashboard even when the model layer degrades

This keeps the operational dashboard available even when the primary model layer is unavailable.

## Fallback Position
If BlueVerse is unavailable, the client falls back to a mock alternate-provider response path to demonstrate graceful degradation, response continuity, and approximate cost tracking. This is positioned as a prototype fallback mechanism for evaluation rather than a production-approved secondary provider.

## Extension Path
The design leaves room for future enhancements:
- persisted token logging per request
- more accurate provider-specific cost estimation
- approved secondary provider integration
- summarized fleet context for longer chat sessions
- Oracle documentation retrieval backed by a real vector index or governed knowledge store
