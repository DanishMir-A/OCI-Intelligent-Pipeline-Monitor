# Mentor Feedback Prep (April 16 to April 20 Submission)

## Meeting Objective
Use the mentor session to convert the current strong prototype into a submission that is:
- technically credible for enterprise adoption,
- aligned to judging criteria,
- realistic and honest about current scope vs. next-step roadmap.

## How To Run The Mentor Meeting (30-40 minutes)

### 1. Context (3 minutes)
- Problem statement: enterprise Oracle pipelines fail due to latency, drift, and operational blind spots.
- Current solution: control tower + AI remediation + governed action path.
- Ask mentor to evaluate technical credibility, feasibility, and scoring strength.

### 2. Live Demo (10 minutes)
- Follow [DEMO_DAY_RUNBOOK.md](./DEMO_DAY_RUNBOOK.md).
- Keep fallback plan ready:
  - BlueVerse strict mode first,
  - fallback mode only if auth fails,
  - mock mode only if live OCI run list is empty.

### 3. Architecture + Code Walkthrough (10-12 minutes)
- UI orchestration and workflows: `app.py`
- Live OCI ingestion and action layer: `data_sources.py`
- AI client behavior and reliability modes: `blueverse.py`
- Health/risk logic: `analytics.py`
- Tests: `tests/test_analytics.py`

### 4. Feedback Capture (10-15 minutes)
- Drive focused discussion with the question bank below.
- End with explicit decision points and ownership.

## What To Ask Mentor (High-Value Question Bank)

## A. OCI Data And Access
1. Which OCI services should be mandatory in the final story: Data Flow only, or Data Flow + Monitoring + Logging?
2. Can we get a stable demo tenancy/compartment with predictable Data Flow runs for final evaluation?
3. Are ODI and GoldenGate live APIs expected for scoring, or is a clear extensibility plan acceptable?
4. What credentials model is preferred for demo: temporary user token vs service principal style access?
5. Do we need explicit network/security notes for enterprise readiness (private endpoints, IAM policy references)?

## B. BlueVerse And AI Integration
1. Should we present strict real-BlueVerse mode as default, with fallback only as controlled continuity mode?
2. Is token-refresh strategy expected in submission docs, or enough to describe current auth handling and next steps?
3. Do judges prefer deeper prompt/cost reporting in UI, or current concise token/cost display?
4. Is lightweight Oracle grounding sufficient, or do we need to prioritize a true RAG implementation before April 20?

## C. Enterprise Feasibility
1. Is the current governed action (approval + audit + rerun) strong enough for enterprise story?
2. What additional control is highest impact before submission:
   - role-based action guardrails,
   - stronger action logging,
   - rollback/verification panel,
   - deployment hardening notes?
3. Which risk should we address first to maximize score impact?

## D. Submission Strategy
1. Which 2-3 strengths should we emphasize most in final narrative?
2. Which limitations must be explicitly documented to stay credible?
3. For judging, should we optimize for live-path demonstration or reliable mock-path with stronger explanation?

## How To Explain Code And Tech Stack To Mentor

## 1. Architecture In One Minute
- Streamlit control tower orchestrates telemetry, AI, prediction, and actions.
- Telemetry normalizes into one pipeline schema used across all tabs.
- AI consumes selected context (pipeline or fleet) for grounded outputs.
- Action layer executes controlled operations (currently OCI Data Flow rerun) with audit trace.

## 2. File-Level Explanation
- `app.py`:
  - UI tabs, sidebar config, session state, and enterprise action controls.
  - strict BlueVerse mode vs optional fallback mode.
- `data_sources.py`:
  - mock data model,
  - live OCI Data Flow run discovery,
  - pipeline schema mapping,
  - live rerun API call.
- `blueverse.py`:
  - BlueVerse request builder,
  - payload parsing,
  - explicit error diagnostics,
  - optional fallback behavior.
- `analytics.py`:
  - deterministic health score and risk heuristics for explainability.
- `tests/test_analytics.py`:
  - regression tests for scoring and Oracle scenario behavior.

## 3. Tech Stack Summary
- Frontend + app runtime: `Streamlit`
- Visualization: `Plotly`, `Pandas`
- AI integration: `BlueVerse API via requests`
- Cloud integration: `OCI Python SDK (Data Flow)`
- Logic/testing: pure Python + `pytest`

## How To Present Feasibility (Without Overclaiming)
- Implemented now:
  - live OCI Data Flow telemetry ingestion,
  - real BlueVerse integration mode,
  - governed live rerun action with audit trail.
- Not fully implemented yet:
  - live ODI/GoldenGate collectors,
  - full OCI Monitoring + Logging ingestion pipeline,
  - production-grade auth/token lifecycle automation.
- Positioning:
  - "working enterprise foundation with one live OCI vertical implemented end-to-end, and a clear extension architecture."

## Meeting Notes Template
Use this template during mentor discussion:

```text
Mentor feedback date:
Top 3 strengths:
Top 3 risks:
Must-fix before Apr 20:
Nice-to-have if time permits:
Demo storyline changes:
Documentation changes:
Owner / ETA:
```

## Execution Plan (Post-Meeting to April 20)

### Day 1 (Immediately after mentor call)
- Lock final demo storyline.
- Apply must-fix architecture/code/docs updates only.
- Update docs with mentor-approved claims and scope boundaries.

### Day 2
- Full rehearsal of primary and fallback demo paths.
- Capture final screenshots/evidence for docs.
- Validate BlueVerse and OCI credentials on final demo environment.

### Day 3 (Submission day)
- Final sanity test.
- Final repo/doc check.
- Submission mail/package dispatch.

## Non-Negotiable Checks Before Final Submission
1. BlueVerse auth works in strict mode.
2. At least one live OCI Data Flow pipeline appears in live mode.
3. Governed rerun action produces request metadata in audit trail.
4. Docs match actual implemented behavior (no overclaims).
5. Demo backup path rehearsed once end-to-end.
