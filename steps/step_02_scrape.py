"""
Step 2: SCRAPE -- Deep-read every local competitor.

Uses Bright Data Web Unlocker to scrape competitor homepages, pricing pages,
features pages, and about pages. Returns clean Markdown for AI analysis.

Output: A /raw_data/ directory with one Markdown file per competitor per page type.
"""

import json
import os
import re
import time
from datetime import datetime

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from steps.bright_data_client import scrape_as_markdown

console = Console()

# Pages to scrape per competitor
PAGE_TYPES = [
    {"name": "homepage", "path": "/", "required": True},
    {"name": "pricing", "paths": ["/pricing", "/plans", "/price", "/packages"], "required": False},
    {"name": "features", "paths": ["/features", "/product", "/solutions", "/platform"], "required": False},
    {"name": "about", "paths": ["/about", "/about-us", "/company", "/team"], "required": False},
]


def _scrape_url(api_key: str, zone: str, url: str, country: str = None) -> dict:
    """
    Scrape a single URL using Bright Data Web Unlocker.
    Returns Markdown content.

    Note: This is a backward-compatible wrapper. New code should use
    bright_data_client.scrape_as_markdown() directly.
    """
    env = {
        "BRIGHT_DATA_API_KEY": api_key,
        "BRIGHT_DATA_UNLOCKER_ZONE": zone,
        "BD_USE_SDK": "false",  # Legacy mode when called with explicit zone
    }
    return scrape_as_markdown(env, url, country)


def _try_page_variants(env: dict, base_url: str, paths: list, country: str, delay: float) -> dict | None:
    """Try multiple URL paths for a page type, return first success."""
    for path in paths:
        url = base_url.rstrip("/") + path
        result = scrape_as_markdown(env, url, country)
        if result["success"]:
            return result
        time.sleep(delay * 0.5)  # Shorter delay between retries
    return None


def _clean_markdown(content: str) -> str:
    """Clean up scraped Markdown for better AI analysis."""
    # Remove excessive newlines
    content = re.sub(r"\n{4,}", "\n\n\n", content)
    # Remove very long base64 images
    content = re.sub(r"!\[.*?\]\(data:image.*?\)", "[image]", content)
    # Remove tracking pixels / tiny images
    content = re.sub(r"!\[\]\(https?://[^\)]*(?:pixel|track|beacon|analytics)[^\)]*\)", "", content)
    # Truncate if extremely long (keep first 15k chars -- enough for analysis)
    if len(content) > 15000:
        content = content[:15000] + "\n\n[... content truncated for analysis ...]"
    return content.strip()


def _get_country_code(market: str) -> str:
    """Map market name to Bright Data country code."""
    return {
        "japan": "jp",
        "korea": "kr",
        "china": "cn",
        "russia": "ru",
        "australia": "au",
        "singapore": "sg",
        "germany": "de",
        "uk": "gb",
        "france": "fr",
        "brazil": "br",
    }.get(market, "us")


