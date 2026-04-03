from datetime import datetime

import streamlit as st

try:
    import oci
except ImportError:
    oci = None


def get_real_oci_telemetry():
    """
    Production placeholder for OCI Monitoring integration.
    Returns None when live telemetry is unavailable so the UI can fall back safely.
    """
    if not oci:
        return None

    try:
        config = oci.config.from_file()
        oci.monitoring.MonitoringClient(config)

        # Future implementation:
        # response = monitoring_client.summarize_metrics_data(...)
        # return map_response_to_pipeline_records(response)
        return None
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_oci_mock_pipelines():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        {
            "pipeline_name": "gg_fin_ledger_sync",
            "type": "GoldenGate",
            "source": "E-Business Suite 12.2",
            "target": "OCI Autonomous Data Warehouse (ADW)",
            "status": "FAILED",
            "expected_rows": 850000,
            "actual_rows": 512000,
            "duration_minutes": 240,
            "avg_duration_minutes": 8,
            "anomaly_detected": "Extract Abend & Giant LAG",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_sales_crm_daily",
            "type": "ODI 12c",
            "source": "Fusion Sales Cloud",
            "target": "Oracle Retail Data Store",
            "status": "FAILED",
            "expected_rows": 45000,
            "actual_rows": 0,
            "duration_minutes": 18,
            "avg_duration_minutes": 15,
            "anomaly_detected": "Schema Drift & ORA-00904",
            "schema_changes": [
                "OPPORTUNITY_ID type changed from NUMBER to VARCHAR2",
                "AMOUNT_USD column dropped from source layout",
            ],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "oci_df_clickstream_rt",
            "type": "OCI Data Flow",
            "source": "OCI Streaming (Kafka)",
            "target": "OCI Object Storage",
            "status": "WARNING",
            "expected_rows": 5000000,
            "actual_rows": 1250000,
            "duration_minutes": 5,
            "avg_duration_minutes": 5,
            "anomaly_detected": "Volume Drop (75%)",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "gg_hr_payroll_sync",
            "type": "GoldenGate",
            "source": "HCM Cloud",
            "target": "ADW (Ashburn)",
            "status": "SUCCESS",
            "expected_rows": 12500,
            "actual_rows": 12500,
            "duration_minutes": 3,
            "avg_duration_minutes": 3,
            "anomaly_detected": "None",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_inventory_global",
            "type": "ODI 12c",
            "source": "JD Edwards EnterpriseOne",
            "target": "Oracle SCM Cloud",
            "status": "WARNING",
            "expected_rows": 320000,
            "actual_rows": 319500,
            "duration_minutes": 78,
            "avg_duration_minutes": 45,
            "anomaly_detected": "Latency Spike (Agent Memory Pressure)",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "oci_df_iot_telemetry",
            "type": "OCI Data Flow",
            "source": "IoT Fleet Sensors",
            "target": "Autonomous JSON Database",
            "status": "FAILED",
            "expected_rows": 1200000,
            "actual_rows": 5000,
            "duration_minutes": 12,
            "avg_duration_minutes": 12,
            "anomaly_detected": "Volume Drop & ORA-01438",
            "schema_changes": ["SENSOR_TEMP precision exceeded column threshold"],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "gg_marketing_campaigns",
            "type": "GoldenGate",
            "source": "MySQL HeatWave On-Prem",
            "target": "OCI MySQL HeatWave",
            "status": "WARNING",
            "expected_rows": 85000,
            "actual_rows": 85000,
            "duration_minutes": 45,
            "avg_duration_minutes": 12,
            "anomaly_detected": "Replicat Checkpoint Lag Spike",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_customer_mdm",
            "type": "ODI 12c",
            "source": "Siebel CRM",
            "target": "Oracle CX Cloud",
            "status": "SUCCESS",
            "expected_rows": 9800,
            "actual_rows": 9800,
            "duration_minutes": 14,
            "avg_duration_minutes": 12,
            "anomaly_detected": "None",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "epm_financial_consolidation",
            "type": "EPM Automate",
            "source": "Oracle ERP Cloud",
            "target": "EPM Cloud (PBCS)",
            "status": "FAILED",
            "expected_rows": 15000,
            "actual_rows": 0,
            "duration_minutes": 35,
            "avg_duration_minutes": 5,
            "anomaly_detected": "Authentication Timeout & Zero Load",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "oci_di_logistics",
            "type": "OCI Data Integration",
            "source": "Oracle Transportation Mgmt",
            "target": "MySQL HeatWave",
            "status": "WARNING",
            "expected_rows": 24000,
            "actual_rows": 24000,
            "duration_minutes": 26,
            "avg_duration_minutes": 10,
            "anomaly_detected": "Latency Spike (DI Workspace Scale Limit)",
            "schema_changes": [],
            "last_run": timestamp,
        },
    ]
