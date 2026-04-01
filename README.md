# ☁️ OCI Intelligent Data Pipeline Monitoring

An Enterprise AI application built for the **Oracle Pythia-26 AI Infusion Hackathon**. 

This repository contains a **Data Fabric Control Tower** that monitors Oracle Cloud Infrastructure (OCI) data pipelines—specifically **Oracle Data Integration (ODI), GoldenGate, and OCI Data Flow**. It tracks real-time anomalies such as *schema drift*, *latency spikes*, and *volume drops*. 

When an anomaly is detected, the **LTIMindtree BlueVerse AI Agent** determines the root cause and automatically generates an **Auto-Remediation Script** (SQL, Python, or OCI CLI snippet) to reduce Mean Time To Resolution (MTTR) by 60%.

---

## 🚀 Features
- **Fleet Overview**: High-end standard `Plotly` dashboard tracking massive volume and latency anomalies across 8 simulated OCI Enterprise pipelines.
- **AI Auto-Remediation Copilot**: Instructs a large language model to write specific fix-scripts for failing Oracle integrations.
- **Predictive Prevention**: Scores system health and forecasts system breakage before total outage.
- **AI Support Chat**: Provides conversational AI assistance analyzing live JSON telemetry data.

---

## 🛠️ Local Setup Instructions

Follow these instructions to run the application on your own machine.

### 1. Prerequisites
- [Python 3.9+](https://www.python.org/downloads/) must be installed on your machine.
- Ensure `pip` is available in your PATH.

### 2. Create a Virtual Environment
It is recommended to use a virtual environment to manage dependencies. Open your terminal (or VS Code terminal) in this directory and run:

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
Once your virtual environment is activated, install the required libraries:

```bash
pip install -r requirements.txt
```

### 4. Run the Application
Start the Streamlit web server:

```bash
streamlit run app.py
```

Your browser should automatically open `http://localhost:8501` showcasing the gorgeous light-themed OCI Control Tower.

---

## 💡 About 
- **Developer:** Danish Mir (Zero)
- **Hackathon:** Pythia-26 Oracle AI Infusion
- **Tech Stack:** Python, Streamlit, Plotly, OCI Telemetry (Mocked), LTIMindtree BlueVerse API (Claude).
