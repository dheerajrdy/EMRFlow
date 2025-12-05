#!/usr/bin/env python3
"""
View production metrics dashboard.

Usage:
    python scripts/view_metrics_dashboard.py
    python scripts/view_metrics_dashboard.py --days 30
    python scripts/view_metrics_dashboard.py --export metrics.json
"""

import argparse
import json
from datetime import timedelta

from src.metrics.metrics_aggregator import MetricsAggregator


def print_metrics_dashboard(time_window_days: int = 7, export_file: str = None):
    """
    Display production metrics dashboard.
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        use_rich = True
    except ImportError:  # pragma: no cover - fallback
        use_rich = False

    aggregator = MetricsAggregator()

    try:
        metrics = aggregator.aggregate_metrics(timedelta(days=time_window_days))
    except ValueError as e:
        print(f"Error: {e}")
        return

    if use_rich:
        _print_rich_dashboard(metrics, time_window_days)
    else:
        _print_plain_dashboard(metrics, time_window_days)

    if export_file:
        with open(export_file, "w") as f:
            json.dump(metrics.__dict__, f, indent=2, default=str)
        print(f"\nMetrics exported to {export_file}")

    return metrics


def _print_rich_dashboard(metrics, time_window_days: int):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    console = Console()

    console.print(
        Panel.fit(
            f"[bold cyan]EMRFlow Production Metrics Dashboard[/bold cyan]\n"
            f"Time Window: Last {time_window_days} days",
            border_style="cyan",
        )
    )

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Metric", style="cyan", width=25)
    summary.add_column("Value", style="magenta", width=20)

    summary.add_row("Total Sessions", str(metrics.total_sessions))
    summary.add_row("Successful Sessions", str(metrics.successful_sessions))
    summary.add_row(
        "Success Rate",
        f"[{'green' if metrics.success_rate >= 0.9 else 'yellow' if metrics.success_rate >= 0.7 else 'red'}]"
        f"{metrics.success_rate:.1%}[/]",
    )
    summary.add_row("Total Turns", str(metrics.total_turns))
    summary.add_row("Avg Turns/Session", f"{metrics.avg_turns_per_session:.1f}")

    console.print(Panel(summary, title="📊 Summary", border_style="green"))

    latency = Table(show_header=False, box=None, padding=(0, 2))
    latency.add_column("Metric", style="cyan", width=25)
    latency.add_column("Value", style="magenta", width=20)

    latency.add_row("Average Latency", f"{metrics.avg_latency_ms:.0f} ms")
    latency.add_row("P50 Latency", f"{metrics.p50_latency_ms:.0f} ms")
    latency.add_row("P95 Latency", f"{metrics.p95_latency_ms:.0f} ms")
    latency.add_row("P99 Latency", f"{metrics.p99_latency_ms:.0f} ms")

    console.print(Panel(latency, title="⚡ Latency", border_style="yellow"))

    confidence = Table(show_header=False, box=None, padding=(0, 2))
    confidence.add_column("Metric", style="cyan", width=25)
    confidence.add_column("Value", style="magenta", width=20)

    confidence.add_row("Avg Confidence Score", f"{metrics.avg_confidence_score:.2f}")
    confidence.add_row("Low Confidence Responses", str(metrics.low_confidence_count))
    confidence.add_row("Low Confidence Rate", f"{metrics.low_confidence_rate:.1%}")

    console.print(Panel(confidence, title="🎯 Confidence", border_style="blue"))

    intent_table = Table(title="🎤 Intent Distribution")
    intent_table.add_column("Intent", style="yellow", width=25)
    intent_table.add_column("Count", style="green", width=10)
    intent_table.add_column("Percentage", style="cyan", width=12)

    total_intents = sum(metrics.intent_distribution.values())
    for intent, count in sorted(metrics.intent_distribution.items(), key=lambda x: -x[1]):
        pct = count / total_intents if total_intents > 0 else 0
        intent_table.add_row(intent, str(count), f"{pct:.1%}")

    console.print(intent_table)

    if metrics.error_distribution:
        error_table = Table(title="❌ Error Distribution", title_style="red")
        error_table.add_column("Error Type", style="red", width=40)
        error_table.add_column("Count", style="yellow", width=10)

        for error, count in sorted(metrics.error_distribution.items(), key=lambda x: -x[1]):
            error_table.add_row(error, str(count))

        console.print(error_table)
    else:
        console.print(Panel("[green]No errors recorded! ✓[/green]", title="❌ Errors"))


def _print_plain_dashboard(metrics, time_window_days: int):
    print(f"\n{'=' * 60}")
    print("EMRFlow Production Metrics Dashboard")
    print(f"Time Window: Last {time_window_days} days")
    print(f"{'=' * 60}\n")

    print("SUMMARY:")
    print(f"  Total Sessions: {metrics.total_sessions}")
    print(f"  Successful Sessions: {metrics.successful_sessions}")
    print(f"  Success Rate: {metrics.success_rate:.1%}")
    print(f"  Total Turns: {metrics.total_turns}")
    print(f"  Avg Turns/Session: {metrics.avg_turns_per_session:.1f}")
    print()

    print("LATENCY:")
    print(f"  Average: {metrics.avg_latency_ms:.0f} ms")
    print(f"  P50: {metrics.p50_latency_ms:.0f} ms")
    print(f"  P95: {metrics.p95_latency_ms:.0f} ms")
    print(f"  P99: {metrics.p99_latency_ms:.0f} ms")
    print()

    print("CONFIDENCE:")
    print(f"  Avg Score: {metrics.avg_confidence_score:.2f}")
    print(f"  Low Confidence Count: {metrics.low_confidence_count}")
    print(f"  Low Confidence Rate: {metrics.low_confidence_rate:.1%}")
    print()

    print("INTENT DISTRIBUTION:")
    total_intents = sum(metrics.intent_distribution.values())
    for intent, count in sorted(metrics.intent_distribution.items(), key=lambda x: -x[1]):
        pct = count / total_intents if total_intents > 0 else 0
        print(f"  {intent}: {count} ({pct:.1%})")
    print()

    if metrics.error_distribution:
        print("ERROR DISTRIBUTION:")
        for error, count in sorted(metrics.error_distribution.items(), key=lambda x: -x[1]):
            print(f"  {error}: {count}")
    else:
        print("ERRORS: None ✓")

    print()


def main():
    parser = argparse.ArgumentParser(description="View production metrics dashboard")
    parser.add_argument("--days", type=int, default=7, help="Number of days to aggregate metrics over")
    parser.add_argument("--export", type=str, help="Export metrics to JSON file")

    args = parser.parse_args()

    print_metrics_dashboard(time_window_days=args.days, export_file=args.export)


if __name__ == "__main__":
    main()

