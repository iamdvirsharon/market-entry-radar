"""
Step 0: DETECT -- Auto-detect product info from homepage URL.

Scrapes the homepage using Bright Data Web Unlocker and sends the content
to Claude to extract product name, description, and category.

This step only runs if the user did not provide a description or category.
It keeps the UI simple: paste your homepage URL, and the tool figures out
what your product is and what category to search for.

Output: dict with detected product info (product_name, description, category).
"""

import json
import re

import anthropic
from anthropic import Anthropic
from rich.console import Console

from steps.step_02_scrape import _scrape_url, _clean_markdown
from steps.error_utils import format_claude_error

console = Console()

DETECT_SYSTEM_PROMPT = """You are a product analyst. Given the scraped content of a product's homepage, extract:

1. product_name: The name of the product or company
2. description: A one-sentence description of what the product does (e.g., "Project management SaaS for B2B teams")
3. category: The product category as a search term (e.g., "project management software", "CRM software", "marketing automation platform")

Respond in this exact JSON format only, no markdown fencing, no extra text:
{"product_name": "...", "description": "...", "category": "..."}

Rules:
- The description should be concise -- one sentence, under 15 words
- The category should be a search-friendly term that someone would Google
- If you cannot determine the product, use reasonable defaults based on whatever content is available
"""


def run(homepage_url: str, env: dict) -> dict:
    """
    Scrape homepage and detect product info using Claude.

    Args:
        homepage_url: The product's homepage URL
        env: Environment variables dict with API keys

    Returns:
        dict with keys: product_name, description, category
    """
    api_key = env["BRIGHT_DATA_API_KEY"]
    zone = env["BRIGHT_DATA_UNLOCKER_ZONE"]

    console.print("\n[bold cyan]STEP 0: DETECT[/bold cyan] -- Auto-detecting product from homepage\n")
    console.print(f"  Scraping: [bold]{homepage_url}[/bold]")

    # Scrape the homepage
    result = _scrape_url(api_key, zone, homepage_url)

    if not result.get("success"):
        error_detail = result.get("error", "Unknown error")
        raise RuntimeError(
            "\n"
            "============================================================\n"
            "  HOMEPAGE SCRAPE ERROR -- Could not read your homepage\n"
            "============================================================\n"
            "\n"
            f"  URL: {homepage_url}\n"
            f"  Error: {error_detail}\n"
            "\n"
            "  --- Fix it ---\n"
            "  1. Verify the URL is correct and accessible in a browser\n"
            "  2. Check your Bright Data Web Unlocker zone is active\n"
            "  3. Or provide product description and category manually\n"
            "\n"
            "  Copy this entire block and paste it to an AI assistant for help.\n"
            "============================================================\n"
        )

    content = _clean_markdown(result["content"])
    console.print(f"  Scraped: [bold]{len(content):,} chars[/bold]")

    # Send to Claude for detection
    console.print("  Detecting product info...")

    try:
        client = Anthropic(api_key=env["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Haiku for speed + cost -- this is a simple extraction
            max_tokens=256,
            system=DETECT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Homepage content:\n\n{content[:8000]}"}],
        )
        raw = response.content[0].text
    except (anthropic.AuthenticationError, anthropic.RateLimitError, anthropic.APIError) as e:
        raise RuntimeError(format_claude_error(e, "Step 0: DETECT", "claude-haiku-4-5-20251001")) from e

    # Parse JSON response
    try:
        detected = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from response if Claude added extra text
        match = re.search(r'\{[^}]+\}', raw)
        if match:
            try:
                detected = json.loads(match.group())
            except json.JSONDecodeError:
                detected = None
        else:
            detected = None

    if not detected:
        console.print("  [yellow]Warning: Could not parse auto-detection result. Using defaults.[/yellow]")
        detected = {
            "product_name": "Unknown Product",
            "description": "Software product",
            "category": "software",
        }

    console.print(f"  [green]Detected:[/green]")
    console.print(f"    Name:     [bold]{detected.get('product_name', 'Unknown')}[/bold]")
    console.print(f"    About:    [bold]{detected.get('description', 'Unknown')}[/bold]")
    console.print(f"    Category: [bold]{detected.get('category', 'Unknown')}[/bold]")

    return detected
