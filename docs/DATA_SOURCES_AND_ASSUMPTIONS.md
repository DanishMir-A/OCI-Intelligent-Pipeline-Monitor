# Data Sources And Assumptions

## Data Sources

### Mock Telemetry
The current prototype is driven primarily by `get_oci_mock_pipelines()` in `data_sources.py`. Each record includes:
- pipeline name
- integration type
- source and target systems
- operational status
- expected and actual row counts
- current and average duration
- anomaly label
- schema-change notes
- last-run timestamp

This dataset is intentionally shaped to demonstrate realistic Oracle operations scenarios such as throughput loss, schema drift, and latency spikes.

### Live OCI Telemetry Path
The repository now contains a live OCI integration path in `get_real_oci_telemetry()`. The current implementation reads OCI Data Flow run telemetry from a user-supplied compartment and maps those runs into the dashboard schema using:
- live run lifecycle state
- live current duration
- recent run duration averages
- live executor counts and recent executor-count baselines
- live run timestamps

When live OCI data is unavailable or the compartment has no recent Data Flow activity, the application falls back to the mock telemetry dataset.

## Oracle Assumptions
The project assumes an Oracle enterprise landscape where:
- ODI pipelines may fail due to schema drift, mappings, or upstream source issues
- GoldenGate pipelines may expose replication lag and latency anomalies
- OCI Data Flow pipelines may show throughput loss or schema-type mismatches
- enterprise business systems include Oracle-centric ERP, CRM, HCM, SCM, and warehouse flows

These assumptions are reflected in both the dashboard wording and the BlueVerse prompt context.

## AI Assumptions
The BlueVerse workflows assume that:
- structured pipeline context is sufficient to generate a first-pass root-cause hypothesis
- Oracle-specific language is more useful than generic incident-response phrasing
- remediation suggestions are advisory and should be reviewed by an engineer before production use

## Prototype Boundaries

### Implemented
- dashboard workflows
- local analytics and prioritization logic
- BlueVerse API integration
- graceful failure handling for missing secrets and failed API responses
- live OCI Data Flow run ingestion for a configured compartment

### Not Yet Implemented
- OCI Monitoring metric mapping
- GoldenGate and ODI live metric collectors
- persistent token logging
- persistent cost tracking
- multi-provider LLM fallback

This boundary is important to preserve accuracy in the final submission narrative.
