def get_status_emoji(status):
    return {"SUCCESS": "🟢", "WARNING": "🟡", "FAILED": "🔴"}.get(status, "⚪")


def get_health_score(pipeline):
    score = 100

    if pipeline["expected_rows"] > 0:
        ratio = pipeline["actual_rows"] / pipeline["expected_rows"]
        if ratio < 0.7:
            score -= 40
        elif ratio < 0.9:
            score -= 20

    if pipeline["avg_duration_minutes"] > 0:
        latency_ratio = pipeline["duration_minutes"] / pipeline["avg_duration_minutes"]
        if latency_ratio > 5:
            score -= 30
        elif latency_ratio > 2:
            score -= 15

    if pipeline["schema_changes"]:
        score -= 20

    if pipeline["status"] == "FAILED":
        score -= 30

    return max(0, score)


def predict_failure(pipeline):
    risk = 0
    reasons = []

    if pipeline["anomaly_detected"] != "None":
        risk += 40
        reasons.append(pipeline["anomaly_detected"])

    if pipeline["expected_rows"] > 0:
        ratio = pipeline["actual_rows"] / pipeline["expected_rows"]
        if ratio < 0.9:
            risk += 30
            if "Volume Drop" not in reasons:
                reasons.append("Volume drop trend")

    if pipeline["avg_duration_minutes"] > 0:
        latency_ratio = pipeline["duration_minutes"] / pipeline["avg_duration_minutes"]
        if latency_ratio > 1.5:
            risk += 20
            if "Latency Spike" not in reasons:
                reasons.append("Latency creeping up")

    if pipeline["schema_changes"]:
        risk += 30
        if "Schema Drift" not in reasons:
            reasons.append("Schema instability")

    if pipeline["status"] == "FAILED":
        risk = 95
        reasons = [pipeline["anomaly_detected"]]

    if risk >= 70:
        return f"🚨 CRITICAL ({risk}%) — {', '.join(reasons)}"
    if risk >= 40:
        return f"⚠️ ELEVATED ({risk}%) — {', '.join(reasons)}"
    return f"✅ STABLE ({risk}%)"
