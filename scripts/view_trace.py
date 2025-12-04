#!/usr/bin/env python3
"""
Simple trace viewer for conversation logs (runs/*.jsonl).

Usage:
  python scripts/view_trace.py --list
  python scripts/view_trace.py --session SESSION_ID

Renders a table of events using `rich` when available, otherwise prints JSON.
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.storage.conversation_logger import get_conversation_logger


def list_sessions(logger, limit=20):
    sessions = logger.list_conversations(limit=limit)
    for s in sessions:
        print(s)


def show_session(logger, session_id):
    events = logger.get_conversation(session_id)
    if not events:
        print(f"No conversation found for session: {session_id}")
        return

    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#")
        table.add_column("Event")
        table.add_column("Time")
        table.add_column("Turn")
        table.add_column("Utterance")
        table.add_column("Response")
        table.add_column("Intent")
        table.add_column("Status")
        table.add_column("Metadata")

        for i, ev in enumerate(events, start=1):
            table.add_row(
                str(i),
                ev.get("event", ""),
                ev.get("timestamp", ""),
                str(ev.get("turn", "")),
                ev.get("utterance", ""),
                ev.get("response", ""),
                str(ev.get("intent", "")),
                str(ev.get("status", "")),
                json.dumps(ev.get("metadata", {}))[:200],
            )

        console.print(table)

    except Exception:
        # Fallback: plain JSON print
        for ev in events:
            print(json.dumps(ev, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List recent sessions")
    parser.add_argument("--session", type=str, help="Session ID to display")
    parser.add_argument("--limit", type=int, default=20, help="Limit for listing sessions")
    parser.add_argument("--path", type=str, default="runs", help="Path to runs directory")

    args = parser.parse_args()

    logger = get_conversation_logger(storage_path=args.path)

    if args.list:
        list_sessions(logger, limit=args.limit)
        return

    if args.session:
        show_session(logger, args.session)
        return

    # Default: if single JSONL exists, show it; otherwise list
    sessions = logger.list_conversations(limit=2)
    if len(sessions) == 1:
        show_session(logger, sessions[0])
        return

    print("No session specified. Use --list to view sessions or --session SESSION_ID to inspect one.")


if __name__ == "__main__":
    main()