def run(config: dict, env: dict, discovery_data: dict) -> dict:
    """
    Run Step 2: Scrape competitors.

    Args:
        config: Parsed config.yaml
        env: Environment variables
        discovery_data: Output from Step 1

    Returns:
        dict with scraped content per competitor
    """
    market = config["target_market"].lower()
    country = _get_country_code(market)
    delay = config["advanced"]["request_delay"]

    competitors = discovery_data["competitors"]

    console.print("\n[bold cyan]STEP 2: SCRAPE[/bold cyan] -- Deep-reading every local competitor\n")
    console.print(f"  Competitors to scrape: [bold]{len(competitors)}[/bold]")
    console.print(f"  Pages per competitor: [bold]{len(PAGE_TYPES)}[/bold]")
    console.print(f"  Country targeting: [bold]{country.upper()}[/bold]")

    # Also scrape the user's own site for comparison
    own_url = config["product"]["homepage_url"]
    own_pricing = config["product"].get("pricing_url", "")

    raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raw_data")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scrape_dir = os.path.join(raw_dir, f"scrapes_{market}_{timestamp}")
    os.makedirs(scrape_dir, exist_ok=True)

    scraped_data = {}
    total_pages = (len(competitors) + 1) * len(PAGE_TYPES)  # +1 for own site
    success_count = 0
    fail_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping competitor pages...", total=total_pages)

        # Scrape own site first
        own_data = {"domain": "own_site", "pages": {}}

        for page_type in PAGE_TYPES:
            page_name = page_type["name"]
            progress.update(task, description=f"Scraping own site: {page_name}...")

            if page_name == "homepage":
                result = scrape_as_markdown(env, own_url, country)
            elif page_name == "pricing" and own_pricing:
                result = scrape_as_markdown(env, own_pricing, country)
            elif "paths" in page_type:
                result = _try_page_variants(env, own_url, page_type["paths"], country, delay)
            else:
                result = None

            if result and result.get("success"):
                result["content"] = _clean_markdown(result["content"])
                own_data["pages"][page_name] = result

                # Save to file
                filename = f"own_site_{page_name}.md"
                with open(os.path.join(scrape_dir, filename), "w", encoding="utf-8") as f:
                    f.write(f"# OWN SITE -- {page_name.upper()}\n")
                    f.write(f"URL: {result['url']}\n\n")
                    f.write(result["content"])
                success_count += 1
            else:
                fail_count += 1

            progress.advance(task)
            time.sleep(delay)

        scraped_data["own_site"] = own_data

        # Scrape each competitor
        for comp in competitors:
            domain = comp["domain"]
            base_url = comp["url"]

            # Ensure base_url has scheme
            if not base_url.startswith("http"):
                base_url = f"https://{domain}"

            comp_data = {"domain": domain, "pages": {}}
            progress.update(task, description=f"Scraping {domain}...")

            for page_type in PAGE_TYPES:
                page_name = page_type["name"]

                if page_name == "homepage":
                    result = scrape_as_markdown(env, base_url, country)
                elif "paths" in page_type:
                    result = _try_page_variants(env, base_url, page_type["paths"], country, delay)
                else:
                    result = scrape_as_markdown(env, base_url.rstrip("/") + "/" + page_name, country)

                if result and result.get("success"):
                    result["content"] = _clean_markdown(result["content"])
                    comp_data["pages"][page_name] = result

                    # Save to file
                    safe_domain = domain.replace(".", "_").replace("/", "_")
                    filename = f"{safe_domain}_{page_name}.md"
                    with open(os.path.join(scrape_dir, filename), "w", encoding="utf-8") as f:
                        f.write(f"# {domain} -- {page_name.upper()}\n")
                        f.write(f"URL: {result['url']}\n")
                        f.write(f"Content length: {result['content_length']} chars\n\n")
                        f.write(result["content"])
                    success_count += 1
                else:
                    fail_count += 1

                progress.advance(task)
                time.sleep(delay)

            scraped_data[domain] = comp_data

    # Summary
    console.print(f"\n  [green]Scraping complete: {success_count} pages scraped, {fail_count} failed[/green]")
    console.print(f"  [dim]Raw scrapes saved to {scrape_dir}[/dim]")

    # Save metadata
    meta_file = os.path.join(scrape_dir, "_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        meta = {
            "market": market,
            "timestamp": timestamp,
            "success_count": success_count,
            "fail_count": fail_count,
            "competitors_scraped": len(competitors),
        }
        # Add page availability per competitor
        for domain, data in scraped_data.items():
            meta[domain] = {
                "pages_scraped": list(data["pages"].keys()),
                "pages_missing": [
                    pt["name"] for pt in PAGE_TYPES if pt["name"] not in data["pages"]
                ],
            }
        json.dump(meta, f, indent=2)

    return {
        "scraped_data": scraped_data,
        "scrape_dir": scrape_dir,
        "success_count": success_count,
        "fail_count": fail_count,
    }
