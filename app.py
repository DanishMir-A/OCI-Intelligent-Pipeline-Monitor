import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import get_health_score, get_status_emoji, predict_failure
from blueverse import call_blueverse_agent
from config import load_blueverse_config
from data_sources import get_oci_mock_pipelines, get_real_oci_telemetry, test_oci_connection


def build_remediation_prompt(selected_pipeline):
    return f"""
You are an expert Oracle Cloud Infrastructure (OCI) Data Engineer AI Assistant.
I have an OCI data pipeline that has triggered an alert.

PIPELINE CONTEXT:
{json.dumps(selected_pipeline, indent=2)}

YOUR TASK:
Analyze the pipeline metric anomalies (data volume drops, schema drift, latency spikes).
Respond STRICTLY in the following format using Markdown:

### Root Cause Hypothesis
(Provide a highly technical, Oracle-specific explanation for why this failure or anomaly occurred. e.g. GoldenGate LAG, ODI agent failure, Kafka to Object Storage partition issues).

### Suggested Fix & Code
(Provide exact actionable remediation steps. Generate a snippet of Python, Oracle SQL, ODI scripting, or OCI CLI commands that an engineer can copy-paste to fix this issue immediately to reduce MTTR).
""".strip()


def build_chat_prompt(pipelines, history):
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
    return f"""
You are an expert Oracle Cloud AI Assistant.
Here is the current real-time state of the enterprise data fabric:
{json.dumps(pipelines, indent=2)}

--- CONVERSATION HISTORY ---
{history_text}

Respond directly to the user's latest query accurately based on the pipeline data above. Provide actionable, concise Oracle-specific advice.
""".strip()


