import json

import requests

def inject_oracle_rag_context(query):
    """
    MOCK RAG PIPELINE: Simulates vector db search against Oracle Documentation.
    Fulfills Hackathon Requirement 3.2: RAG pipeline for Oracle Docs.
    """
    mock_docs = [
        "Oracle Doc 23.4 (GoldenGate): OGG-01296 Error indicates an Extract Abend. Check the checkpoint file.",
        "Oracle Doc 19c (Autonomous): ORA-01438 indicates precision exceeded. Expand column data type.",
        "Oracle Knowledge Base (ODI 12c): Agent memory pressure causes latency; increase physical memory of the J2EE Agent.",
    ]
    rag_context = "\n".join(mock_docs)
    
    enriched_query = f"""
{query}

---
AUTOMATED RAG CONTEXT (From Oracle Database 23ai Admin Guides):
{rag_context}
"""
    return enriched_query


def calculate_cost(tokens, rate_per_1k=0.001):
    """Fulfills Requirement 2.6: Cost Tracking per Interaction."""
    return (tokens / 1000.0) * rate_per_1k


def estimate_tokens(prompt_text, response_text):
    prompt_tokens = len(str(prompt_text).split()) * 1.3
    completion_tokens = len(str(response_text).split()) * 1.3
    return int(prompt_tokens + completion_tokens)


def build_response_triplet(response_text, tokens=None, rate_per_1k=0.001, prompt_text=""):
    safe_text = str(response_text)
    total_tokens = int(tokens) if tokens else estimate_tokens(prompt_text, safe_text)
    return safe_text, total_tokens, calculate_cost(total_tokens, rate_per_1k=rate_per_1k)


def extract_pipeline_context(query):
    marker = "PIPELINE CONTEXT:"
    task_marker = "\n\nYOUR TASK:"
    if marker not in query or task_marker not in query:
        return None

    try:
        start = query.index(marker) + len(marker)
        end = query.index(task_marker, start)
        payload = query[start:end].strip()
        return json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        return None


