# Test Plan

## Objective
The testing approach for this project is focused on three goals:
- verify that Oracle-style anomaly scenarios appear correctly in the dashboard
- verify that BlueVerse integration behaves safely under normal and failure conditions
- ensure the demo experience remains clear and stable even when live dependencies are unavailable

## Functional Validation Scope
The core functional scenarios covered by the project are:
1. GoldenGate latency spike is visible in the fleet overview.
2. ODI schema drift appears in the remediation workflow.
3. OCI Data Flow volume drop appears in the throughput view.
4. Health score decreases appropriately for failed pipelines.
5. Predictive prioritization surfaces the weakest pipelines first.
6. AI remediation is generated from the selected pipeline context.
7. Support chat answers using the current telemetry snapshot.
8. Refresh clears cached mock telemetry and reruns the app.
9. Live telemetry mode falls back to mock data when OCI integration is unavailable.
10. Mixed Oracle pipeline types are rendered together in one operational view.

## Edge-Case Coverage
The design explicitly validates:
1. Missing BlueVerse secrets
2. BlueVerse timeout
3. BlueVerse HTTP failure
4. BlueVerse non-JSON response
5. Missing OCI SDK
6. Empty live telemetry result
7. Pipelines with no anomaly
8. Pipelines with schema changes but stable latency
9. Pipelines with zero or near-zero throughput
10. Chat use before any existing session history

## Quality Checks
Quality review focuses on:
- Oracle-specific language in AI responses
- alignment between anomaly type and remediation suggestion
- clear user feedback when AI features are unavailable
- readable dashboard sections for a short live demo
- preservation of usability even when external dependencies fail

## Automated Test Coverage
The current repo includes automated regression tests in `tests/test_analytics.py` for:
- health-score baseline behavior
- compound score degradation under bad telemetry
- critical prediction for failed pipelines
- elevated prediction for warning pipelines

## Performance Intent
This prototype is optimized for a demo-ready single-user experience. Startup time, chart responsiveness, and BlueVerse response latency should be verified during final rehearsal and recorded in `TEST_RESULTS.md`.
