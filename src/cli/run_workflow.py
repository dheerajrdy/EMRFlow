"""
CLI entry point for EMRFlow workflows.

Based on CodeFlow CLI pattern.
"""

import asyncio
import click
import yaml
import logging
from pathlib import Path
from typing import Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """EMRFlow - Multi-agent workflow system for healthcare."""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Config file path')
@click.option('--dry-run', is_flag=True, help='Dry run without executing external operations')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(config: Optional[str], dry_run: bool, verbose: bool):
    """
    Run EMRFlow workflow.

    TODO: Implement based on specific healthcare use case.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("EMRFlow workflow runner")

    # Load config
    config_path = config or "config/config.yaml"
    if not Path(config_path).exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please create config.yaml from config.template.yaml")
        sys.exit(1)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    logger.info(f"Loaded config from {config_path}")

    if dry_run:
        logger.info("DRY RUN MODE - No external operations will be performed")

    # TODO: Implement workflow execution based on healthcare use case
    logger.info("Workflow execution not yet implemented")
    logger.info("Define healthcare use case and agents first")


@cli.command()
@click.option('--limit', '-n', type=int, default=10, help='Number of runs to show')
@click.option('--status', type=click.Choice(['success', 'failure', 'pending', 'running']), help='Filter by status')
def list_runs(limit: int, status: Optional[str]):
    """List recent workflow runs."""
    from src.storage.run_storage import JSONLRunStorage

    async def _list():
        storage = JSONLRunStorage()
        runs = await storage.list_runs(limit=limit, status=status)

        if not runs:
            click.echo("No runs found")
            return

        click.echo(f"\nFound {len(runs)} runs:\n")
        for run in runs:
            click.echo(f"ID: {run['workflow_id']}")
            click.echo(f"  Status: {run['status']}")
            click.echo(f"  Created: {run.get('created_at', 'N/A')}")
            click.echo(f"  Errors: {len(run.get('errors', []))}")
            click.echo()

    asyncio.run(_list())


@cli.command()
@click.argument('workflow_id')
def show_run(workflow_id: str):
    """Show details of a specific workflow run."""
    from src.storage.run_storage import JSONLRunStorage

    async def _show():
        storage = JSONLRunStorage()
        context = await storage.get_run(workflow_id)

        if not context:
            click.echo(f"Run not found: {workflow_id}")
            return

        click.echo(f"\nWorkflow Run: {workflow_id}")
        click.echo(f"Status: {context.status.value}")
        click.echo(f"Created: {context.created_at}")
        click.echo(f"Updated: {context.updated_at}")

        click.echo("\nStep Results:")
        for step_name, result in context.step_results.items():
            click.echo(f"  {step_name}: {result}")

        if context.errors:
            click.echo("\nErrors:")
            for error in context.errors:
                click.echo(f"  - {error}")

        click.echo("\nMetadata:")
        for key, value in context.metadata.items():
            click.echo(f"  {key}: {value}")

    asyncio.run(_show())


@cli.command()
def stats():
    """Show workflow statistics."""
    from src.storage.run_storage import JSONLRunStorage

    async def _stats():
        storage = JSONLRunStorage()
        stats = await storage.get_run_stats()

        click.echo("\nWorkflow Statistics:")
        click.echo(f"  Total runs: {stats['total_runs']}")
        click.echo(f"  Successful: {stats['success_count']}")
        click.echo(f"  Failed: {stats['failure_count']}")
        click.echo(f"  Success rate: {stats['success_rate']:.1%}")

        if stats['most_recent']:
            click.echo(f"  Most recent: {stats['most_recent']}")

    asyncio.run(_stats())


@cli.command()
def version():
    """Show EMRFlow version."""
    click.echo("EMRFlow v0.1.0 (Development)")


if __name__ == '__main__':
    cli()