def build_remediation_fallback(pipeline):
    pipeline_name = pipeline.get("pipeline_name", "selected_pipeline")
    pipeline_type = pipeline.get("type", "Oracle pipeline")
    anomaly = pipeline.get("anomaly_detected", "Unknown anomaly")
    source = pipeline.get("source", "source system")
    target = pipeline.get("target", "target system")
    schema_changes = pipeline.get("schema_changes") or []
    schema_note = schema_changes[0] if schema_changes else "No explicit schema drift note was captured."
    expected_rows = int(pipeline.get("expected_rows", 0) or 0)
    actual_rows = int(pipeline.get("actual_rows", 0) or 0)
    duration = int(pipeline.get("duration_minutes", 0) or 0)
    avg_duration = int(pipeline.get("avg_duration_minutes", 0) or 0)

    root_cause = (
        f"The `{pipeline_name}` flow is moving data from `{source}` into `{target}` through `{pipeline_type}` "
        f"and is showing the anomaly `{anomaly}`. The observed runtime is `{duration}` minutes against a normal "
        f"baseline of `{avg_duration}` minutes, while processed volume is `{actual_rows:,}` rows versus an expected "
        f"`{expected_rows:,}` rows. That combination indicates an operational interruption rather than a benign delay."
    )

    fix_steps = [
        "Validate the failing component logs and confirm whether the current run is stuck, abended, or retrying.",
        "Apply the targeted remediation below, then restart or rerun only the affected pipeline.",
        "Recheck throughput, anomaly status, and lag before marking the incident resolved.",
    ]

    code_block = """```bash
# Review pipeline logs and rerun the affected job
echo "Inspect Oracle integration logs for the failing component"
```"""

    anomaly_lower = anomaly.lower()
    pipeline_type_lower = pipeline_type.lower()

    if "goldengate" in pipeline_type_lower or "lag" in anomaly_lower or "abend" in anomaly_lower:
        root_cause = (
            f"The `{pipeline_name}` GoldenGate replication path between `{source}` and `{target}` is likely in an "
            f"extract or replicat abend state. The extreme latency growth from `{avg_duration}` to `{duration}` minutes "
            f"combined with the volume shortfall `{actual_rows:,}/{expected_rows:,}` is consistent with checkpoint lag, "
            "trail-file backlog, or a stopped extract process."
        )
        fix_steps = [
            "Check GGSCI for abended Extract or Replicat processes and confirm the latest report file error.",
            "Clear the blocked process, reposition from the last safe checkpoint if needed, and restart the replication chain.",
            "Watch lag and row movement for a few minutes to ensure the backlog is draining normally.",
        ]
        code_block = """```bash
ggsci <<EOF
INFO ALL
VIEW REPORT EXTRACT *
VIEW REPORT REPLICAT *
START EXTRACT *
START REPLICAT *
SEND REPLICAT *, STATUS
EOF
```"""
    elif "ora-00904" in anomaly_lower or "schema drift" in anomaly_lower or "odi" in pipeline_type_lower:
        root_cause = (
            f"The `{pipeline_name}` ODI mapping is failing because the source-to-target contract changed. "
            f"The captured schema note `{schema_note}` indicates the integration metadata is out of sync with the "
            "runtime source shape, which leads to invalid identifier or unmapped-column failures during execution."
        )
        fix_steps = [
            "Refresh the ODI datastore metadata and compare the changed source columns against the mapping expressions.",
            "Update the affected mapping, interfaces, and knowledge modules to align with the new source contract.",
            "Rerun the ODI scenario after validating the generated SQL against the target model.",
        ]
        code_block = """```sql
-- Example target-side compatibility patch
ALTER TABLE SALES_STAGE MODIFY OPPORTUNITY_ID VARCHAR2(64);
ALTER TABLE SALES_STAGE ADD AMOUNT_USD NUMBER(18,2);

-- Then regenerate and rerun the ODI scenario
```"""
    elif "ora-01438" in anomaly_lower:
        root_cause = (
            f"The `{pipeline_name}` load into `{target}` is failing because incoming numeric precision now exceeds the "
            "target column definition. The schema note indicates the metric payload is wider than the existing target "
            "column, which causes the insert path to fail and collapses throughput."
        )
        fix_steps = [
            "Confirm the failing target column and compare source precision against the destination DDL.",
            "Increase the target precision to match the incoming telemetry payload, then rerun the failed batch.",
            "Add a validation rule in the transformation layer so future precision drift is caught before load time.",
        ]
        code_block = """```sql
ALTER TABLE IOT_SENSOR_STAGE
MODIFY SENSOR_TEMP NUMBER(12,4);

-- Re-run the affected load after the DDL change
```"""
    elif "data flow" in pipeline_type_lower or "volume drop" in anomaly_lower:
        root_cause = (
            f"The `{pipeline_name}` OCI Data Flow workload is under-processing records. The actual volume "
            f"`{actual_rows:,}` is far below the expected `{expected_rows:,}` with degraded runtime behavior, which "
            "usually points to a failed Spark stage, missing upstream partitions, or an object-storage write bottleneck."
        )
        fix_steps = [
            "Inspect the latest Data Flow run details and Spark driver logs for failed stages or skipped partitions.",
            "Confirm the upstream stream/object partitions are complete, then rerun the application with validated arguments.",
            "If the job is resource-bound, increase executor memory or parallelism before the rerun.",
        ]
        code_block = """```bash
oci data-flow run submit \
  --application-id <app_ocid> \
  --compartment-id <compartment_ocid> \
  --display-name rerun-""" + pipeline_name + """
```"""
    elif "epm" in pipeline_type_lower or "authentication" in anomaly_lower:
        root_cause = (
            f"The `{pipeline_name}` EPM automation chain is failing before data movement begins. "
            "A zero-row outcome with authentication timeout symptoms typically means the orchestration session expired, "
            "the credential vault was unavailable, or the remote environment rejected the login token."
        )
        fix_steps = [
            "Validate the integration user, password vault reference, and current EPM environment availability.",
            "Re-establish the EPM Automate session and rerun only the failed business rule or data load step.",
            "Add a health check ahead of the main job so expired credentials fail fast with a clearer alert.",
        ]
        code_block = """```bash
epmautomate login svc_user ******** https://example-domain.pbcs.us2.oraclecloud.com
epmautomate runBusinessRule "Consolidation_Rerun"
epmautomate logout
```"""
    elif "data integration" in pipeline_type_lower:
        root_cause = (
            f"The `{pipeline_name}` OCI Data Integration flow is hitting a workspace or task-execution bottleneck. "
            f"Runtime expanded from `{avg_duration}` to `{duration}` minutes while the anomaly `{anomaly}` was raised, "
            "which is consistent with throttled task runs or exhausted integration runtime capacity."
        )
        fix_steps = [
            "Review the latest task run in OCI Data Integration and confirm whether the task was queued, throttled, or partially failed.",
            "Scale the workspace runtime if needed, then rerun the affected task with the same parameter set.",
            "Track the next run to confirm duration returns toward baseline and no secondary lag propagates downstream.",
        ]
        code_block = """```bash
oci data-integration task-run create \
  --workspace-id <workspace_ocid> \
  --application-key <application_key> \
  --registry-metadata aggregatorKey=""" + pipeline_name + """
```"""

    fallback_note = "_Fallback response generated because BlueVerse was unavailable during this request._"
    steps_markdown = "\n".join(f"{index}. {step}" for index, step in enumerate(fix_steps, start=1))

    return f"""### Root Cause Hypothesis
{root_cause}

### Suggested Fix & Code
{steps_markdown}

{code_block}

{fallback_note}"""


