from datetime import datetime
from statistics import mean

import streamlit as st

try:
    import oci
except ImportError:
    oci = None


OCI_REQUIRED_FIELDS = ("tenancy_ocid", "user_ocid", "fingerprint", "region", "key_file")


def build_oci_config(connection_settings):
    if not connection_settings:
        return None

    config_path = (connection_settings.get("config_path") or "").strip()
    profile_name = (connection_settings.get("profile_name") or "DEFAULT").strip() or "DEFAULT"

    if config_path:
        return oci.config.from_file(file_location=config_path, profile_name=profile_name)

    if all((connection_settings.get(field) or "").strip() for field in OCI_REQUIRED_FIELDS):
        config = {
            "user": connection_settings["user_ocid"].strip(),
            "fingerprint": connection_settings["fingerprint"].strip(),
            "tenancy": connection_settings["tenancy_ocid"].strip(),
            "region": connection_settings["region"].strip(),
            "key_file": connection_settings["key_file"].strip(),
        }
        pass_phrase = (connection_settings.get("pass_phrase") or "").strip()
        if pass_phrase:
            config["pass_phrase"] = pass_phrase
        return config

    return None


def test_oci_connection(connection_settings):
    """Validate whether the supplied OCI connection settings are usable."""
    if not connection_settings:
        return False, "Add OCI credentials or a config file path to enable the live connection bridge."

    if not oci:
        return False, "OCI SDK is not installed in this environment, so the app will stay in simulator mode."

    try:
        config = build_oci_config(connection_settings)
    except Exception as exc:
        return False, f"Unable to read OCI config: {exc}"

    if not config:
        return (
            False,
            "Provide either an OCI config file path or the required inline fields: tenancy, user, fingerprint, region, and key file.",
        )

    try:
        oci.data_flow.DataFlowClient(config)
        return True, "OCI connection validated. The app can now attempt live OCI Data Flow telemetry retrieval."
    except Exception as exc:
        return False, f"OCI connection validation failed: {exc}"


def format_timestamp(value):
    if not value:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return value.strftime("%Y-%m-%d %H:%M:%S")


def compute_duration_minutes(start_time, end_time=None):
    if not start_time:
        return 0
    finish = end_time or datetime.utcnow().replace(tzinfo=start_time.tzinfo if hasattr(start_time, "tzinfo") else None)
    delta = finish - start_time
    return max(1, round(delta.total_seconds() / 60))


def map_run_status(lifecycle_state):
    lifecycle = (lifecycle_state or "").upper()
    if lifecycle in {"SUCCEEDED"}:
        return "SUCCESS"
    if lifecycle in {"FAILED", "CANCELED", "STOPPED"}:
        return "FAILED"
    return "WARNING"


def derive_anomaly(lifecycle_state, duration_minutes, avg_duration_minutes):
    lifecycle = (lifecycle_state or "").upper()
    if lifecycle == "FAILED":
        return "Run Failed"
    if lifecycle in {"CANCELED", "STOPPED"}:
        return "Run Interrupted"
    if avg_duration_minutes and duration_minutes > max(avg_duration_minutes * 1.5, avg_duration_minutes + 5):
        return "Latency Spike"
    if lifecycle in {"IN_PROGRESS", "ACCEPTED"}:
        return "Run In Progress"
    return "None"


def list_all_results(list_fn, *args, **kwargs):
    if hasattr(oci, "pagination"):
        return oci.pagination.list_call_get_all_results(list_fn, *args, **kwargs).data
    return list_fn(*args, **kwargs).data


def fetch_data_flow_runs(config, compartment_id, limit=20):
    data_flow_client = oci.data_flow.DataFlowClient(config)
    application_summaries = list_all_results(
        data_flow_client.list_applications,
        compartment_id,
        limit=100,
    )
    application_map = {app.id: app for app in application_summaries}

    run_summaries = list_all_results(
        data_flow_client.list_runs,
        compartment_id,
        limit=limit,
    )

    if not run_summaries:
        return []

    run_details = []
    durations_by_application = {}
    executors_by_application = {}

    for run_summary in run_summaries:
        run_id = getattr(run_summary, "id", None)
        run_data = run_summary
        if run_id:
            try:
                run_data = data_flow_client.get_run(run_id).data
            except Exception:
                run_data = run_summary

        application_id = getattr(run_data, "application_id", None)
        time_created = getattr(run_data, "time_created", None)
        time_updated = (
            getattr(run_data, "time_updated", None)
            or getattr(run_data, "time_ended", None)
            or getattr(run_data, "time_updated", None)
        )
        duration_minutes = compute_duration_minutes(time_created, time_updated)
        executor_count = int(getattr(run_data, "total_executor_count", 0) or 0)

        durations_by_application.setdefault(application_id or "unknown", []).append(duration_minutes)
        executors_by_application.setdefault(application_id or "unknown", []).append(executor_count)
        run_details.append(
            {
                "run": run_data,
                "application": application_map.get(application_id),
                "duration_minutes": duration_minutes,
                "executor_count": executor_count,
            }
        )

    pipeline_records = []
    for item in run_details:
        run_data = item["run"]
        application = item["application"]
        application_id = getattr(run_data, "application_id", None)
        duration_minutes = item["duration_minutes"]
        current_executor_count = item["executor_count"]
        historical_durations = durations_by_application.get(application_id or "unknown", [duration_minutes])
        historical_executors = executors_by_application.get(application_id or "unknown", [current_executor_count])
        avg_duration_minutes = max(1, round(mean(historical_durations)))
        avg_executor_count = max(0, round(mean(historical_executors)))
        lifecycle_state = getattr(run_data, "lifecycle_state", "UNKNOWN")
        archive_uri = getattr(application, "archive_uri", None) or getattr(application, "file_uri", None)
        display_name = (
            getattr(run_data, "display_name", None)
            or getattr(application, "display_name", None)
            or f"dataflow_{str(getattr(run_data, 'id', 'run'))[-6:]}"
        )
        anomaly = derive_anomaly(lifecycle_state, duration_minutes, avg_duration_minutes)
        created_time = getattr(run_data, "time_created", None)
        updated_time = getattr(run_data, "time_updated", None) or getattr(run_data, "time_ended", None)
        last_run = format_timestamp(updated_time or created_time)
        schema_changes = []
        if lifecycle_state and str(lifecycle_state).upper() == "FAILED":
            spark_exception = getattr(run_data, "spark_exception", None)
            if spark_exception:
                schema_changes = [str(spark_exception)[:160]]

        pipeline_records.append(
            {
                "pipeline_name": display_name,
                "type": "OCI Data Flow",
                "source": getattr(application, "language", None) or "OCI Data Flow Application",
                "target": archive_uri or "OCI Data Flow Runtime",
                "status": map_run_status(lifecycle_state),
                "expected_rows": avg_executor_count,
                "actual_rows": current_executor_count,
                "duration_minutes": duration_minutes,
                "avg_duration_minutes": avg_duration_minutes,
                "anomaly_detected": anomaly,
                "schema_changes": schema_changes,
                "last_run": last_run,
            }
        )

    return pipeline_records


def get_real_oci_telemetry(connection_settings=None):
    """
    Live OCI integration for Data Flow runs in the configured compartment.
    Returns None when live telemetry is unavailable so the UI can fall back safely.
    """
    if not oci or not connection_settings:
        return None

    try:
        config = build_oci_config(connection_settings)
        if not config:
            return None
        compartment_id = (connection_settings.get("compartment_ocid") or "").strip()
        if not compartment_id:
            return None

        live_runs = fetch_data_flow_runs(config, compartment_id)
        return live_runs or None
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
