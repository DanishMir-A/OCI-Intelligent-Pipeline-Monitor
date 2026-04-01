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
