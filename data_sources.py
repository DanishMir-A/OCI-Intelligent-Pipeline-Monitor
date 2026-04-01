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
            "source": "E-Business Suite",
            "target": "OCI ADW (Frankfurt)",
            "status": "FAILED",
            "expected_rows": 500000,
            "actual_rows": 500000,
            "duration_minutes": 185,
            "avg_duration_minutes": 5,
            "anomaly_detected": "Latency Spike",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_sales_crm_daily",
            "type": "ODI",
            "source": "Salesforce",
            "target": "Oracle ERP Cloud",
            "status": "FAILED",
            "expected_rows": 12000,
            "actual_rows": 0,
            "duration_minutes": 12,
            "avg_duration_minutes": 10,
            "anomaly_detected": "Schema Drift & Volume Drop",
            "schema_changes": [
                "opportunity_id changed to UUID",
                "amount_usd missing from source layer",
            ],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "oci_df_clickstream_rt",
            "type": "OCI Data Flow",
            "source": "Kafka Topics (OCI Streaming)",
            "target": "OCI Object Storage",
            "status": "WARNING",
            "expected_rows": 2500000,
            "actual_rows": 850000,
            "duration_minutes": 5,
            "avg_duration_minutes": 5,
            "anomaly_detected": "Volume Drop (66%)",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "gg_hr_payroll_sync",
            "type": "GoldenGate",
            "source": "HCM Cloud",
            "target": "OCI ADW (Ashburn)",
            "status": "SUCCESS",
            "expected_rows": 8500,
            "actual_rows": 8500,
            "duration_minutes": 2,
            "avg_duration_minutes": 2,
            "anomaly_detected": "None",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_inventory_global",
            "type": "ODI",
            "source": "SAP ERP",
            "target": "Oracle SCM Cloud",
            "status": "SUCCESS",
            "expected_rows": 150000,
            "actual_rows": 149950,
            "duration_minutes": 45,
            "avg_duration_minutes": 42,
            "anomaly_detected": "None",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "oci_df_iot_telemetry",
            "type": "OCI Data Flow",
            "source": "IoT Fleet Sensors",
            "target": "Autonomous JSON DB",
            "status": "FAILED",
            "expected_rows": 1000000,
            "actual_rows": 10000,
            "duration_minutes": 10,
            "avg_duration_minutes": 10,
            "anomaly_detected": "Volume Drop & Schema Drift",
            "schema_changes": ["sensor_temp_c data type changed from INT to FLOAT"],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "gg_marketing_campaigns",
            "type": "GoldenGate",
            "source": "MySQL On-Prem",
            "target": "OCI MySQL Heatwave",
            "status": "WARNING",
            "expected_rows": 50000,
            "actual_rows": 50000,
            "duration_minutes": 35,
            "avg_duration_minutes": 8,
            "anomaly_detected": "Latency Spike",
            "schema_changes": [],
            "last_run": timestamp,
        },
        {
            "pipeline_name": "odi_customer_mdm",
            "type": "ODI",
            "source": "Siebel CRM",
            "target": "OCI ADW",
            "status": "SUCCESS",
            "expected_rows": 5000,
            "actual_rows": 5000,
            "duration_minutes": 8,
            "avg_duration_minutes": 7,
            "anomaly_detected": "None",
            "schema_changes": [],
            "last_run": timestamp,
        },
    ]
