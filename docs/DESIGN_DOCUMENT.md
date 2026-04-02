# Design Document

## Solution Summary
**OCI Intelligent Data Pipeline Monitoring** is an Oracle-focused operations dashboard that monitors integration health across ODI, GoldenGate, and OCI Data Flow. The solution combines telemetry visibility, anomaly prioritization, and BlueVerse-guided remediation in one control surface so engineers can move from detection to action faster.

## Problem
Oracle enterprise estates often run multiple data movement technologies at the same time. When issues appear, teams must quickly determine whether the problem is caused by latency spikes, throughput drops, schema drift, or target-side instability. In practice, that investigation is spread across dashboards, logs, and tribal knowledge, which increases Mean Time To Resolution and slows business operations.

## Proposed Solution
The project provides a lightweight but extensible control tower that:
- shows fleet-wide pipeline status in one interface
- computes health and risk using local heuristics
- highlights likely intervention priorities
- uses BlueVerse to generate Oracle-specific remediation guidance
- keeps the dashboard usable even when secrets or live OCI telemetry are unavailable

## Oracle Context
The prototype is grounded in Oracle-specific integration patterns rather than generic ETL monitoring. It references:
- Oracle Data Integration (ODI)
- Oracle GoldenGate
- OCI Data Flow
- Oracle ADW and Oracle cloud application targets
- enterprise sources such as ERP, CRM, HCM, SCM, and E-Business Suite style systems

This framing makes the remediation prompts and operational language more relevant to Oracle data engineering teams and leaves a clear path to support broader Oracle product families such as Fusion, JDE, EBS, and EPM.

## Architecture
The application is modularized into focused components:
- `app.py`: Streamlit user interface, prompt construction, and workflow orchestration
- `data_sources.py`: mock telemetry and the future OCI Monitoring integration hook
- `analytics.py`: health scoring and predictive heuristics
- `blueverse.py`: BlueVerse API integration with reliability safeguards
- `config.py`: secrets loading with graceful degradation
- `tests/test_analytics.py`: regression tests for the scoring layer

At runtime, the app loads telemetry, derives health and risk signals, renders dashboard views, and optionally sends structured context to BlueVerse for remediation or support-chat responses.

## BlueVerse Integration
BlueVerse is integrated directly into two operator workflows:
- **AI Auto-Remediation** for a selected anomalous pipeline
- **Support AI Chat** for telemetry-aware troubleshooting questions

The integration is built with demo-safe reliability choices:
- credentials are externalized through Streamlit secrets
- AI features disable cleanly if secrets are unavailable
- timeout, HTTP failure, and malformed-response handling are implemented in the client layer

## User Experience
The interface is designed as a command-surface dashboard with:
- a fleet health summary
- status-oriented KPI cards
- telemetry tables and charts
- guided remediation context
- predictive prioritization views
- an operator chat panel

This structure helps judges and operators understand the operational story quickly during a short demo.

## Business Impact
The project is aimed at improving:
- incident triage speed
- root-cause discovery time
- operator efficiency
- visibility into pipeline health across Oracle technologies

The strongest KPI story for the prototype is reduced investigation effort. Instead of separately interpreting latency, throughput, and schema signals, an engineer can review one dashboard, identify the most critical pipeline, and immediately invoke BlueVerse-assisted remediation.

## Scalability Direction
Although the current version is a hackathon prototype, the architecture is already structured for extension:
- swap mock telemetry for OCI Monitoring mappings
- introduce richer Oracle documentation context
- add token and cost logging
- expand to more Oracle product families and client-specific data sources
- host the application in a managed environment with externalized secrets

## Conclusion
This project demonstrates a practical Oracle-centric monitoring assistant with a clean demo experience, modular code structure, and a credible path toward production telemetry integration. The core value is not only anomaly display, but the combination of detection, prioritization, and AI-assisted remediation in a single workflow.