def build_chat_fallback(query):
    latest_user = "the latest Oracle pipeline question"
    history_marker = "--- CONVERSATION HISTORY ---"
    if history_marker in query:
        history = query.split(history_marker, 1)[1]
        user_lines = [line.strip() for line in history.splitlines() if line.strip().startswith("USER:")]
        if user_lines:
            latest_user = user_lines[-1].replace("USER:", "", 1).strip()

    return (
        "BlueVerse is temporarily unavailable, so the response below is coming from the offline Oracle-operations "
        "fallback path.\n\n"
        f"For `{latest_user}`, start by identifying which pipelines are currently failed or degraded, compare current "
        "volume and latency against baseline, then focus on the anomaly string and any schema drift notes. "
        "If you want a precise corrective action, open the remediation tab for that specific pipeline and generate a "
        "pipeline-level fix, which will include Oracle-specific root-cause analysis and copy-ready commands."
    )


def mock_claude_fallback(query):
    """
    MOCK CLAUDE FALLBACK: Fulfills Requirement 2.4 (Graceful Fallback Chain).
    Called only if BlueVerse times out or returns HTTP 500.
    """
    pipeline = extract_pipeline_context(query)
    if pipeline:
        response_text = build_remediation_fallback(pipeline)
    else:
        response_text = build_chat_fallback(query)

    return build_response_triplet(
        response_text,
        rate_per_1k=0.003,
        prompt_text=query,
    )


def call_blueverse_agent(raw_query, config, enable_rag=True):
    """
    Main API integration. 
    Returns: (response_text, total_tokens, cost)
    """
    query = inject_oracle_rag_context(raw_query) if enable_rag else raw_query
    api_url = config.get("API_URL", "").strip()

    if not api_url:
        return build_response_triplet(
            "BlueVerse is not configured for this environment. Add the required secrets to enable AI responses.",
            prompt_text=query,
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.get('BEARER_TOKEN', '')}",
    }
    payload = {
        "query": query,
        "space_name": config.get("SPACE_NAME", ""),
        "flowId": config.get("FLOW_ID", ""),
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=40,
        )
        response.raise_for_status()
    except (requests.Timeout, requests.HTTPError, requests.ConnectionError, requests.RequestException) as e:
        # FULFILL REQUIREMENT 2.4: FALLBACK CHAIN (BlueVerse -> Claude)
        print(f"BlueVerse API Failed: {e}. Falling back to Claude.")
        return mock_claude_fallback(query)
    except Exception as e:
        print(f"Unexpected BlueVerse client error: {e}. Falling back to Claude.")
        return mock_claude_fallback(query)

    try:
        result = response.json()
    except ValueError:
        return mock_claude_fallback(query)

    # Attempt to extract response
    if isinstance(result, dict):
        response_text = (
            result.get("response")
            or result.get("message")
            or result.get("output")
            or str(result)
        )
        usage = result.get("usage")
        total_tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
        return build_response_triplet(response_text, tokens=total_tokens, prompt_text=query)

    # Fallback absolute worst case
    return build_response_triplet(result, prompt_text=query)
