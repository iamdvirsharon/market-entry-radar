"""
Market Entry Radar -- Core Pipeline Logic

Reusable pipeline that can be called from both CLI (run.py) and Web UI (app.py).
Supports single market or multi-market runs with cross-market comparison.
"""

import copy
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
    Run the full Market Entry Radar pipeline for a single market.

    Args:
        config: Configuration dict. Must have config["target_market"] set.
        env: Environment variables dict with API keys.
        progress_callback: Optional callback(step_number, message) for UI updates.

    Returns:
        dict with all pipeline results and report path.
    """
    market = config["target_market"].upper()

    def _notify(step: int, message: str):
        if progress_callback:
            progress_callback(step, message)

    # STEP 1: DISCOVER
    _notify(1, f"[{market}] Discovering local competitors via geo-targeted SERP queries...")
    discovery_data = step_01_discover.run(config, env)

    if not discovery_data["competitors"]:
        raise RuntimeError(f"[{market}] No competitors discovered. Check your config and API keys.")

    _notify(1, f"[{market}] Discovered {len(discovery_data['competitors'])} competitors")

    # STEP 2: SCRAPE
    _notify(2, f"[{market}] Scraping competitor websites via Web Unlocker...")
    scrape_data = step_02_scrape.run(config, env, discovery_data)

    if scrape_data["success_count"] == 0:
        raise RuntimeError(f"[{market}] No pages scraped successfully. Check your Bright Data zone config.")

    _notify(2, f"[{market}] Scraped {scrape_data['success_count']} pages")

    # STEP 3: ANALYZE
    _notify(3, f"[{market}] Running Claude AI analysis (positioning, pricing, content gaps)...")
    analysis_data = step_03_analyze.run(config, env, discovery_data, scrape_data)
    _notify(3, f"[{market}] Analysis complete")

    # STEP 4: ENRICH
    _notify(4, f"[{market}] Enriching with market-specific intelligence...")
    enrichment_data = step_04_enrich.run(config, env, analysis_data, scrape_data)
    _notify(4, f"[{market}] Enrichment complete")

    # STEP 5: DELIVER
    _notify(5, f"[{market}] Generating Market Entry Brief...")
    report_data = step_05_deliver.run(config, env, discovery_data, scrape_data, analysis_data, enrichment_data)
    _notify(5, f"[{market}] Report generated")

    return {
        "discovery_data": discovery_data,
        "scrape_data": scrape_data,
        "analysis_data": analysis_data,
        "enrichment_data": enrichment_data,
        "report_data": report_data,
    }


def run_multi_market_pipeline(
    config: dict,
    env: dict,
    progress_callback: Callable[[int, str], None] | None = None,
) -> dict:
    """
    Run the pipeline for one or more markets. If multiple markets are selected,
    generates individual reports per market plus a cross-market comparison.

    Args:
        config: Configuration dict. Must have config["target_markets"] as a list.
        env: Environment variables dict with API keys.
        progress_callback: Optional callback(step_number, message) for UI updates.

    Returns:
        dict with per-market results and optional comparison report.
    """
    markets = config.get("target_markets", [])

    # Backward compatibility: single market string
    if not markets and config.get("target_market"):
        markets = [config["target_market"]]

    if not markets:
        raise RuntimeError("No target markets specified.")

    all_results = {}
    total_markets = len(markets)

    def _market_callback(market_idx: int):
        """Create a progress callback scoped to a specific market."""
        def callback(step: int, message: str):
            if progress_callback:
                # Scale progress: each market gets an equal share
                overall_step = step  # Keep step number for status display
                prefix = f"[Market {market_idx + 1}/{total_markets}] "
                progress_callback(overall_step, prefix + message)
        return callback

    for idx, market in enumerate(markets):
        # Create a copy of config with this specific market set
        market_config = copy.deepcopy(config)
        market_config["target_market"] = market

        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]  MARKET {idx + 1}/{total_markets}: {market.upper()}[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")

        result = run_pipeline(market_config, env, progress_callback=_market_callback(idx))
        all_results[market] = result

    # Cross-market comparison (only if 2+ markets)
    comparison_data = None
    if len(markets) >= 2:
        if progress_callback:
            progress_callback(5, "Generating cross-market comparison...")

        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]  CROSS-MARKET COMPARISON[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")

        comparison_data = step_05_deliver.run_comparison(
            config, env, markets, all_results
        )

        if progress_callback:
            progress_callback(5, "Cross-market comparison complete")

    return {
        "markets": markets,
        "per_market": all_results,
        "comparison": comparison_data,
    }


def display_config_panel(config: dict):
    """Display the run configuration in a Rich panel (CLI only)."""
    markets = config.get("target_markets", [config.get("target_market", "unknown")])
    category = config["product"]["category"]

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="bold")
    info_table.add_column()
    info_table.add_row("Product", config["product"]["description"])
    info_table.add_row("Category", category)
    info_table.add_row("Target Markets", ", ".join(m.upper() for m in markets))
    info_table.add_row("Homepage", config["product"]["homepage_url"])
    info_table.add_row("Max Competitors", str(config["advanced"]["max_competitors"]))
    info_table.add_row("Max Queries", str(config["advanced"]["max_queries"]))

    console.print(Panel(info_table, title="[bold]Run Configuration[/bold]", border_style="cyan"))


def display_multi_completion_panel(config: dict, results: dict):
    """Display the completion panel for multi-market runs (CLI only)."""
    markets = results["markets"]

    lines = ["[bold green]Pipeline complete![/bold green]\n"]

    for market in markets:
        r = results["per_market"][market]
        lines.append(
            f"[bold]{market.upper()}[/bold]: "
            f"{len(r['discovery_data']['competitors'])} competitors, "
            f"{r['scrape_data']['success_count']} pages scraped, "
            f"report: {r['report_data']['latest_path']}"
        )

    if results.get("comparison"):
        lines.append(f"\n[bold]Cross-Market Comparison:[/bold] {results['comparison']['comparison_path']}")

    console.print("\n")
    console.print(Panel(
        "\n".join(lines),
        title="[bold] Market Entry Radar -- Complete [/bold]",
        border_style="green",
    ))