def render_metric_card(title, value, subtitle, tone="neutral"):
    st.markdown(
        f"""
<div class="metric-card metric-{tone}">
    <div class="metric-title">{title}</div>
    <div class="metric-value">{value}</div>
    <div class="metric-subtitle">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_section_intro(eyebrow, title, description):
    st.markdown(
        f"""
<div class="section-intro">
    <div class="section-eyebrow">{eyebrow}</div>
    <h2>{title}</h2>
    <p>{description}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_pipeline_brief(pipeline, score):
    anomaly = pipeline["anomaly_detected"] if pipeline["anomaly_detected"] != "None" else "No active anomaly"
    drift = "<br>".join(pipeline["schema_changes"]) if pipeline["schema_changes"] else "No schema drift detected"
    st.markdown(
        f"""
<div class="detail-card">
    <div class="detail-header">
        <div>
            <div class="detail-label">Selected Pipeline</div>
            <h3>{pipeline["pipeline_name"]}</h3>
        </div>
        <div class="health-pill">Health {score}/100</div>
    </div>
    <div class="detail-grid">
        <div>
            <span>Tech Stack</span>
            <strong>{pipeline["type"]}</strong>
        </div>
        <div>
            <span>Flow</span>
            <strong>{pipeline["source"]} → {pipeline["target"]}</strong>
        </div>
        <div>
            <span>Anomaly</span>
            <strong>{anomaly}</strong>
        </div>
        <div>
            <span>Schema Notes</span>
            <strong>{drift}</strong>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def style_volume_chart(fig):
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FBFBFC",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
        ),
        xaxis=dict(title="", showgrid=False, tickangle=-20),
        yaxis=dict(title="Rows", gridcolor="#E6E8EB", zeroline=False),
    )
    fig.update_traces(marker_line_width=0, hovertemplate="%{y:,}<extra>%{fullData.name}</extra>")


def style_latency_chart(fig):
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FBFBFC",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
        ),
        xaxis=dict(title="", showgrid=False, tickangle=-20),
        yaxis=dict(title="Minutes", gridcolor="#E6E8EB", zeroline=False),
    )
    fig.update_traces(line_width=3, marker_size=8)


def clone_pipeline_record(pipeline):
    cloned = dict(pipeline)
    cloned["schema_changes"] = list(pipeline.get("schema_changes", []))
    return cloned


def load_default_mock_pipelines():
    return [clone_pipeline_record(pipeline) for pipeline in get_oci_mock_pipelines()]


def ensure_mock_pipeline_state(force_reset=False):
    if force_reset or "mock_pipelines" not in st.session_state:
        st.session_state["mock_pipelines"] = load_default_mock_pipelines()
    return st.session_state["mock_pipelines"]


def clear_remediation_state():
    for key in (
        "last_fix",
        "last_fix_pipe",
        "last_fix_tokens",
        "last_fix_cost",
        "last_fix_applied_pipe",
        "last_fix_applied_at",
        "last_fix_apply_mode",
    ):
        st.session_state.pop(key, None)


def get_saved_oci_connection():
    return st.session_state.get(
        "oci_connection",
        {
            "config_path": "",
            "profile_name": "DEFAULT",
            "tenancy_ocid": "",
            "user_ocid": "",
            "fingerprint": "",
            "region": "",
            "compartment_ocid": "",
            "key_file": "",
            "pass_phrase": "",
        },
    )


def has_saved_oci_connection(connection):
    meaningful_fields = (
        "config_path",
        "tenancy_ocid",
        "user_ocid",
        "fingerprint",
        "region",
        "compartment_ocid",
        "key_file",
    )
    return any(str(connection.get(field, "")).strip() for field in meaningful_fields)


def apply_mock_fix(pipeline_name):
    pipelines = ensure_mock_pipeline_state()
    for pipeline in pipelines:
        if pipeline["pipeline_name"] == pipeline_name:
            pipeline["status"] = "SUCCESS"
            pipeline["actual_rows"] = pipeline["expected_rows"]
            pipeline["duration_minutes"] = max(1, pipeline["avg_duration_minutes"])
            pipeline["anomaly_detected"] = "None"
            pipeline["schema_changes"] = []
            pipeline["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return clone_pipeline_record(pipeline)
    return None


st.set_page_config(
    page_title="Intelligent Data Pipeline Monitor (OCI)",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {
        --oracle-red: #f80000;
        --ink: #131722;
        --muted: #5d6471;
        --panel: rgba(255, 255, 255, 0.82);
        --panel-strong: #ffffff;
        --line: rgba(19, 23, 34, 0.08);
        --shadow: 0 18px 45px rgba(17, 24, 39, 0.09);
        --success: #138a52;
        --warning: #bb6b00;
        --critical: #d7261e;
        --accent-sand: #fff4ec;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(248, 0, 0, 0.08), transparent 28%),
            radial-gradient(circle at 85% 10%, rgba(255, 184, 77, 0.10), transparent 22%),
            linear-gradient(180deg, #fffdf9 0%, #f7f7f8 48%, #f2f4f7 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .main-header {
        position: relative;
        overflow: hidden;
        padding: 34px 34px 28px 34px;
        border-radius: 28px;
        margin-bottom: 18px;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.97) 0%, rgba(250,250,251,0.94) 55%, rgba(255,244,236,0.92) 100%);
        border: 1px solid rgba(255,255,255,0.7);
        box-shadow: var(--shadow);
    }

    .main-header::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(120deg, rgba(248,0,0,0.09), transparent 24%),
            linear-gradient(0deg, transparent 0%, rgba(255,255,255,0.28) 100%);
        pointer-events: none;
    }

    .hero-grid {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: 2.1fr 1fr;
        gap: 24px;
        align-items: start;
    }

    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--oracle-red);
        margin-bottom: 14px;
    }

    .hero-title {
        margin: 0;
        color: var(--ink);
        font-size: clamp(2rem, 3.2vw, 3.4rem);
        line-height: 0.95;
        letter-spacing: -0.04em;
    }

    .hero-subtitle {
        margin: 14px 0 18px 0;
        max-width: 760px;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.6;
    }

    .hero-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(19, 23, 34, 0.04);
        border: 1px solid rgba(19, 23, 34, 0.06);
        color: var(--ink);
        font-size: 0.88rem;
        font-weight: 600;
    }

    .hero-chip strong {
        font-weight: 800;
    }

    .hero-panel {
        background: rgba(19, 23, 34, 0.96);
        color: white;
        border-radius: 22px;
        padding: 18px 20px;
        box-shadow: 0 20px 40px rgba(19, 23, 34, 0.16);
    }

    .hero-panel-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.72;
        margin-bottom: 8px;
    }

    .hero-panel-value {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin-bottom: 8px;
    }

    .hero-panel-copy {
        color: rgba(255,255,255,0.78);
        line-height: 1.5;
        font-size: 0.92rem;
    }

    .status-band {
        margin: 8px 0 22px 0;
        padding: 14px 18px;
        border-radius: 18px;
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(19,23,34,0.05);
        backdrop-filter: blur(8px);
    }

    .status-band strong {
        color: var(--ink);
    }

    .section-intro {
        margin: 6px 0 14px 0;
    }

    .section-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--oracle-red);
        margin-bottom: 8px;
    }

    .section-intro h2 {
        margin: 0 0 6px 0;
        color: var(--ink);
        font-size: 1.55rem;
        letter-spacing: -0.03em;
    }

    .section-intro p {
        margin: 0;
        color: var(--muted);
        max-width: 760px;
        line-height: 1.6;
    }

    .metric-card {
        min-height: 132px;
        padding: 18px 18px 16px 18px;
        border-radius: 22px;
        background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(250,250,251,0.92));
        border: 1px solid rgba(19,23,34,0.06);
        box-shadow: 0 12px 32px rgba(17, 24, 39, 0.06);
    }

    .metric-title {
        color: var(--muted);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 16px;
    }

    .metric-value {
        color: var(--ink);
        font-size: 2rem;
        line-height: 1;
        letter-spacing: -0.05em;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .metric-subtitle {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .metric-success {
        box-shadow: inset 0 0 0 1px rgba(19,138,82,0.08), 0 12px 32px rgba(17, 24, 39, 0.06);
    }

    .metric-warning {
        box-shadow: inset 0 0 0 1px rgba(187,107,0,0.1), 0 12px 32px rgba(17, 24, 39, 0.06);
    }

    .metric-danger {
        box-shadow: inset 0 0 0 1px rgba(215,38,30,0.12), 0 12px 32px rgba(17, 24, 39, 0.06);
    }

    .detail-card {
        padding: 22px;
        border-radius: 24px;
        background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,249,251,0.94));
        border: 1px solid rgba(19,23,34,0.06);
        box-shadow: var(--shadow);
        margin-bottom: 12px;
    }

    .detail-header {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
        margin-bottom: 18px;
    }

    .detail-header h3 {
        margin: 4px 0 0 0;
        font-size: 1.5rem;
        line-height: 1.05;
        color: var(--ink);
        letter-spacing: -0.03em;
    }

    .detail-label {
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .health-pill {
        white-space: nowrap;
        padding: 10px 14px;
        border-radius: 999px;
        background: rgba(248,0,0,0.08);
        color: #a80b0b;
        font-weight: 800;
        font-size: 0.9rem;
    }

    .detail-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
    }

    .detail-grid div {
        padding: 14px 16px;
        border-radius: 18px;
        background: rgba(19,23,34,0.03);
        border: 1px solid rgba(19,23,34,0.05);
    }

    .detail-grid span {
        display: block;
        color: var(--muted);
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .detail-grid strong {
        color: var(--ink);
        line-height: 1.5;
        font-size: 0.95rem;
    }

    .chart-shell {
        padding: 16px 18px 8px 18px;
        border-radius: 24px;
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(19,23,34,0.06);
        box-shadow: 0 16px 36px rgba(17, 24, 39, 0.05);
        backdrop-filter: blur(8px);
    }

    .chart-title {
        margin: 0 0 2px 0;
        color: var(--ink);
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .chart-copy {
        margin: 0 0 12px 0;
        color: var(--muted);
        font-size: 0.9rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(255,255,255,0.72);
        padding: 8px;
        border-radius: 18px;
        border: 1px solid rgba(19,23,34,0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 14px;
        padding: 0 16px;
        background: transparent;
        color: var(--muted);
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(248,0,0,0.1), rgba(255,244,236,0.95));
        color: var(--ink);
    }

    .st-emotion-cache-16txtl3,
    .st-emotion-cache-1r6slb0,
    div[data-testid="stExpander"] {
        border-radius: 20px !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid rgba(19,23,34,0.06);
        background: rgba(255,255,255,0.82);
        box-shadow: 0 10px 28px rgba(17, 24, 39, 0.05);
    }

    @media (max-width: 900px) {
        .hero-grid,
        .detail-grid {
            grid-template-columns: 1fr;
        }

        .hero-panel {
            margin-top: 6px;
        }

        .detail-header {
            flex-direction: column;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

blueverse_config, missing_blueverse_keys = load_blueverse_config()
blueverse_enabled = not missing_blueverse_keys

st.sidebar.header("Enterprise Config")
live_mode = st.sidebar.toggle(
    "Live OCI Telemetry Mode",
    value=False,
    help="Connect directly to Oracle Cloud Infrastructure and read live Data Flow run telemetry from the selected compartment.",
)
allow_blueverse_fallback = st.sidebar.toggle(
    "Use offline AI fallback",
    value=False,
    help="Turn this on only if you want simulated AI output when BlueVerse is unavailable.",
)

saved_oci_connection = get_saved_oci_connection()
saved_connection_status = st.session_state.get("oci_connection_status")

with st.sidebar.expander("Connect To OCI", expanded=live_mode):
    st.caption(
        "Store OCI connection settings in the current session so the dashboard can attempt a live bridge. "
        "The current live implementation reads OCI Data Flow run telemetry from the compartment you provide. "
        "For hosted deployments, map these values to managed secrets rather than local files."
    )
    with st.form("oci_connection_form"):
        config_path = st.text_input(
            "OCI config file path",
            value=saved_oci_connection.get("config_path", ""),
            help="Optional. Use this if you already have a local OCI config file.",
        )
        profile_name = st.text_input(
            "OCI profile name",
            value=saved_oci_connection.get("profile_name", "DEFAULT"),
        )
        tenancy_ocid = st.text_input(
            "Tenancy OCID",
            value=saved_oci_connection.get("tenancy_ocid", ""),
        )
        user_ocid = st.text_input(
            "User OCID",
            value=saved_oci_connection.get("user_ocid", ""),
        )
        fingerprint = st.text_input(
            "API key fingerprint",
            value=saved_oci_connection.get("fingerprint", ""),
        )
        region = st.text_input(
            "Region",
            value=saved_oci_connection.get("region", ""),
            help="Example: ap-mumbai-1",
        )
        compartment_ocid = st.text_input(
            "Compartment OCID",
            value=saved_oci_connection.get("compartment_ocid", ""),
            help="Required for live OCI Data Flow telemetry discovery.",
        )
        key_file = st.text_input(
            "Private key file path",
            value=saved_oci_connection.get("key_file", ""),
            help="Optional when using a config file path. Required for inline OCI fields.",
        )
        pass_phrase = st.text_input(
            "Private key pass phrase",
            value=saved_oci_connection.get("pass_phrase", ""),
            type="password",
        )
        save_connection = st.form_submit_button("Save OCI Connection")
        clear_connection = st.form_submit_button("Clear OCI Connection")

    if save_connection:
        st.session_state["oci_connection"] = {
            "config_path": config_path,
            "profile_name": profile_name,
            "tenancy_ocid": tenancy_ocid,
            "user_ocid": user_ocid,
            "fingerprint": fingerprint,
            "region": region,
            "compartment_ocid": compartment_ocid,
            "key_file": key_file,
            "pass_phrase": pass_phrase,
        }
        is_valid, status_message = test_oci_connection(st.session_state["oci_connection"])
        st.session_state["oci_connection_status"] = {
            "ok": is_valid,
            "message": status_message,
        }
        saved_oci_connection = st.session_state["oci_connection"]
        saved_connection_status = st.session_state["oci_connection_status"]

    if clear_connection:
        st.session_state["oci_connection"] = {
            "config_path": "",
            "profile_name": "DEFAULT",
            "tenancy_ocid": "",
            "user_ocid": "",
            "fingerprint": "",
            "region": "",
            "compartment_ocid": "",
            "key_file": "",
            "pass_phrase": "",
        }
        st.session_state.pop("oci_connection_status", None)
        saved_oci_connection = st.session_state["oci_connection"]
        saved_connection_status = None

    if saved_connection_status:
        if saved_connection_status.get("ok"):
            st.success(saved_connection_status["message"])
        else:
            st.warning(saved_connection_status["message"])

if not blueverse_enabled:
    st.sidebar.info(
        "AI features are disabled until these Streamlit secrets are configured: "
        + ", ".join(missing_blueverse_keys)
    )

with st.spinner("Synchronizing with OCI Data Fabric..."):
    telemetry_mode = "Mock telemetry"
    telemetry_note = "Using the built-in Oracle pipeline simulator."
    compartment_configured = bool((saved_oci_connection.get("compartment_ocid") or "").strip())
    if live_mode:
        if has_saved_oci_connection(saved_oci_connection):
            real_data = get_real_oci_telemetry(saved_oci_connection)
        else:
            real_data = None

        if not real_data:
            if has_saved_oci_connection(saved_oci_connection):
                if not compartment_configured:
                    telemetry_note = (
                        "OCI connection details are attached, but live OCI Data Flow telemetry also needs a compartment OCID. "
                        "The dashboard is showing normalized Oracle demo telemetry."
                    )
                    st.sidebar.warning(telemetry_note)
                else:
                    telemetry_mode = "OCI bridge simulator"
                    telemetry_note = (
                        "OCI connection details are attached, but no live OCI Data Flow runs were returned for the selected compartment. "
                        "The dashboard is showing normalized Oracle demo telemetry."
                    )
                    st.sidebar.warning(telemetry_note)
            else:
                telemetry_note = (
                    "Live telemetry needs OCI connection details. The dashboard is using the Hackathon mock simulator."
                )
                st.sidebar.info(telemetry_note)
            oci_pipelines = ensure_mock_pipeline_state()
        else:
            oci_pipelines = real_data
            telemetry_mode = "Live OCI telemetry"
            telemetry_note = "Live OCI Data Flow telemetry is active for the selected compartment."
    else:
        oci_pipelines = ensure_mock_pipeline_state()

total = len(oci_pipelines)
failed = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "FAILED")
warning = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "WARNING")
success = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "SUCCESS")
critical = sum(1 for pipeline in oci_pipelines if get_health_score(pipeline) < 40)
average_health = round(sum(get_health_score(pipeline) for pipeline in oci_pipelines) / max(total, 1))
latest_heartbeat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
mode_label = telemetry_mode
if blueverse_enabled:
    ai_label = "BlueVerse live only" if not allow_blueverse_fallback else "BlueVerse with fallback"
else:
    ai_label = "BlueVerse offline"
connection_label = (
    "OCI bridge attached" if has_saved_oci_connection(saved_oci_connection) else "OCI bridge not attached"
)
uses_live_data_flow_metrics = telemetry_mode == "Live OCI telemetry"
metric_column_label = "Executor Metric" if uses_live_data_flow_metrics else "Throughput"
metric_chart_title = "Executor Allocation" if uses_live_data_flow_metrics else "Volume Throughput"
metric_chart_copy = (
    "Compare current executor allocation against recent baseline executor counts for each OCI Data Flow application."
    if uses_live_data_flow_metrics
    else "Compare expected volume against actual processed rows to spot ingestion gaps immediately."
)
metric_y_axis = "Executors" if uses_live_data_flow_metrics else "Rows"

st.markdown(
    f"""
<div class="main-header">
    <div class="hero-grid">
        <div>
            <div class="hero-eyebrow">OCI Command Surface</div>
            <h1 class="hero-title">Intelligent Data Pipeline Monitoring</h1>
            <p class="hero-subtitle">
                A control tower for Oracle-focused data operations across ODI, GoldenGate, and OCI Data Flow.
                Monitor throughput, expose schema drift, surface risk, and move from alert to remediation in one screen.
            </p>
            <div class="hero-strip">
                <div class="hero-chip"><strong>{total}</strong> active pipelines</div>
                <div class="hero-chip"><strong>{mode_label}</strong></div>
                <div class="hero-chip"><strong>{connection_label}</strong></div>
                <div class="hero-chip"><strong>{ai_label}</strong></div>
                <div class="hero-chip"><strong>Last heartbeat</strong> {latest_heartbeat}</div>
            </div>
        </div>
        <div class="hero-panel">
            <div class="hero-panel-label">Fleet Health Index</div>
            <div class="hero-panel-value">{average_health}/100</div>
            <div class="hero-panel-copy">
                {success} operational, {warning} degraded, and {failed} failed integrations are currently in view.
                Use the tabs below to inspect the fleet, generate fixes, and prioritize intervention.
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="status-band">
    <strong>Control Status:</strong> Monitoring {total} enterprise pipelines with {critical} critical anomalies.
    Telemetry mode is set to <strong>{mode_label}</strong>, the OCI bridge is <strong>{connection_label}</strong>,
    and AI assist is <strong>{ai_label}</strong>.
</div>
""",
    unsafe_allow_html=True,
)

st.caption(telemetry_note)

control_col1, control_col2, _ = st.columns([1.1, 1.2, 4])
with control_col1:
    if st.button("Refresh Telemetry"):
        st.cache_data.clear()
        st.rerun()
with control_col2:
    if st.button(
        "Reset Demo State",
        disabled=telemetry_mode == "Live OCI telemetry",
        help="Reset simulated telemetry and clear any applied remediation actions.",
    ):
        ensure_mock_pipeline_state(force_reset=True)
        clear_remediation_state()
        st.rerun()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_metric_card("Total Assets", total, "Pipelines currently tracked")
with col2:
    render_metric_card("Operational", success, "Healthy flows moving normally", tone="success")
with col3:
    render_metric_card("Warning State", warning, "Pipelines showing early instability", tone="warning")
with col4:
    render_metric_card("Failures", failed, "Incidents requiring active remediation", tone="danger")
with col5:
    render_metric_card("Critical", critical, "Health score below 40", tone="danger")

st.markdown("")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Fleet Overview",
        "AI Auto-Remediation",
        "Predict & Prevent",
        "Support AI Chat",
    ]
)

with tab1:
    render_section_intro(
        "Operations View",
        "Fleet Telemetry",
        "Track throughput, latency, and anomaly state across the current estate. This is the fastest way to spot unhealthy movement patterns across the data fabric.",
    )

    health_data = []
    for pipeline in oci_pipelines:
        score = get_health_score(pipeline)
        health_data.append(
            {
                "Status": get_status_emoji(pipeline["status"]),
                "Pipeline Name": pipeline["pipeline_name"],
                "Tech Stack": pipeline["type"],
                "Source": pipeline["source"],
                "Target": pipeline["target"],
                "Anomaly": pipeline["anomaly_detected"],
                metric_column_label: f"{pipeline['actual_rows']:,}/{pipeline['expected_rows']:,}",
                "Latency": f"{pipeline['duration_minutes']}m (avg {pipeline['avg_duration_minutes']}m)",
                "Health Score": score,
            }
        )

    df = pd.DataFrame(health_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Health Score": st.column_config.ProgressColumn(
                "Health Score",
                min_value=0,
                max_value=100,
                format="%d",
            ),
        },
    )

    st.markdown("")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
        st.markdown(f'<div class="chart-title">{metric_chart_title}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="chart-copy">{metric_chart_copy}</div>',
            unsafe_allow_html=True,
        )
        df_vol = pd.DataFrame(
            {
                "Pipeline": [pipeline["pipeline_name"] for pipeline in oci_pipelines],
                "Expected": [pipeline["expected_rows"] for pipeline in oci_pipelines],
                "Actual": [pipeline["actual_rows"] for pipeline in oci_pipelines],
            }
        )
        fig_vol = px.bar(
            df_vol,
            x="Pipeline",
            y=["Expected", "Actual"],
            barmode="group",
            color_discrete_map={"Expected": "#2B313B", "Actual": "#F35B04"},
            template="plotly_white",
        )
        style_volume_chart(fig_vol)
        fig_vol.update_yaxes(title=metric_y_axis)
        st.plotly_chart(fig_vol, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Latency Deviation</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-copy">Read current execution time against historical average to identify drift before it becomes an outage.</div>',
            unsafe_allow_html=True,
        )
        df_lat = pd.DataFrame(
            {
                "Pipeline": [pipeline["pipeline_name"] for pipeline in oci_pipelines],
                "Current Duration (m)": [pipeline["duration_minutes"] for pipeline in oci_pipelines],
                "Avg Duration (m)": [pipeline["avg_duration_minutes"] for pipeline in oci_pipelines],
            }
        )
        fig_lat = px.line(
            df_lat,
            x="Pipeline",
            y=["Current Duration (m)", "Avg Duration (m)"],
            markers=True,
            color_discrete_map={
                "Current Duration (m)": "#F80000",
                "Avg Duration (m)": "#117A65",
            },
            template="plotly_white",
        )
        style_latency_chart(fig_lat)
        st.plotly_chart(fig_lat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    render_section_intro(
        "AI Assist",
        "Root Cause And Remediation",
        "Select a pipeline anomaly, review the operational context, and ask BlueVerse for a targeted fix with copy-ready steps.",
    )

    if not blueverse_enabled:
        st.warning(
            "BlueVerse credentials are missing, so remediation generation is disabled. "
            "Add the required values to `.streamlit/secrets.toml` to enable it."
        )

    options = [
        f"{get_status_emoji(pipeline['status'])} {pipeline['pipeline_name']} [{pipeline['type']}] - Anomaly: {pipeline['anomaly_detected']}"
        for pipeline in oci_pipelines
    ]
    selected = st.selectbox("Select anomaly to investigate", options)
    selected_pipeline = oci_pipelines[options.index(selected)]
    selected_score = get_health_score(selected_pipeline)

    left_col, right_col = st.columns([1.1, 1.4])
    with left_col:
        render_pipeline_brief(selected_pipeline, selected_score)

        if selected_pipeline["anomaly_detected"] != "None":
            st.error(f"Anomaly detected: {selected_pipeline['anomaly_detected']}")

        if selected_pipeline["schema_changes"]:
            for change in selected_pipeline["schema_changes"]:
                st.warning(f"Schema drift: {change}")
        else:
            st.success("No schema drift notes are attached to this pipeline.")

    with right_col:
        st.markdown(
            """
<div class="chart-shell">
    <div class="chart-title">AI Response Workspace</div>
    <div class="chart-copy">Generate a structured root-cause explanation and a remediation script tailored to the selected OCI pipeline.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if st.button(
            "Generate AI Root Cause & Fix",
            type="primary",
            disabled=not blueverse_enabled,
        ):
            with st.spinner(f"AI analyzing {selected_pipeline['type']} telemetry..."):
                result, tokens, cost = call_blueverse_agent(
                    build_remediation_prompt(selected_pipeline),
                    blueverse_config,
                    allow_fallback=allow_blueverse_fallback,
                )

            st.session_state["last_fix"] = result
            st.session_state["last_fix_pipe"] = selected_pipeline["pipeline_name"]
            st.session_state["last_fix_tokens"] = tokens
            st.session_state["last_fix_cost"] = cost

        if "last_fix" in st.session_state and "last_fix_pipe" in st.session_state:
            st.success(f"Auto-remediation generated for {st.session_state['last_fix_pipe']}")
            st.markdown(f"**⚡ Tokens:** {st.session_state.get('last_fix_tokens', 0):,} | **💰 Est. Cost:** ${st.session_state.get('last_fix_cost', 0):.4f}")
            st.markdown(st.session_state["last_fix"])
            st.download_button(
                label="Download Remediation Script",
                data=st.session_state["last_fix"],
                file_name=f"fix_{st.session_state['last_fix_pipe']}.md",
                mime="text/markdown",
            )

            can_apply_fix = st.session_state["last_fix_pipe"] == selected_pipeline["pipeline_name"]
            apply_help = (
                "Apply the AI fix directly to the session-backed telemetry simulator and refresh the dashboard."
                if telemetry_mode != "Live OCI telemetry"
                else "Live apply requires backend orchestration and an approved OCI action layer."
            )
            if st.button(
                "Apply Fix To Pipeline",
                disabled=not can_apply_fix or telemetry_mode == "Live OCI telemetry",
                help=apply_help,
            ):
                recovered_pipeline = apply_mock_fix(selected_pipeline["pipeline_name"])
                if recovered_pipeline:
                    st.session_state["last_fix_applied_pipe"] = recovered_pipeline["pipeline_name"]
                    st.session_state["last_fix_applied_at"] = recovered_pipeline["last_run"]
                    st.session_state["last_fix_apply_mode"] = telemetry_mode
                    st.rerun()

            if not can_apply_fix:
                st.info("Generate a fix for the currently selected pipeline before applying it.")

        if st.session_state.get("last_fix_applied_pipe") == selected_pipeline["pipeline_name"]:
            st.success(
                f"AI remediation applied in {st.session_state.get('last_fix_apply_mode', 'demo mode')} at "
                f"{st.session_state.get('last_fix_applied_at', 'the current session')}."
            )

with tab3:
    render_section_intro(
        "Preventive Ops",
        "Intervention Forecasting",
        "Use the current telemetry snapshot to prioritize which integrations need attention first. This view surfaces deteriorating patterns before total failure.",
    )

    pred_data = []
    for pipeline in oci_pipelines:
        pred_data.append(
            {
                "Pipeline": pipeline["pipeline_name"],
                "Tech Stack": pipeline["type"],
                "Current Status": f"{get_status_emoji(pipeline['status'])} {pipeline['status']}",
                "Anomaly Forecaster": predict_failure(pipeline),
                "Health Score": get_health_score(pipeline),
            }
        )

    pred_df = pd.DataFrame(pred_data).sort_values(by="Health Score")
    st.dataframe(
        pred_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Health Score": st.column_config.ProgressColumn(
                "Health Score",
                min_value=0,
                max_value=100,
                format="%d",
            ),
        },
    )

    st.markdown("")
    st.markdown(
        """
<div class="section-intro">
    <div class="section-eyebrow">Priority Queue</div>
    <h2>High-Priority Intervention Required</h2>
    <p>These pipelines have the weakest health scores in the fleet and should be reviewed first.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    critical_pipes = [pipeline for pipeline in oci_pipelines if get_health_score(pipeline) < 50]

    if critical_pipes:
        for pipeline in critical_pipes:
            with st.expander(
                f"{get_status_emoji(pipeline['status'])} {pipeline['pipeline_name']} [{pipeline['type']}] — {pipeline['anomaly_detected']}"
            ):
                col1, col2, col3 = st.columns(3)
                col1.metric("Health", f"{get_health_score(pipeline)}/100")
                col2.metric("Latency", f"{pipeline['duration_minutes']} min")
                data_loss = round(
                    (1 - pipeline["actual_rows"] / max(pipeline["expected_rows"], 1)) * 100
                )
                col3.metric("Data Loss %", f"{data_loss}%")

                st.button(
                    f"Generate ServiceNow Ticket for {pipeline['pipeline_name']}",
                    key=f"tkt_{pipeline['pipeline_name']}",
                )
    else:
        st.success("OCI Data Fabric is stable. No predictive failures detected.")

with tab4:
    render_section_intro(
        "Operator Console",
        "Support AI Chat",
        "Ask questions about pipeline latency, drift, or recovery options. The assistant receives the current telemetry snapshot as context.",
    )

    if not blueverse_enabled:
        st.info(
            "Chat is disabled until BlueVerse secrets are configured in `.streamlit/secrets.toml`."
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about pipeline latencies, schema drifts, or how to fix ODI...",
        disabled=not blueverse_enabled,
    )

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Analyzing data fabric..."):
                response, tokens, cost = call_blueverse_agent(
                    build_chat_prompt(oci_pipelines, st.session_state.messages),
                    blueverse_config,
                    allow_fallback=allow_blueverse_fallback,
                )
            st.markdown(response)
            st.caption(f"⚡ Tokens: {tokens:,} | 💰 Cost: ${cost:.4f}")

        st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
st.markdown(
    """
<p style='text-align: center; color: #666; font-size: 13px;'>
    OCI Intelligent Data Pipeline Monitoring |
    Pythia-26 Oracle AI Infusion Hackathon |
    Built with LTIMindtree BlueVerse AI |
    Data Engineer: Zero (Danish Mir)
</p>
""",
    unsafe_allow_html=True,
)
