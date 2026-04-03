from analytics import get_health_score, predict_failure


def make_pipeline(**overrides):
    pipeline = {
        "pipeline_name": "test_pipeline",
        "type": "ODI",
        "source": "Source",
        "target": "Target",
        "status": "SUCCESS",
        "expected_rows": 100,
        "actual_rows": 100,
        "duration_minutes": 10,
        "avg_duration_minutes": 10,
        "anomaly_detected": "None",
        "schema_changes": [],
        "last_run": "2026-04-02 00:00:00",
    }
    pipeline.update(overrides)
    return pipeline


def test_health_score_starts_at_100_for_healthy_pipeline():
    assert get_health_score(make_pipeline()) == 100


def test_health_score_drops_for_volume_latency_schema_and_failure():
    pipeline = make_pipeline(
        status="FAILED",
        actual_rows=20,
        duration_minutes=80,
        avg_duration_minutes=10,
        schema_changes=["column renamed"],
    )

    assert get_health_score(pipeline) == 0


def test_predict_failure_marks_failed_pipeline_critical():
    pipeline = make_pipeline(
        status="FAILED",
        anomaly_detected="Schema Drift & Volume Drop",
        actual_rows=0,
        schema_changes=["column renamed"],
    )

    assert predict_failure(pipeline) == "🚨 CRITICAL (95%) — Schema Drift & Volume Drop"


def test_predict_failure_marks_warning_pipeline_elevated():
    pipeline = make_pipeline(
        status="WARNING",
        anomaly_detected="Latency Spike",
        duration_minutes=25,
        avg_duration_minutes=10,
    )

    assert predict_failure(pipeline) == "⚠️ ELEVATED (60%) — Latency Spike, Latency creeping up"


def test_oracle_scenario_goldengate_abend():
    pipeline = make_pipeline(
        type="GoldenGate",
        status="FAILED",
        anomaly_detected="Extract Abend & Giant LAG",
        actual_rows=0,
        expected_rows=500000,
        duration_minutes=240,
        avg_duration_minutes=8,
    )
    assert get_health_score(pipeline) == 0
    assert "CRITICAL (95%)" in predict_failure(pipeline)


def test_oracle_scenario_fusion_crm_schema_drift():
    pipeline = make_pipeline(
        type="ODI 12c",
        source="Fusion Sales Cloud",
        status="FAILED",
        schema_changes=["OPPORTUNITY_ID type changed"],
        anomaly_detected="Schema Drift & ORA-00904"
    )
    score = get_health_score(pipeline)
    assert score == 50  # 100 - 20 (schema) - 30 (failed)


def test_oracle_scenario_oci_data_flow_volume_drop():
    pipeline = make_pipeline(
        type="OCI Data Flow",
        status="WARNING",
        anomaly_detected="Volume Drop (75%)",
        expected_rows=5000000,
        actual_rows=1250000, # < 0.7 ratio
    )
    assert get_health_score(pipeline) == 60 # 100 - 40


def test_oracle_scenario_jde_latency_spike():
    pipeline = make_pipeline(
        source="JD Edwards EnterpriseOne",
        status="WARNING",
        anomaly_detected="Latency Spike (Agent Memory Pressure)",
        duration_minutes=78,
        avg_duration_minutes=45, # ratio 1.7
    )
    pred = predict_failure(pipeline)
    assert "ELEVATED" in pred
    assert "Latency creeping up" in pred


def test_oracle_scenario_autonomous_db_precision_error():
    pipeline = make_pipeline(
        target="Autonomous JSON Database",
        status="FAILED",
        anomaly_detected="Volume Drop & ORA-01438",
        schema_changes=["SENSOR_TEMP precision exceeded column threshold"],
    )
    assert "ORA-01438" in predict_failure(pipeline)


def test_oracle_scenario_mysql_heatwave_checkpoint_lag():
    pipeline = make_pipeline(
        target="OCI MySQL HeatWave",
        status="WARNING",
        duration_minutes=45,
        avg_duration_minutes=12,
        anomaly_detected="Replicat Checkpoint Lag Spike",
    )
    assert get_health_score(pipeline) == 70  # 100 - 30 (latency ratio > 2)


def test_oracle_scenario_epm_automate_timeout():
    pipeline = make_pipeline(
        type="EPM Automate",
        target="EPM Cloud (PBCS)",
        status="FAILED",
        anomaly_detected="Authentication Timeout & Zero Load",
        expected_rows=15000,
        actual_rows=0,
    )
    assert get_health_score(pipeline) <= 30
