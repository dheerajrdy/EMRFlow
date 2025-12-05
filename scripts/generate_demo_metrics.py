#!/usr/bin/env python3
"""
Generate synthetic conversation logs for metrics demo.

Usage:
    python scripts/generate_demo_metrics.py
    python scripts/generate_demo_metrics.py --sessions 100
"""

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_demo_conversation_logs(num_sessions: int = 50):
    """
    Generate synthetic conversation logs for metrics demo.
    """
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)

    intents = [
        "ScheduleAppointment",
        "RescheduleAppointment",
        "CancelAppointment",
        "InfoQuery",
        "FAQ",
        "Other",
    ]

    intent_weights = [0.35, 0.20, 0.10, 0.20, 0.10, 0.05]

    print(f"Generating {num_sessions} synthetic conversation logs...")

    for i in range(num_sessions):
        session_id = f"demo_session_{i:03d}"
        log_file = runs_dir / f"{session_id}.jsonl"

        num_turns = random.randint(2, 8)
        has_error = random.random() < 0.15
        is_authenticated = random.random() < 0.80

        start_time = datetime.now() - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        with open(log_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "session_id": session_id,
                        "event": "call_start",
                        "timestamp": start_time.isoformat(),
                    }
                )
                + "\n"
            )

            if is_authenticated:
                auth_time = start_time + timedelta(seconds=3)
                f.write(
                    json.dumps(
                        {
                            "session_id": session_id,
                            "event": "authentication_success",
                            "timestamp": auth_time.isoformat(),
                        }
                    )
                    + "\n"
                )

            current_time = start_time + timedelta(seconds=5)

            for turn in range(num_turns):
                intent = random.choices(intents, weights=intent_weights)[0]

                if random.random() < 0.05:
                    latency = random.randint(5000, 10000)
                else:
                    latency = random.randint(800, 3500)

                if has_error and turn == num_turns - 1:
                    confidence = random.uniform(0.3, 0.6)
                    retry_count = random.randint(1, 3)
                else:
                    confidence = random.uniform(0.7, 1.0)
                    retry_count = 0

                turn_event = {
                    "session_id": session_id,
                    "event": "turn",
                    "turn": turn + 1,
                    "intent": intent,
                    "entities": {},
                    "latency_ms": latency,
                    "confidence_score": confidence,
                    "timestamp": current_time.isoformat(),
                    "metadata": {"retry_count": retry_count},
                }

                if has_error and turn == num_turns - 1:
                    turn_event["error"] = random.choice(
                        ["NLU_LOW_CONFIDENCE", "SLOT_UNAVAILABLE", "AUTHENTICATION_FAILED"]
                    )

                f.write(json.dumps(turn_event) + "\n")

                current_time += timedelta(seconds=latency / 1000 + random.randint(2, 5))

            outcome = "failure" if has_error else "success"
            f.write(
                json.dumps(
                    {
                        "session_id": session_id,
                        "event": "call_end",
                        "timestamp": current_time.isoformat(),
                        "outcome": outcome,
                    }
                )
                + "\n"
            )

    print(f"✓ Generated {num_sessions} conversation logs in {runs_dir}/")
    print("  View with: python scripts/view_metrics_dashboard.py")


def main():
    parser = argparse.ArgumentParser(description="Generate demo conversation logs")
    parser.add_argument("--sessions", type=int, default=50, help="Number of sessions to generate")

    args = parser.parse_args()

    generate_demo_conversation_logs(args.sessions)


if __name__ == "__main__":
    main()

