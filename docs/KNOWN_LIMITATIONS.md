# Known Limitations

## Current Constraints

### Live OCI Coverage
Live ingestion is currently implemented for **OCI Data Flow** run telemetry.  
Live collectors for ODI, GoldenGate, and broader OCI Monitoring/Logging sources are not yet implemented.

### Token And Cost Persistence
The app displays per-request token and cost values in the UI, but it does not yet persist token/cost analytics to a long-term store for trend reporting.

### BlueVerse Authentication Lifecycle
BlueVerse integration is live, but token refresh lifecycle automation is not yet implemented. Expired tokens still require operator update in secrets.

### Action Scope
Governed live action is implemented for OCI Data Flow rerun.  
Cross-service remediation actions (ODI, GoldenGate, database patch orchestration) are not yet implemented.

### Production Hardening
The prototype is demo-ready, but enterprise deployment hardening is still pending:
- centralized secrets/IAM policy templates,
- environment-specific config bundles,
- formal SLO/SLA monitoring and alert routing.

### AI Output Variability
AI remediation quality depends on prompt context and model behavior. Outputs should still be reviewed by an engineer before production execution.

## Near-Term Improvement Path
1. Add OCI Monitoring and OCI Logging collectors to enrich live telemetry.
2. Add live ODI and GoldenGate telemetry adapters.
3. Add persisted token/cost telemetry and reporting.
4. Add policy-controlled action templates for additional Oracle services.
5. Add deployment hardening artifacts (security notes, runbooks, environment baselines).
