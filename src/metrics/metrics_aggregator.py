import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.metrics.metrics_models import AggregateMetrics, SessionMetrics


class MetricsAggregator:
    """
    Aggregate metrics from conversation logs.
    """

    def __init__(self, runs_dir: str = "runs"):
        self.runs_dir = Path(runs_dir)

    def load_session_metrics(self, session_file: Path) -> SessionMetrics:
        """
        Parse single JSONL conversation log into SessionMetrics.
        """
        intents: List[str] = []
        latencies: List[float] = []
        confidences: List[float] = []
        errors: List[str] = []
        retry_counts: List[int] = []
        authenticated = False
        start_time = None
        end_time = None

        with open(session_file, "r") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_name = event.get("event")
                timestamp = event.get("timestamp")

                if event_name == "call_start" and timestamp:
                    start_time = self._parse_timestamp(timestamp)

                if event_name == "turn":
                    intents.append(event.get("intent", "Unknown"))
                    if event.get("latency_ms") is not None:
                        try:
                            latencies.append(float(event["latency_ms"]))
                        except (TypeError, ValueError):
                            pass

                    confidence = event.get("confidence_score")
                    if confidence is None:
                        confidence = event.get("metadata", {}).get("confidence_score")
                    if confidence is None:
                        confidence = 1.0
                    try:
                        confidences.append(float(confidence))
                    except (TypeError, ValueError):
                        confidences.append(1.0)

                    retry_val = event.get("metadata", {}).get("retry_count")
                    if retry_val is not None:
                        try:
                            retry_counts.append(int(retry_val))
                        except (TypeError, ValueError):
                            pass

                if event_name == "authentication_success":
                    authenticated = True

                if event_name == "error":
                    errors.append(
                        event.get("error")
                        or event.get("error_type")
                        or event.get("error_message")
                        or "UnknownError"
                    )

                if event.get("error") and event_name != "error":
                    errors.append(event.get("error"))

                if event_name == "call_end" and timestamp:
                    end_time = self._parse_timestamp(timestamp)
                    if event.get("outcome") == "failure":
                        errors.append("call_failure")

        success = len(errors) == 0 and len(intents) > 0

        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0.0
            if start_time and not end_time:
                # Best-effort duration using file modified time
                duration = (datetime.fromtimestamp(session_file.stat().st_mtime) - start_time).total_seconds()

        return SessionMetrics(
            session_id=session_file.stem,
            timestamp=start_time or datetime.fromtimestamp(session_file.stat().st_mtime),
            total_turns=len(intents),
            intents=intents,
            latencies_ms=latencies,
            confidence_scores=confidences,
            errors=errors,
            success=success,
            duration_seconds=duration,
            patient_authenticated=authenticated,
            retry_counts=retry_counts,
        )

    def aggregate_metrics(self, time_window: timedelta = timedelta(days=7)) -> AggregateMetrics:
        """
        Aggregate metrics across all sessions in time window.
        """
        cutoff = datetime.now() - time_window

        all_sessions: List[SessionMetrics] = []
        for session_file in self.runs_dir.rglob("*.jsonl"):
            if session_file.name in {"flagged_responses.jsonl", "runs.jsonl"}:
                continue

            metrics = self.load_session_metrics(session_file)
            if metrics.timestamp >= cutoff:
                all_sessions.append(metrics)

        if not all_sessions:
            raise ValueError("No sessions found in time window")

        total_sessions = len(all_sessions)
        successful_sessions = sum(1 for s in all_sessions if s.success)
        success_rate = successful_sessions / total_sessions if total_sessions else 0.0

        total_turns = sum(s.total_turns for s in all_sessions)
        avg_turns = total_turns / total_sessions if total_sessions else 0.0

        all_latencies = [lat for s in all_sessions for lat in s.latencies_ms]
        avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
        p50_latency = self._percentile(all_latencies, 50)
        p95_latency = self._percentile(all_latencies, 95)
        p99_latency = self._percentile(all_latencies, 99)

        all_intents = [intent for s in all_sessions for intent in s.intents]
        intent_dist = {intent: all_intents.count(intent) for intent in set(all_intents)} if all_intents else {}

        all_errors = [error for s in all_sessions for error in s.errors]
        error_dist = {error: all_errors.count(error) for error in set(all_errors)} if all_errors else {}

        all_confidences = [conf for s in all_sessions for conf in s.confidence_scores]
        low_conf_count = sum(1 for conf in all_confidences if conf < 0.7)
        low_conf_rate = low_conf_count / len(all_confidences) if all_confidences else 0
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 1.0

        all_retries = [rc for s in all_sessions for rc in s.retry_counts]
        retry_dist = {rc: all_retries.count(rc) for rc in set(all_retries)} if all_retries else {}

        return AggregateMetrics(
            time_window=str(time_window),
            total_sessions=total_sessions,
            successful_sessions=successful_sessions,
            success_rate=success_rate,
            total_turns=total_turns,
            avg_turns_per_session=avg_turns,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            intent_distribution=intent_dist,
            error_distribution=error_dist,
            low_confidence_count=low_conf_count,
            low_confidence_rate=low_conf_rate,
            avg_confidence_score=avg_confidence,
            retry_count_distribution=retry_dist,
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        """Parse ISO timestamps, tolerating trailing Z."""
        try:
            if value.endswith("Z"):
                value = value[:-1]
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.fromtimestamp(0)

    @staticmethod
    def _percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
