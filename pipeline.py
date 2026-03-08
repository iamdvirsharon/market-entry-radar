"""
Market Entry Radar -- Core Pipeline Logic

Reusable pipeline that can be called from both CLI (run.py) and Web UI (app.py).
Runs all 5 steps: DISCOVER → SCRAPE → ANALYZE → ENRICH → DELIVER.
"""

import sys
import time
from pathlib import Path
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from steps import (
    step_01_discover,
    step_02_scrape,
    step_03_analyze,
    step_04_enrich,
    step_05_deliver,
)

console = Console()


def run_pipeline(
    config: dict,
    env: dict,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict:
    """
    Run the full Market Entry Radar pipeline.

    Args:
        config: Configuration dict (same shape as config.yaml)
        env: Environment variables dict with API keys
        progress_callback: Optional callback(step_number, message) for UI updates.
                          step_number is 1-5, message describes current activity.

    Returns:
        dict with all pipeline results and report path
    """
    market = config["target_market"].upper()

    def _notify(step: int, message: str):
        if progress_callback:
            progress_callback(step, message)

    # =========================================================
    # STEP 1: DISCOVER
    # =========================================================
    _notify(1, "Discovering local competitors via geo-targeted SERP queries...")
    discovery_data = step_01_discover.run(config, env)

    if not discovery_data["competitors"]:
        raise RuntimeError("No competitors discovered. Check your config and API keys.")

    _notify(1, f"Discovered {len(discovery_data['competitors'])} competitors")

    # =========================================================
    # STEP 2: SCRAPE
    # =========================================================
    _notify(2, "Scraping competitor websites via Web Unlocker...")
    scrape_data = step_02_scrape.run(config, env, discovery_data)

    if scrape_data["success_count"] == 0:
        raise RuntimeError("No pages scraped successfully. Check your Bright Data zone config.")

    _notify(2, f"Scraped {scrape_data['success_count']} pages")

    # =========================================================
    # STEP 3: ANALYZE
    # =========================================================
    _notify(3, "Running Claude AI analysis (positioning, pricing, content gaps)...")
    analysis_data = step_03_analyze.run(config, env, discovery_data, scrape_data)
    _notify(3, "Analysis complete")

    # =========================================================
    # STEP 4: ENRICH
    # =========================================================
    _notify(4, "Enriching with market-specific intelligence...")
    enrichment_data = step_04_enrich.run(config, env, analysis_data, scrape_data)
    _notify(4, "Enrichment complete")

    # =========================================================
    # STEP 5: DELIVER
    # =========================================================
    _notify(5, "Generating Market Entry Brief...")
    report_data = step_05_deliver.run(config, env, discovery_data, scrape_data, analysis_data, enrichment_data)
    _notify(5, "Report generated")

    return {
        "discovery_data": discovery_data,
        "scrape_data": scrape_data,
        "analysis_data": analysis_data,
        "enrichment_data": enrichment_data,
        "report_data": report_data,
    }


def display_config_panel(config: dict):
    """Display the run configuration in a Rich panel (CLI only)."""
    market = config["target_market"].upper()
    category = config["product"]["category"]

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="bold")
    info_table.add_column()
    info_table.add_row("Product", config["product"]["description"])
    info_table.add_row("Category", category)
    info_table.add_row("Target Market", market)
    info_table.add_row("Homepage", config["product"]["homepage_url"])
    info_table.add_row("Max Competitors", str(config["advanced"]["max_competitors"]))
    info_table.add_row("Max Queries", str(config["advanced"]["max_queries"]))

    console.print(Panel(info_table, title="[bold]Run Configuration[/bold]", border_style="cyan"))


def display_completion_panel(config: dict, results: dict):
    """Display the completion panel (CLI only)."""
    market = config["target_market"].upper()
    discovery_data = results["discovery_data"]
    scrape_data = results["scrape_data"]
    report_data = results["report_data"]

    console.print("\n")
    console.print(Panel(
        f"""[bold green]Pipeline complete![/bold green]

[bold]Market:[/bold] {market}
[bold]Competitors analyzed:[/bold] {len(discovery_data['competitors'])}
[bold]Pages scraped:[/bold] {scrape_data['success_count']}
[bold]Report:[/bold] {report_data['report_path']}

Open the report: [cyan]{report_data['latest_path']}[/cyan]""",
        title="[bold] Market Entry Radar -- Complete [/bold]",
        border_style="green",
    ))
