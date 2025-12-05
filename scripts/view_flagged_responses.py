#!/usr/bin/env python3
"""
View flagged responses for human review.

Usage:
    python scripts/view_flagged_responses.py
    python scripts/view_flagged_responses.py --threshold 0.6
    python scripts/view_flagged_responses.py --session sess_123
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional


def load_flagged_responses(
    log_file: str = "runs/flagged_responses.jsonl",
    threshold: Optional[float] = None,
    session_id: Optional[str] = None,
) -> List[Dict]:
    """
    Load flagged responses from log file.

    Args:
        log_file: Path to flagged responses JSONL file
        threshold: Optional filter for confidence threshold
        session_id: Optional filter for specific session

    Returns:
        List of flagged response dictionaries
    """
    path = Path(log_file)
    if not path.exists():
        return []

    flagged: List[Dict] = []
    with open(path, "r") as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if threshold is not None and item.get("confidence_score", 1.0) >= threshold:
                continue
            if session_id and item.get("session_id") != session_id:
                continue

            flagged.append(item)

    return flagged


def print_flagged_responses(flagged: List[Dict]) -> None:
    """Print flagged responses in readable format."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        use_rich = True
    except ImportError:  # pragma: no cover - fallback
        use_rich = False

    if not flagged:
        print("No flagged responses found.")
        return

    if use_rich:
        console = Console()

        console.print(
            Panel.fit(
                f"[bold red]Flagged Responses for Human Review[/bold red]\n"
                f"Total: {len(flagged)} responses",
                border_style="red",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session", style="cyan", width=16)
        table.add_column("Turn", style="yellow", width=6)
        table.add_column("Confidence", style="red", width=12)
        table.add_column("Intent", style="green", width=18)
        table.add_column("Query", style="white", width=32)
        table.add_column("Response", style="white", width=40)

        for item in flagged:
            table.add_row(
                str(item.get("session_id", ""))[-16:],
                str(item.get("turn")),
                f"{item.get('confidence_score', 0):.2f}",
                str(item.get("intent", "")),
                _truncate(item.get("user_query", ""), 32),
                _truncate(item.get("agent_response", ""), 40),
            )

        console.print(table)
        return

    # Plain text fallback
    print(f"\n=== Flagged Responses for Human Review ({len(flagged)} total) ===\n")
    for idx, item in enumerate(flagged, 1):
        print(f"{idx}. Session: {item.get('session_id')}, Turn: {item.get('turn')}")
        print(f"   Confidence: {item.get('confidence_score')}")
        print(f"   Intent: {item.get('intent')}")
        print(f"   Query: {item.get('user_query')}")
        print(f"   Response: {item.get('agent_response')}")
        print(f"   Timestamp: {item.get('timestamp')}")
        print()


def _truncate(text: Optional[str], max_len: int) -> str:
    if not text:
        return ""
    return text[: max_len - 3] + "..." if len(text) > max_len else text


def main() -> List[Dict]:
    parser = argparse.ArgumentParser(description="View flagged responses for human review")
    parser.add_argument("--threshold", type=float, help="Only show responses below this confidence score")
    parser.add_argument("--session", type=str, help="Filter by session ID")
    parser.add_argument(
        "--log-file",
        type=str,
        default="runs/flagged_responses.jsonl",
        help="Path to flagged responses log",
    )

    args = parser.parse_args()

    flagged = load_flagged_responses(
        log_file=args.log_file,
        threshold=args.threshold,
        session_id=args.session,
    )
    print_flagged_responses(flagged)
    return flagged


if __name__ == "__main__":
    main()

