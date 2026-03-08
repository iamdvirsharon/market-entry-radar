"""
Step 0: DETECT -- Auto-detect product info from homepage URL.

Scrapes the homepage and sends the content to an LLM to extract
product name, description, and category.

This step only runs if the user did not provide a description or category.
It keeps the UI simple: paste your homepage URL, and the tool figures out
what your product is and what category to search for.

Output: dict with detected product info (product_name, description, category).
"""

import json
import re

from rich.console import Console

from steps.bright_data_client import scrape_as_markdown, format_scrape_error
from steps.step_02_scrape import _clean_markdown
from steps.llm_client import call_llm, get_fast_model

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
    Scrape homepage and detect product info using LLM.

    Args:
        homepage_url: The product's homepage URL
        env: Environment variables dict with API keys

    Returns:
        dict with keys: product_name, description, category
    """
    console.print("\n[bold cyan]STEP 0: DETECT[/bold cyan] -- Auto-detecting product from homepage\n")
    console.print(f"  Scraping: [bold]{homepage_url}[/bold]")

    # Scrape the homepage
    result = scrape_as_markdown(env, homepage_url)

    if not result.get("success"):
        error_detail = result.get("error", "Unknown error")
        raise RuntimeError(format_scrape_error(homepage_url, error_detail))

    content = _clean_markdown(result["content"])
    console.print(f"  Scraped: [bold]{len(content):,} chars[/bold]")

    # Send to LLM for detection
    console.print("  Detecting product info...")

    fast_model = get_fast_model(env)
    raw = call_llm(
        env=env,
        system_prompt=DETECT_SYSTEM_PROMPT,
        user_content=f"Homepage content:\n\n{content[:8000]}",
        max_tokens=256,
        model_override=fast_model,
        step_name="Step 0: DETECT",
    )

    # Parse JSON response
    try:
        detected = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from response if LLM added extra text
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
