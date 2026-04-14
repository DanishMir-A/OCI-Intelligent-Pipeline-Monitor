# Demo Day Runbook

## Objective
Show a credible enterprise operations flow:
1. detect pipeline risk,
2. diagnose with AI,
3. execute a governed action,
4. confirm operational recovery signals.

The strongest story in the current build is:
- live OCI Data Flow telemetry ingestion,
- BlueVerse-assisted remediation and chat,
- approval-gated live rerun action with audit trail.

## Pre-Demo Checks (15-20 minutes before)
1. Confirm Streamlit app is reachable and loads all tabs.
2. Confirm BlueVerse auth is valid:
   - `Use offline AI fallback` should be `False`.
   - Generate one remediation response and one chat response.
3. Confirm OCI live mode:
   - `Live OCI Telemetry Mode` = `On`.
   - `Connect To OCI` has valid credentials plus `Compartment OCID`.
   - At least one real OCI Data Flow pipeline appears in Fleet Overview.
4. Confirm live action path:
   - open a live OCI Data Flow pipeline in `AI Auto-Remediation`,
   - check approval box,
   - run `Execute Live OCI Rerun`,
   - verify audit log shows `Run ID` and `Request ID`.

## Demo Flow (8-10 minutes)

### 0:00 - 1:00 | Opening
- Introduce the problem: enterprise Oracle pipelines fail due to lag, schema drift, and latency.
- Position the app as an OCI operations control tower with AI-assisted MTTR reduction.

### 1:00 - 3:00 | Fleet Telemetry
- Show `Fleet Overview`.
- Highlight risk visibility:
  - status distribution,
  - latency deviation chart,
  - metric chart (throughput in mock mode, executor allocation in live Data Flow mode).

### 3:00 - 5:30 | AI Root Cause + Fix
- Open `AI Auto-Remediation`.
- Select a degraded/failed pipeline.
- Click `Generate AI Root Cause & Fix`.
- Explain structured output:
  - root-cause hypothesis,
  - actionable fix steps,
  - copy-ready SQL/CLI/script snippets.

### 5:30 - 7:30 | Governed Action (Enterprise Control)
- In `Enterprise Action Control`, enter change justification.
- Check approval gate checkbox.
- Click `Execute Live OCI Rerun` (live mode) or `Apply Fix To Pipeline` (mock mode).
- Show `Operator Action Audit Trail` entry with timestamps and IDs.

### 7:30 - 9:00 | Predictive + Chat
- Open `Predict & Prevent` and show risk prioritization.
- Open `Support AI Chat` and ask one operations question tied to the selected pipeline.

### 9:00 - 10:00 | Close
- Summarize business value:
  - faster triage,
  - guided remediation,
  - governed action trail.
- State extension path:
  - add OCI Monitoring, ODI, and GoldenGate collectors to the same schema.

## Fallback Plan (If Anything Breaks Live)
1. If BlueVerse returns auth error:
   - quickly enable `Use offline AI fallback`,
   - continue RCA/fix demonstration using fallback path.
2. If live OCI has no runs in compartment:
   - switch to mock mode,
   - demonstrate complete flow including `Apply Fix To Pipeline`.
3. If action API fails:
   - show that failure is captured in audit trail,
   - explain governance and error visibility as an enterprise control requirement.

## Judge Q&A Cheat Sheet

### Q: Is this enterprise-feasible or just a dashboard?
A: It supports both observation and governed action. The current build includes live OCI Data Flow telemetry ingestion and approval-gated rerun execution with audit traceability.

### Q: Is AI grounded or generic?
A: AI prompts are grounded with structured pipeline context. Remediation uses selected-pipeline context, while chat uses fleet snapshot plus session conversation history.

### Q: Can this scale across Oracle products?
A: Yes. The app already normalizes telemetry into a common schema and can add connectors for OCI Monitoring, ODI, GoldenGate, and other Oracle services without changing the control-tower UX.

### Q: What about reliability if BlueVerse is down?
A: There is explicit strict mode for real BlueVerse responses and optional fallback mode for continuity. Failures are surfaced clearly and do not take down the telemetry dashboard.

### Q: Is there governance for actions?
A: Yes. Live action is approval-gated with required justification and an audit log that captures status, timestamp, and OCI request metadata.

## Final Checklist Before Joining Demo
1. Browser tab ready at Fleet Overview.
2. BlueVerse token confirmed valid today.
3. OCI credentials and compartment saved in sidebar.
4. One known pipeline selected for remediation.
5. One known chat question prepared.
6. Backup mode rehearsed once.
