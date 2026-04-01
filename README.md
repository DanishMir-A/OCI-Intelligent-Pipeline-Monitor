# OCI Intelligent Data Pipeline Monitoring

[![Live Demo On Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://oci-intelligent-pipeline-monitor.streamlit.app/)

An enterprise AI application built for the **Oracle Pythia-26 AI Infusion Hackathon**.

This repository contains a **Data Fabric Control Tower** that monitors Oracle Cloud Infrastructure (OCI) data pipelines, specifically **Oracle Data Integration (ODI), GoldenGate, and OCI Data Flow**. It tracks anomalies such as *schema drift*, *latency spikes*, and *volume drops*.

When an anomaly is detected, the **LTIMindtree BlueVerse AI Agent** can generate an **auto-remediation script** (SQL, Python, or OCI CLI snippet) to help reduce Mean Time To Resolution (MTTR).

---

## Features
- **Fleet Overview**: Plotly dashboard tracking volume and latency anomalies across 8 simulated OCI enterprise pipelines.
- **AI Auto-Remediation Copilot**: Prompts BlueVerse to generate root-cause analysis and fix scripts for failing Oracle integrations.
- **Predictive Prevention**: Uses local heuristic scoring to highlight pipelines trending toward failure.
- **AI Support Chat**: Provides conversational assistance over the current pipeline telemetry snapshot.
- **Graceful Fallbacks**: The dashboard still runs in mock mode when BlueVerse secrets or live OCI telemetry are unavailable.

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
The "Live OCI Telemetry Mode" toggle is still a production placeholder. If you want to build that path out locally, install the OCI SDK separately:

```bash
pip install oci
```

---

## Project Structure
- `app.py`: Streamlit entrypoint and page layout
- `analytics.py`: Health scoring and prediction helpers
- `blueverse.py`: BlueVerse API client with error handling
- `config.py`: Optional loading of Streamlit secrets
- `data_sources.py`: Mock pipeline data and OCI live telemetry placeholder
- `tests/test_analytics.py`: Tests for scoring and predictive logic

---

## About
- **Developer:** Danish Mir (Zero)
- **Hackathon:** Pythia-26 Oracle AI Infusion
- **Tech Stack:** Python, Streamlit, Plotly, OCI telemetry (mocked), LTIMindtree BlueVerse API
