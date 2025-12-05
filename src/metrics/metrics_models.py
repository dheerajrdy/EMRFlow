from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class SessionMetrics:
    """Metrics for a single conversation session."""

    session_id: str
    timestamp: datetime
    total_turns: int
    intents: List[str]
    latencies_ms: List[float]
    confidence_scores: List[float]
    errors: List[str]
    success: bool
    duration_seconds: float
    patient_authenticated: bool
    retry_counts: List[int] = field(default_factory=list)


@dataclass
class AggregateMetrics:
    """Aggregate metrics across multiple sessions."""

    time_window: str
    total_sessions: int
    successful_sessions: int
    success_rate: float
    total_turns: int
    avg_turns_per_session: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    intent_distribution: Dict[str, int]
    error_distribution: Dict[str, int]
    low_confidence_count: int
    low_confidence_rate: float
    avg_confidence_score: float
    retry_count_distribution: Dict[int, int] = field(default_factory=dict)
