"""
Market Entry Radar -- Core Pipeline Logic

Reusable pipeline that can be called from both CLI (run.py) and Web UI (app.py).
Supports single market or multi-market runs with cross-market comparison.
Auto-detects product info from homepage URL if not provided.
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
    step_00_detect,
    step_01_discover,
    step_02_scrape,
    step_03_analyze,
    step_04_enrich,
    step_05_deliver,
)

console = Console()


def _wrap_step_error(step_num: int, step_name: str, error: Exception) -> RuntimeError:
    """Wrap an unexpected exception with step context for debugging."""
    return RuntimeError(
        "\n"
        "============================================================\n"
        f"  PIPELINE ERROR -- Step {step_num} ({step_name}) failed\n"
        "============================================================\n"
        "\n"
        f"  Error type: {type(error).__name__}\n"
        f"  Error: {error}\n"
        "\n"
        "  This is likely a bug or a configuration issue.\n"
        "  Copy this entire block and paste it to an AI assistant for help.\n"
        "============================================================\n"
    )


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

    # STEP 0: AUTO-DETECT (if description or category missing)
    product = config.get("product", {})
    if not product.get("description") or not product.get("category"):
        homepage = product.get("homepage_url", "")
        if not homepage:
            raise RuntimeError(
                "Homepage URL is required. Provide a URL so the tool can "
                "auto-detect your product, or fill in description and category manually."
            )

        _notify(0, f"[{market}] Auto-detecting product from homepage...")
        try:
            detected = step_00_detect.run(homepage, env)
        except RuntimeError:
            raise
        except Exception as e:
            raise _wrap_step_error(0, "DETECT", e) from e

        if not product.get("description"):
            config["product"]["description"] = detected["description"]
        if not product.get("category"):
            config["product"]["category"] = detected["category"]
        _notify(0, f"[{market}] Detected: {detected.get('description', 'unknown')}")

    # STEP 1: DISCOVER
    _notify(1, f"[{market}] Discovering local competitors via geo-targeted SERP queries...")
    try:
        discovery_data = step_01_discover.run(config, env)
    except RuntimeError:
        raise
    except Exception as e:
        raise _wrap_step_error(1, "DISCOVER", e) from e

    if not discovery_data["competitors"]:
        raise RuntimeError(
            f"[{market}] No competitors discovered. "
            f"All {discovery_data.get('queries_run', 0)} SERP queries returned zero results. "
            f"Verify your product category '{config['product']['category']}' generates relevant queries, "
            f"and check the SERP API zone configuration."
        )

    _notify(1, f"[{market}] Discovered {len(discovery_data['competitors'])} competitors")

    # STEP 2: SCRAPE
    _notify(2, f"[{market}] Scraping competitor websites via Web Unlocker...")
    try:
        scrape_data = step_02_scrape.run(config, env, discovery_data)
    except RuntimeError:
        raise
    except Exception as e:
        raise _wrap_step_error(2, "SCRAPE", e) from e

    if scrape_data["success_count"] == 0:
        raise RuntimeError(
            f"[{market}] No pages scraped successfully. "
            f"Check your Bright Data Web Unlocker zone configuration."
        )

    _notify(2, f"[{market}] Scraped {scrape_data['success_count']} pages")

    # STEP 3: ANALYZE
    _notify(3, f"[{market}] Running Claude AI analysis (positioning, pricing, content gaps)...")
    try:
        analysis_data = step_03_analyze.run(config, env, discovery_data, scrape_data)
    except RuntimeError:
        raise
    except Exception as e:
        raise _wrap_step_error(3, "ANALYZE", e) from e
    _notify(3, f"[{market}] Analysis complete")

    # STEP 4: ENRICH
    _notify(4, f"[{market}] Enriching with market-specific intelligence...")
    try:
        enrichment_data = step_04_enrich.run(config, env, analysis_data, scrape_data)
    except RuntimeError:
        raise
    except Exception as e:
        raise _wrap_step_error(4, "ENRICH", e) from e
    _notify(4, f"[{market}] Enrichment complete")

    # STEP 5: DELIVER
    _notify(5, f"[{market}] Generating Market Entry Brief...")
    try:
        report_data = step_05_deliver.run(config, env, discovery_data, scrape_data, analysis_data, enrichment_data)
    except RuntimeError:
        raise
    except Exception as e:
        raise _wrap_step_error(5, "DELIVER", e) from e
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
                overall_step = step
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
    description = config.get("product", {}).get("description", "(auto-detect from URL)")
    category = config.get("product", {}).get("category", "(auto-detect from URL)")

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column(style="bold")
    info_table.add_column()
    info_table.add_row("Product", description or "(auto-detect from URL)")
    info_table.add_row("Category", category or "(auto-detect from URL)")
    info_table.add_row("Target Markets", ", ".join(m.upper() for m in markets))
    info_table.add_row("Homepage", config.get("product", {}).get("homepage_url", "N/A"))
    info_table.add_row("Max Competitors", str(config.get("advanced", {}).get("max_competitors", 15)))
    info_table.add_row("Max Queries", str(config.get("advanced", {}).get("max_queries", 40)))

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
