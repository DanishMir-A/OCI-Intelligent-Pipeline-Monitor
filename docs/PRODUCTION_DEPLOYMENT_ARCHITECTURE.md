# Production Deployment Architecture

## Current Production-Feasible Shape
The current implementation is suitable as an enterprise pilot architecture with a live OCI Data Flow vertical:
- operator UI in Streamlit,
- live OCI Data Flow telemetry read path,
- AI remediation and chat via BlueVerse,
- approval-gated live rerun action with audit visibility.

## Recommended Target Deployment On OCI

## 1. Presentation Layer
- Internal Streamlit UI container (private network/VPN access).
- Purpose: operator workflows, triage, RCA viewing, governed action trigger.

## 2. API/Orchestration Layer
- Python service (FastAPI/Flask) for:
  - telemetry normalization,
  - BlueVerse prompt orchestration,
  - action policy checks.
- Keeps business logic out of UI runtime for scale and governance.

## 3. Telemetry Layer
- Current live source: OCI Data Flow runs.
- Planned additions:
  - OCI Monitoring metrics,
  - OCI Logging/Logging Analytics,
  - ODI and GoldenGate collectors.

## 4. Action Layer
- Controlled action endpoints (currently Data Flow rerun).
- Mandatory controls:
  - operator approval,
  - change justification,
  - audit entry and request metadata capture.

## 5. Data Layer
- Persist telemetry snapshots and action logs in a durable store (ADW/Postgres/Object Storage).
- Enables historical trend analysis, compliance reports, and incident traceability.

## 6. Security Layer
- OCI IAM policies and least-privilege service access.
- OCI Vault for secrets and token material.
- No static credentials in source repository.

## 7. Operations Layer
- OCI Logging/APM for runtime observability.
- Alert routing for AI/API/action failures.
- CI/CD with environment promotion gates (dev -> stage -> prod).

## Deployment Options

## Option A: OCI Container Instances (Fastest pilot)
- Streamlit container + API container + managed database.
- Good for hackathon and near-term pilot.

## Option B: OCI OKE (Kubernetes, enterprise scale)
- Better for multi-service scaling, policy control, and enterprise operations.

## Current Scope vs Production Scope

## Implemented Now
- Live Data Flow telemetry ingestion.
- BlueVerse strict/fallback modes.
- Approval-gated Data Flow rerun + audit trail.
- Token/cost visibility per interaction.

## Planned For Full Production
- Multi-source live telemetry (Monitoring/Logging/ODI/GoldenGate).
- Persisted token/cost and action analytics.
- Service separation with API layer and durable storage.
- Full security hardening and policy automation.
