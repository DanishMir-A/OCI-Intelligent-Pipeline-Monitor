# Deployment Guide

## Local Deployment

### Prerequisites
- Python 3.9+
- `pip`
- network access for BlueVerse API calls when AI features are enabled

### Setup
```powershell
cd "C:\Users\Danish Farooq\Documents\Oracle_Hackathon"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

If `python` is not available on PATH:

```powershell
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### BlueVerse Configuration
Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example` and populate:

```toml
BEARER_TOKEN = "your bearer token"
API_URL = "https://blueverse-foundry.ltimindtree.com/chatservice/chat"
SPACE_NAME = "your_space_name_here"
FLOW_ID = "your_flow_id_here"
```

### Start The App
```powershell
streamlit run app.py
```

The local dashboard opens at:
`http://localhost:8501`

## Runtime Behavior
- When BlueVerse secrets are present, remediation and chat workflows are enabled.
- When BlueVerse secrets are missing, the dashboard remains available and AI features disable gracefully.
- When live OCI telemetry is unavailable, the application falls back to the mock telemetry dataset.

## Hosted Deployment
The application is compatible with a hosted Streamlit deployment. A standard hosted setup uses:
1. the GitHub repository as the source
2. `app.py` as the entrypoint
3. hosted secrets configuration for BlueVerse values
4. optional OCI credentials if live telemetry is implemented later

## Environment Model

### Development
- local Python runtime
- local Streamlit secrets file
- mock telemetry by default

### Demo
- hosted or local Streamlit app
- validated BlueVerse credentials
- stable demo dataset and scenarios

### Production Direction
- OCI Monitoring ingestion
- centralized secret management
- request logging, token tracking, and operational monitoring

## Troubleshooting
- If the app does not start, confirm Python and dependencies are installed.
- If AI features are disabled, confirm `.streamlit/secrets.toml` exists and includes all required keys.
- If live mode shows mock data, OCI ingestion is either unavailable or not yet implemented.
- If BlueVerse requests fail, confirm the bearer token, API URL, space name, and flow ID.
