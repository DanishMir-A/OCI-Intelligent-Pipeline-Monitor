# OCI Intelligent Data Pipeline Monitoring

[![Live Demo On Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://oci-intelligent-pipeline-monitor.streamlit.app/)

An enterprise AI application built for the **Oracle Pythia-26 AI Infusion Hackathon**.

This repository contains a **Data Fabric Control Tower** that monitors Oracle Cloud Infrastructure (OCI) data pipelines, specifically **Oracle Data Integration (ODI), GoldenGate, and OCI Data Flow**. It tracks anomalies such as *schema drift*, *latency spikes*, and *volume drops*.

When an anomaly is detected, the **LTIMindtree BlueVerse AI Agent** can generate an **auto-remediation script** (SQL, Python, or OCI CLI snippet) to help reduce Mean Time To Resolution (MTTR).

---

## Features
- **Fleet Overview**: Plotly dashboard tracking throughput/executor and latency anomalies across Oracle-shaped enterprise pipelines.
- **AI Auto-Remediation Copilot**: Prompts BlueVerse to generate root-cause analysis and fix scripts for failing Oracle integrations.
- **Predictive Prevention**: Uses local heuristic scoring to highlight pipelines trending toward failure.
- **AI Support Chat**: Provides conversational assistance over the current pipeline telemetry snapshot.
- **Live OCI Data Flow Telemetry**: Reads live Data Flow run signals for a configured OCI compartment.
- **Governed Live Action**: Approval-gated OCI Data Flow rerun with operator justification and audit trail.
- **Graceful Fallbacks**: The dashboard still runs in mock mode when BlueVerse or live OCI telemetry are unavailable.

---

## Local Setup Instructions

### 1. Prerequisites
- [Python 3.9+](https://www.python.org/downloads/) installed locally
- `pip` available in your PATH

### 2. Create a Virtual Environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Runtime Requirements
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets for BlueVerse
Because the AI remediation and chat features connect to LTIMindtree BlueVerse, configure credentials locally:

1. Inside the `.streamlit/` folder, find `secrets.toml.example`.
2. Copy or rename it to `secrets.toml`.
3. Fill in your real values:

```toml
BEARER_TOKEN = "your_actual_long_jwt_token_here"
API_URL = "https://blueverse-foundry.ltimindtree.com/chatservice/chat"
SPACE_NAME = "your_space_name"
FLOW_ID = "your_flow_id"
```

`secrets.toml` is ignored by Git and should stay local.

The app also supports environment variables in deployment environments:

```bash
BEARER_TOKEN=...
API_URL=https://blueverse-foundry.ltimindtree.com/chatservice/chat
SPACE_NAME=...
FLOW_ID=...
```

### 5. Run the Application
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### 6. Run Tests
Install `pytest` if needed, then run:

```bash
pip install pytest
pytest
```

### 7. Optional Live OCI Integration
The "Live OCI Telemetry Mode" now supports a live vertical for OCI Data Flow runs. Use the sidebar `Connect To OCI` panel and provide either:
- OCI config file path (+ optional profile), or
- inline OCI credentials (tenancy/user/fingerprint/region/key path),

plus `Compartment OCID` for run discovery.

---

## Container Deployment (Docker)

Build image:

```bash
docker build -t oci-pipeline-monitor:latest .
```

Run container:

```bash
docker run --rm -p 8501:8501 \
  -e BEARER_TOKEN="..." \
  -e API_URL="https://blueverse-foundry.ltimindtree.com/chatservice/chat" \
  -e SPACE_NAME="..." \
  -e FLOW_ID="..." \
  oci-pipeline-monitor:latest
```

Then open `http://localhost:8501`.

---

## Project Structure
- `app.py`: Streamlit entrypoint and page layout
- `analytics.py`: Health scoring and prediction helpers
- `blueverse.py`: BlueVerse API client with error handling
- `config.py`: Loading of Streamlit secrets and env var fallback
- `data_sources.py`: Mock pipeline loader, live OCI Data Flow telemetry ingestion, and governed live rerun action
- `data/mock_pipelines.json`: Externalized mock pipeline dataset
- `tests/test_analytics.py`: Tests for scoring and predictive logic

## Submission Docs
The repo includes a reviewer-facing `docs/` package for the submission:
- `docs/SUBMISSION_INDEX.md`
- `docs/DESIGN_DOCUMENT.md`
- `docs/ARCHITECTURE_DIAGRAM.md`
- `docs/DEPLOYMENT_GUIDE.md`
- `docs/BLUEVERSE_STRATEGY.md`
- `docs/TEST_PLAN.md`
- `docs/TEST_RESULTS.md`
- `docs/DATA_SOURCES_AND_ASSUMPTIONS.md`
- `docs/KNOWN_LIMITATIONS.md`

Internal team-only preparation notes are intentionally kept outside the public documentation set.

---

## About
- **Developer:** Danish Mir (Zero)
- **Hackathon:** Pythia-26 Oracle AI Infusion
- **Tech Stack:** Python, Streamlit, Plotly, OCI telemetry (mocked), LTIMindtree BlueVerse API
