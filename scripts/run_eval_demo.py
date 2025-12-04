#!/usr/bin/env python3
"""
Demo script to run evaluation harness with metrics reporting.

Usage:
  python scripts/run_eval_demo.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluation.test_scenarios import FakeDialogueManager, build_scenarios
from tests.evaluation.eval_runner import run_eval_with_metrics, print_eval_report


async def main():
    """Run evaluation with metrics and display report."""
    print("🚀 Starting EMRFlow Evaluation Harness\n")

    # Initialize dialogue manager and scenarios
    dm = FakeDialogueManager()
    scenarios = build_scenarios()

    print(f"📋 Running {len(scenarios)} test scenarios...\n")

    # Run evaluation with metrics
    metrics = await run_eval_with_metrics(dm, scenarios)

    # Display formatted report
    print_eval_report(metrics, verbose=True)

    # Return exit code based on success
    return 0 if metrics.success_rate == 100 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
