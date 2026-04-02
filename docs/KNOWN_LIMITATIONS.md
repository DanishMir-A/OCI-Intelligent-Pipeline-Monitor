# Known Limitations

## Current Constraints

### Live OCI Telemetry
The application includes a future OCI integration hook, but the current dashboard experience is still driven primarily by mock telemetry rather than live OCI Monitoring data.

### Token And Cost Logging
The prototype does not yet persist prompt-token, completion-token, or per-request cost metrics.

### Single LLM Provider
The current implementation uses BlueVerse as the primary model layer and supports graceful degradation when it is unavailable, but it does not yet switch automatically to a second provider.

### Benchmark Automation
The dashboard is demo-ready, but startup time, response latency, and concurrency observations are not yet captured automatically inside the product.

### Mock Scenario Dependence
The anomaly scenarios are realistic and Oracle-shaped, but they are still simulated rather than sourced from a live enterprise estate.

### AI Output Variability
Remediation quality depends on the relevance and precision of BlueVerse responses. Outputs should be treated as engineering guidance rather than production-safe automation without review.

## Near-Term Improvement Path
- implement OCI Monitoring metric mapping
- add token and cost logging
- add a policy-approved fallback model layer
- expand automated test coverage
- add richer operational export and incident-report workflows
