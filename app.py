import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import get_health_score, get_status_emoji, predict_failure
from blueverse import call_blueverse_agent
from config import load_blueverse_config
from data_sources import get_oci_mock_pipelines, get_real_oci_telemetry


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


def build_chat_prompt(pipelines, prompt):
    return f"""
You are an expert Oracle Cloud AI Assistant.
Here is the current real-time state of the enterprise data fabric:
{json.dumps(pipelines, indent=2)}

The user asks: {prompt}
Answer correctly based on the pipeline data above. Provide actionable, concise Oracle-specific advice.
""".strip()


st.set_page_config(
    page_title="Intelligent Data Pipeline Monitor (OCI)",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 25px;
        background: linear-gradient(135deg, #FFFFFF 0%, #FAFAFA 100%);
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class='main-header'>
    <h1 style='color: #F80000; margin:0;'>☁️ Intelligent Data Pipeline Monitoring</h1>
    <h3 style='color: #333333; margin:5px 0;'>OCI Data Engineering Control Tower</h3>
    <p style='color: #666; margin:0; font-size: 14px;'>
        Powered by LTIMindtree BlueVerse AI | Monitoring ODI, GoldenGate, and OCI Data Flow
    </p>
</div>
""",
    unsafe_allow_html=True,
)

blueverse_config, missing_blueverse_keys = load_blueverse_config()
blueverse_enabled = not missing_blueverse_keys

st.sidebar.header("⚙️ Enterprise Config")
live_mode = st.sidebar.toggle(
    "🌐 Live OCI Telemetry Mode",
    value=False,
    help="Connect directly to Oracle Cloud Infrastructure Monitoring APIs",
)

if not blueverse_enabled:
    st.sidebar.info(
        "AI features are disabled until these Streamlit secrets are configured: "
        + ", ".join(missing_blueverse_keys)
    )

with st.spinner("Synchronizing with OCI Data Fabric..."):
    if live_mode:
        real_data = get_real_oci_telemetry()
        if not real_data:
            st.sidebar.warning(
                "Live OCI telemetry is unavailable, so the dashboard is using the Hackathon mock simulator."
            )
            oci_pipelines = get_oci_mock_pipelines()
        else:
            oci_pipelines = real_data
    else:
        oci_pipelines = get_oci_mock_pipelines()

st.caption(
    f"Last heartbeat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Monitoring {len(oci_pipelines)} active enterprise data pipelines"
)

if st.button("🔄 Refresh Telemetry"):
    st.cache_data.clear()
    st.rerun()

total = len(oci_pipelines)
failed = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "FAILED")
warning = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "WARNING")
success = sum(1 for pipeline in oci_pipelines if pipeline["status"] == "SUCCESS")
critical = sum(1 for pipeline in oci_pipelines if get_health_score(pipeline) < 40)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Data Assets", total)
with col2:
    st.metric("🟢 Operational", success)
with col3:
    st.metric("🟡 Warning State", warning)
with col4:
    st.metric("🔴 Pipeline Failures", failed, delta=f"-{failed} incidents", delta_color="inverse")
with col5:
    st.metric("🚨 Critical Anomalies", critical, help="Pipelines with < 40% Health")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Fleet Overview",
        "🤖 AI Auto-Remediation",
        "🔮 Predict & Prevent",
        "💬 Support AI Chat",
    ]
)

with tab1:
    st.subheader("Data Fabric Telemetry")

    health_data = []
    for pipeline in oci_pipelines:
        score = get_health_score(pipeline)
        health_data.append(
            {
                "": get_status_emoji(pipeline["status"]),
                "Pipeline Name": pipeline["pipeline_name"],
                "Tech Stack": pipeline["type"],
                "Source": pipeline["source"],
                "Target": pipeline["target"],
                "Anomaly": pipeline["anomaly_detected"],
                "Throughput": f"{pipeline['actual_rows']}/{pipeline['expected_rows']}",
                "Latency": f"{pipeline['duration_minutes']}m (avg {pipeline['avg_duration_minutes']}m)",
                "Health Score": score,
            }
        )

    df = pd.DataFrame(health_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 Visualization & Analytics")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("**Volume Throughput (Actual vs Expected)**")
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
            color_discrete_map={"Expected": "#333333", "Actual": "#C74634"},
            template="plotly_white",
        )
        fig_vol.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_chart2:
        st.markdown("**Latency Spikes (Duration vs Avg)**")
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
                "Avg Duration (m)": "#00A65A",
            },
            template="plotly_white",
        )
        fig_lat.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_lat, use_container_width=True)

with tab2:
    st.subheader("🤖 AI Root Cause & Code Remediation")
    st.write(
        "Detecting volume drops, schema drift, and latency spikes across ODI, GoldenGate, and OCI Data Flow."
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
    selected = st.selectbox("Select Anomaly to Remediate:", options)
    selected_pipeline = oci_pipelines[options.index(selected)]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Context Vectors")
        st.info(f"**Integration:** {selected_pipeline['type']}")
        st.info(f"**Source:** {selected_pipeline['source']} → **Target:** {selected_pipeline['target']}")

        score = get_health_score(selected_pipeline)
        st.metric("System Health", f"{score}/100")

        if selected_pipeline["anomaly_detected"] != "None":
            st.error(f"⚠️ {selected_pipeline['anomaly_detected']}")

        if selected_pipeline["schema_changes"]:
            for change in selected_pipeline["schema_changes"]:
                st.warning(f"🔧 Schema Drift: {change}")

    with col2:
        if st.button(
            "🔍 Generate AI Root Cause & Fix (MTTR -60%)",
            type="primary",
            disabled=not blueverse_enabled,
        ):
            with st.spinner(f"🧠 AI analyzing {selected_pipeline['type']} telemetry..."):
                result = call_blueverse_agent(
                    build_remediation_prompt(selected_pipeline),
                    blueverse_config,
                )

            st.session_state["last_fix"] = result
            st.session_state["last_fix_pipe"] = selected_pipeline["pipeline_name"]

        if "last_fix" in st.session_state and "last_fix_pipe" in st.session_state:
            st.success(f"✅ Auto-Remediation Generated for {st.session_state['last_fix_pipe']}")
            st.markdown(st.session_state["last_fix"])
            st.download_button(
                label="📥 Download Remediation Script",
                data=st.session_state["last_fix"],
                file_name=f"fix_{st.session_state['last_fix_pipe']}.md",
                mime="text/markdown",
            )

with tab3:
    st.subheader("🔮 Predictive Prevention")
    st.write("Applying heuristic scoring to current pipeline metrics to predict future outages.")

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
    st.dataframe(pred_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🚨 High-Priority Intervention Required")

    critical_pipes = [pipeline for pipeline in oci_pipelines if get_health_score(pipeline) < 50]

    if critical_pipes:
        for pipeline in critical_pipes:
            with st.expander(
                f"🔴 {pipeline['pipeline_name']} [{pipeline['type']}] — {pipeline['anomaly_detected']}"
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
        st.success("✅ OCI Data Fabric is stable. No predictive failures detected.")

with tab4:
    st.subheader("💬 OCI AI Data Engineering Assistant")
    st.write("Talk to your entire Data Fabric. The AI has context over all ODI, GoldenGate, and Data Flow jobs.")

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
                response = call_blueverse_agent(
                    build_chat_prompt(oci_pipelines, prompt),
                    blueverse_config,
                )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
st.markdown(
    """
<p style='text-align: center; color: #666; font-size: 13px;'>
    ☁️ Intelligent Data Pipeline Monitoring |
    Pythia-26 Oracle AI Infusion Hackathon |
    Built with LTIMindtree BlueVerse AI |
    Data Engineer: Zero (Danish Mir)
</p>
""",
    unsafe_allow_html=True,
)
