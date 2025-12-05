from datetime import datetime, timedelta
import json

from src.metrics.metrics_aggregator import MetricsAggregator


def _write_session_log(path, session_id, start_time, intents, confidences, latencies, outcome="success"):
    with open(path, "w") as f:
        f.write(
            json.dumps({"session_id": session_id, "event": "call_start", "timestamp": start_time.isoformat()})
            + "\n"
        )
        f.write(
            json.dumps(
                {"session_id": session_id, "event": "authentication_success", "timestamp": start_time.isoformat()}
            )
            + "\n"
        )
        for idx, intent in enumerate(intents):
            f.write(
                json.dumps(
                    {
                        "session_id": session_id,
                        "event": "turn",
                        "turn": idx + 1,
                        "intent": intent,
                        "latency_ms": latencies[idx],
                        "confidence_score": confidences[idx],
                        "timestamp": (start_time + timedelta(seconds=idx + 1)).isoformat(),
                        "metadata": {"retry_count": idx},
                    }
                )
                + "\n"
            )

        f.write(
            json.dumps(
                {
                    "session_id": session_id,
                    "event": "call_end",
                    "timestamp": (start_time + timedelta(seconds=10)).isoformat(),
                    "outcome": outcome,
                }
            )
            + "\n"
        )


def test_load_session_metrics(tmp_path):
    session_file = tmp_path / "sess_a.jsonl"
    start_time = datetime.now()
    _write_session_log(
        session_file,
        session_id="sess_a",
        start_time=start_time,
        intents=["FAQ", "ScheduleAppointment"],
        confidences=[0.9, 0.6],
        latencies=[1200, 800],
    )

    aggregator = MetricsAggregator(runs_dir=str(tmp_path))
    metrics = aggregator.load_session_metrics(session_file)

    assert metrics.session_id == "sess_a"
    assert metrics.total_turns == 2
    assert metrics.confidence_scores == [0.9, 0.6]
    assert metrics.latencies_ms == [1200, 800]
    assert metrics.patient_authenticated is True
    assert metrics.retry_counts == [0, 1]


def test_aggregate_metrics(tmp_path):
    start_time = datetime.now()
    _write_session_log(
        tmp_path / "sess_a.jsonl",
        session_id="sess_a",
        start_time=start_time,
        intents=["FAQ"],
        confidences=[0.9],
        latencies=[1000],
    )
    _write_session_log(
        tmp_path / "sess_b.jsonl",
        session_id="sess_b",
        start_time=start_time - timedelta(days=1),
        intents=["Other"],
        confidences=[0.4],
        latencies=[2000],
        outcome="failure",
    )

    aggregator = MetricsAggregator(runs_dir=str(tmp_path))
    metrics = aggregator.aggregate_metrics(time_window=timedelta(days=2))

    assert metrics.total_sessions == 2
    assert metrics.successful_sessions == 1
    assert metrics.total_turns == 2
    assert metrics.low_confidence_count >= 1
    assert "FAQ" in metrics.intent_distribution
    assert metrics.p50_latency_ms >= 1000
