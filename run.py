#!/usr/bin/env python3
"""
Market Entry Radar -- Regional GTM Intelligence Pipeline

A 5-step workflow that produces 80% of a $200K market entry
research package in under 2 hours. Powered by Bright Data + Claude.

Usage:
    1. Copy .env.example to .env and add your API keys
    2. Edit config.yaml with your product details and target market(s)
    3. Run: python run.py

For the web UI (no CLI needed):
    python -m streamlit run app.py

Steps:
    1. DISCOVER -- Geo-targeted SERP queries across the RIGHT search engines
    2. SCRAPE   -- Deep-read every local competitor via Web Unlocker
    3. ANALYZE  -- Claude produces positioning matrix, pricing benchmark, content gaps
    4. ENRICH   -- Layer market-specific intelligence (buyer behavior, regulations, culture)
    5. DELIVER  -- Generate a complete Market Entry Brief

Author: Dvir Sharon (https://www.linkedin.com/in/dvirsharon/)
Powered by: Bright Data (https://brightdata.com) + Anthropic Claude
"""

import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.console import Console

from pipeline import (
    run_multi_market_pipeline,
    display_config_panel,
    display_multi_completion_panel,
)

console = Console()

PROJECT_ROOT = Path(__file__).parent

BANNER = """
[bold cyan]
 __  __            _        _     ___       _
|  \\/  | __ _ _ __| | _____| |_  | __| _ _ | |_ _ _ _  _
| |\\/| |/ _` | '__| |/ / _ \\ __| | _| | ' \\|  _| '_| || |
| |  | | (_| | |  |   <  __/ |_  | |__| || || | | |  \\_, |
|_|  |_|\\__,_|_|  |_|\\_\\___|\\__| |____|_||_||_| |_|  |__/

                   [bold white]R  A  D  A  R[/bold white]
[/bold cyan]
[dim]Regional GTM Intelligence Pipeline
Powered by Bright Data + Claude[/dim]
"""


def load_config() -> dict:
    """Load and validate config.yaml. Handles both old and new format."""
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        console.print("[red]Error: config.yaml not found. Copy config.yaml.example and edit it.[/red]")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Handle backward compatibility: target_market (string) -> target_markets (list)
    if "target_markets" not in config and "target_market" in config:
        config["target_markets"] = [config["target_market"]]
    elif "target_markets" in config and "target_market" not in config:
        # Set target_market to first market for any code that still reads it
        config["target_market"] = config["target_markets"][0]

    # Validate required fields
    required = [
        ("product.description", config.get("product", {}).get("description")),
        ("product.category", config.get("product", {}).get("category")),
        ("product.homepage_url", config.get("product", {}).get("homepage_url")),
        ("target_markets", config.get("target_markets")),
    ]

    missing = [name for name, val in required if not val]
    if missing:
        console.print(f"[red]Error: Missing required config fields: {', '.join(missing)}[/red]")
        sys.exit(1)

    return config


def load_env() -> dict:
    """Load and validate environment variables."""
    load_dotenv(PROJECT_ROOT / ".env")

    required_vars = [
        "BRIGHT_DATA_API_KEY",
        "BRIGHT_DATA_SERP_ZONE",
        "BRIGHT_DATA_UNLOCKER_ZONE",
        "ANTHROPIC_API_KEY",
    ]

    env = {}
    missing = []
    for var in required_vars:
        val = os.getenv(var)
        if not val or val.startswith("your_"):
            missing.append(var)
        else:
            env[var] = val

    if missing:
        console.print(f"[red]Error: Missing environment variables: {', '.join(missing)}[/red]")
        console.print("[dim]Copy .env.example to .env and fill in your API keys.[/dim]")
        sys.exit(1)

    return env


def main():
    """Run the full Market Entry Radar pipeline via CLI."""
    console.print(BANNER)

    config = load_config()
    env = load_env()

    display_config_panel(config)

    start_time = time.time()

    results = run_multi_market_pipeline(config, env)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    display_multi_completion_panel(config, results)
    console.print(f"\n  [dim]Runtime: {minutes}m {seconds}s[/dim]\n")


if __name__ == "__main__":
    main()
