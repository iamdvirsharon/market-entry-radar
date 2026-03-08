#!/usr/bin/env python3
"""
Market Entry Radar -- Regional GTM Intelligence Pipeline

Usage:
    1. Copy .env.example to .env and add your API keys
    2. Edit config.yaml with your homepage URL and target market(s)
    3. Run: python run.py

For the web UI (no CLI needed):
    python -m streamlit run app.py

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
    """Load and validate config.yaml."""
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
        config["target_market"] = config["target_markets"][0]

    # Ensure product dict has required keys (even if empty -- pipeline auto-detects)
    product = config.setdefault("product", {})
    product.setdefault("description", "")
    product.setdefault("category", "")
    product.setdefault("homepage_url", "")
    product.setdefault("pricing_url", "")

    # Validate: homepage URL is required (everything else can be auto-detected)
    if not product.get("homepage_url"):
        console.print("[red]Error: product.homepage_url is required in config.yaml[/red]")
        sys.exit(1)

    if not config.get("target_markets"):
        console.print("[red]Error: target_markets is required in config.yaml[/red]")
        sys.exit(1)

    return config


def load_env() -> dict:
    """Load and validate environment variables."""
    load_dotenv(PROJECT_ROOT / ".env")

    # Required keys
    required_vars = ["BRIGHT_DATA_API_KEY", "ANTHROPIC_API_KEY"]

    env = {}
    missing = []
    for var in required_vars:
        val = os.getenv(var)
        if not val or val.startswith("your_"):
            missing.append(var)
        else:
            env[var] = val

    if missing:
        console.print(f"[red]Error: Missing required API keys: {', '.join(missing)}[/red]")
        console.print("[dim]Copy .env.example to .env and add your API keys.[/dim]")
        sys.exit(1)

    # Optional zone names with defaults
    env["BRIGHT_DATA_SERP_ZONE"] = os.getenv("BRIGHT_DATA_SERP_ZONE", "serp_api1")
    env["BRIGHT_DATA_UNLOCKER_ZONE"] = os.getenv("BRIGHT_DATA_UNLOCKER_ZONE", "web_unlocker1")

    return env


def main():
    """Run the full Market Entry Radar pipeline via CLI."""
    console.print(BANNER)

    config = load_config()
    env = load_env()

    display_config_panel(config)

    start_time = time.time()

    try:
        results = run_multi_market_pipeline(config, env)
    except RuntimeError as e:
        console.print(f"\n[red]{e}[/red]")
        sys.exit(1)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    display_multi_completion_panel(config, results)
    console.print(f"\n  [dim]Runtime: {minutes}m {seconds}s[/dim]\n")


if __name__ == "__main__":
    main()
