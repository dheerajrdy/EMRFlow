"""
Simple evaluation harness for scripted conversation scenarios.

Runs test scenarios through the dialogue manager and tracks metrics:
- Success rate (% passing)
- Average latency per scenario
- Pass/fail status for each scenario
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.utils.conversation_state import ConversationState


@dataclass
class EvalMetrics:
    """Metrics collected during evaluation run."""

    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    total_latency_ms: float = 0.0
    scenario_results: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.passed / self.total_scenarios * 100) if self.total_scenarios > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency per scenario."""
        return self.total_latency_ms / self.total_scenarios if self.total_scenarios > 0 else 0.0

    def add_result(
        self,
        name: str,
        passed: bool,
        latency_ms: float,
        error: Optional[str] = None
    ):
        """Add a scenario result to metrics."""
        self.total_scenarios += 1
        if passed:
            self.passed += 1
        else:
            self.failed += 1

        self.total_latency_ms += latency_ms

        self.scenario_results.append({
            "name": name,
            "passed": passed,
            "latency_ms": latency_ms,
            "status": "PASS" if passed else "FAIL",
            "error": error
        })


async def run_eval_scenario(dialogue_manager, scenario: Dict[str, Any]) -> bool:
    """Run a single scenario definition."""
    state = ConversationState()
    last_result = None

    for utterance in scenario["utterances"]:
        last_result = await dialogue_manager.execute({"utterance": utterance, "state": state})
        state = ConversationState.from_dict(last_result.output.get("state", {}))

    assert_fn = scenario.get("assertion")
    if assert_fn:
        return assert_fn(last_result, state)
    return last_result.is_success if last_result else False


async def run_eval_suite(dialogue_manager, scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run all scenarios and return pass/fail results."""
    results = []
    for scenario in scenarios:
        passed = await run_eval_scenario(dialogue_manager, scenario)
        results.append({"name": scenario["name"], "passed": passed})
    return results


async def run_eval_with_metrics(
    dialogue_manager,
    scenarios: List[Dict[str, Any]]
) -> EvalMetrics:
    """
    Run all scenarios and collect detailed metrics.

    Args:
        dialogue_manager: DialogueManager instance
        scenarios: List of scenario definitions

    Returns:
        EvalMetrics with success rate, latency, and per-scenario results
    """
    metrics = EvalMetrics()

    for scenario in scenarios:
        start_time = time.time()
        error_msg = None

        try:
            passed = await run_eval_scenario(dialogue_manager, scenario)
        except Exception as e:
            passed = False
            error_msg = str(e)

        latency_ms = (time.time() - start_time) * 1000

        metrics.add_result(
            name=scenario["name"],
            passed=passed,
            latency_ms=latency_ms,
            error=error_msg
        )

    return metrics


def print_eval_report(metrics: EvalMetrics, verbose: bool = True):
    """
    Print formatted evaluation report.

    Args:
        metrics: EvalMetrics to display
        verbose: If True, show detailed per-scenario results
    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box

        console = Console()

        if verbose:
            # Detailed table
            table = Table(
                title="[bold cyan]Evaluation Results[/bold cyan]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            table.add_column("#", style="dim", width=4)
            table.add_column("Scenario", style="cyan", width=35)
            table.add_column("Status", justify="center", width=10)
            table.add_column("Latency", justify="right", width=12)
            table.add_column("Error", style="dim", width=30)

            for i, result in enumerate(metrics.scenario_results, start=1):
                status_color = "green" if result["passed"] else "red"
                status_symbol = "✓" if result["passed"] else "✗"
                status_text = f"[{status_color}]{status_symbol} {result['status']}[/{status_color}]"

                latency = result.get("latency_ms", 0)
                latency_color = "green" if latency < 500 else "yellow" if latency < 1000 else "red"
                latency_text = f"[{latency_color}]{latency:.1f}ms[/{latency_color}]"

                error_text = result.get("error", "")[:30] if result.get("error") else ""

                table.add_row(
                    str(i),
                    result["name"],
                    status_text,
                    latency_text,
                    error_text
                )

            console.print()
            console.print(table)
            console.print()

        # Summary panel
        outcome_color = "green" if metrics.success_rate >= 90 else "yellow" if metrics.success_rate >= 70 else "red"
        latency_color = "green" if metrics.avg_latency_ms < 500 else "yellow" if metrics.avg_latency_ms < 1000 else "red"

        summary = Panel(
            f"[bold cyan]Total Scenarios:[/bold cyan] {metrics.total_scenarios}\n"
            f"[bold green]Passed:[/bold green] {metrics.passed}\n"
            f"[bold red]Failed:[/bold red] {metrics.failed}\n"
            f"[bold {outcome_color}]Success Rate:[/bold {outcome_color}] [{outcome_color}]{metrics.success_rate:.1f}%[/{outcome_color}]\n"
            f"[bold {latency_color}]Avg Latency:[/bold {latency_color}] [{latency_color}]{metrics.avg_latency_ms:.1f}ms/scenario[/{latency_color}]",
            title="📊 [bold green]Evaluation Summary[/bold green]",
            box=box.DOUBLE,
            border_style=outcome_color
        )

        console.print(summary)
        console.print()

        # Status message
        if metrics.success_rate == 100:
            console.print("[bold green]✓ All scenarios passed! System is ready for demo.[/bold green]")
        elif metrics.success_rate >= 90:
            console.print(f"[bold yellow]⚠ {metrics.failed} scenario(s) failing. Review before demo.[/bold yellow]")
        else:
            console.print(f"[bold red]✗ {metrics.failed} scenarios failing. Needs attention.[/bold red]")

    except ImportError:
        # Fallback: plain text output
        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)

        for i, result in enumerate(metrics.scenario_results, start=1):
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{i}. {result['name']}: {status} ({result['latency_ms']:.1f}ms)")

        print("\n" + "-" * 60)
        print(f"Total Scenarios: {metrics.total_scenarios}")
        print(f"Passed: {metrics.passed}")
        print(f"Failed: {metrics.failed}")
        print(f"Success Rate: {metrics.success_rate:.1f}%")
        print(f"Avg Latency: {metrics.avg_latency_ms:.1f}ms/scenario")
        print("=" * 60 + "\n")


def run_suite_sync(dialogue_manager, scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Synchronous wrapper for convenience."""
    return asyncio.get_event_loop().run_until_complete(run_eval_suite(dialogue_manager, scenarios))
