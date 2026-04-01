# Codebase Architectural Context

This document explains how the repository is structured so teammates can jump in quickly and understand the flow of the **OCI Intelligent Pipeline Monitor**.

---

## Project Structure

- **`app.py`**: Streamlit entrypoint that renders the dashboard, tabs, and user interactions.
- **`analytics.py`**: Health scoring, risk prediction, and small status-display helpers.
- **`blueverse.py`**: BlueVerse API integration with timeout, HTTP-status, and JSON parsing safeguards.
- **`config.py`**: Safe loading of Streamlit secrets so the app can boot even without AI credentials.
- **`data_sources.py`**: Mock pipeline data plus the placeholder OCI live telemetry hook.
- **`tests/test_analytics.py`**: Regression tests for scoring and predictive heuristics.
- **`requirements.txt`**: Runtime Python dependencies.
- **`.streamlit/config.toml`**: Global light theme configuration.
- **`.streamlit/secrets.toml`**: Local-only BlueVerse credentials and routing details.

---

## Core Components

### 1. Configuration Loading
`config.py` reads BlueVerse settings from Streamlit secrets and returns both the available values and a list of missing keys. This allows the dashboard to render in mock mode even if AI credentials are not configured.

### 2. Data Engine
`data_sources.py` contains two pipeline sources:

- `get_oci_mock_pipelines()` returns the mock dashboard data used for the hackathon experience.
- `get_real_oci_telemetry()` is the future production hook for OCI Monitoring integration. It currently falls back safely when OCI configuration or the SDK is unavailable.

The mock data intentionally includes:
- **Volume anomalies**
- **Latency anomalies**
- **Schema drift**

### 3. BlueVerse Integration
`blueverse.py` connects to the **LTIMindtree BlueVerse GenAI platform**.

When a user generates a remediation or asks a support question, the app:
1. Builds a prompt from the selected pipeline or the full telemetry snapshot.
2. Sends an HTTP POST request to the BlueVerse API.
3. Handles timeouts, HTTP failures, and non-JSON responses without crashing the app.

### 4. Analytics Helpers
`analytics.py` contains:
- `get_status_emoji()`
- `get_health_score()`
- `predict_failure()`

These helpers are now isolated from the UI so they are easier to test and evolve.

### 5. UI Rendering
`app.py` handles the Streamlit layout:
- Sidebar config and telemetry loading
- KPI summary cards
- Fleet overview table and charts
- AI remediation workflow
- Predictive risk view
- Support chat

---

## How To Contribute

If you want to add a new feature:
1. **Add a new chart:** update the relevant tab section in `app.py`.
2. **Change the AI prompts:** edit `build_remediation_prompt()` or `build_chat_prompt()` in `app.py`.
3. **Adjust scoring logic:** update `analytics.py` and extend `tests/test_analytics.py`.
4. **Add a new mock pipeline:** add another dictionary entry in `get_oci_mock_pipelines()` inside `data_sources.py`.
