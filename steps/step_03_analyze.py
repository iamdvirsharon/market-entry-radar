"""
Step 3: ANALYZE -- Turn raw scrapes into competitive intelligence.

Uses Claude API to process scraped competitor data through three analysis passes:
A) Positioning Matrix -- how each competitor positions, where white space is
B) Pricing Intelligence -- tier structures, local currency, feature gates
C) Content & SEO Gap Map -- topics competitors rank for that user doesn't cover

Output: Structured analysis dicts ready for enrichment and report generation.
"""

import json
import os
from pathlib import Path

import anthropic
from anthropic import Anthropic
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from steps.error_utils import format_claude_error

console = Console()


def _load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")


def _call_claude(client: Anthropic, model: str, system_prompt: str, user_content: str) -> str:
    """Make a Claude API call with structured prompts."""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return response.content[0].text
    except (anthropic.AuthenticationError, anthropic.RateLimitError, anthropic.APIError) as e:
        raise RuntimeError(format_claude_error(e, "Step 3: ANALYZE", model)) from e


def _prepare_competitor_summary(scraped_data: dict) -> str:
    """Build a text summary of all competitor data for Claude analysis."""
    summary_parts = []

    for domain, data in scraped_data.items():
        if domain == "own_site":
            continue

        pages = data.get("pages", {})
        if not pages:
            continue

        part = f"\n{'='*60}\n## COMPETITOR: {domain}\n{'='*60}\n"

        for page_name, page_data in pages.items():
            content = page_data.get("content", "")
            # Truncate long pages for analysis
            if len(content) > 4000:
                content = content[:4000] + "\n[... truncated ...]"
            part += f"\n### {page_name.upper()} ({page_data.get('url', '')})\n{content}\n"

        summary_parts.append(part)

    return "\n".join(summary_parts)


def _prepare_own_site_summary(scraped_data: dict) -> str:
    """Build a text summary of the user's own site data."""
    own = scraped_data.get("own_site", {})
    pages = own.get("pages", {})
    if not pages:
        return "(Own site data not available)"

    parts = ["## YOUR SITE\n"]
    for page_name, page_data in pages.items():
        content = page_data.get("content", "")
        if len(content) > 3000:
            content = content[:3000] + "\n[... truncated ...]"
        parts.append(f"### {page_name.upper()} ({page_data.get('url', '')})\n{content}\n")

    return "\n".join(parts)


def _run_positioning_analysis(
    client: Anthropic, model: str, competitor_summary: str, own_site_summary: str, market: str, category: str
) -> str:
    """Analysis A: Positioning Matrix."""
    system_prompt = _load_prompt("positioning_analysis")

    user_content = f"""MARKET: {market.upper()}
PRODUCT CATEGORY: {category}

{own_site_summary}

{competitor_summary}

Analyze all competitors above and produce the Positioning Matrix as described in your instructions."""

    return _call_claude(client, model, system_prompt, user_content)


def _run_pricing_analysis(
    client: Anthropic, model: str, competitor_summary: str, own_site_summary: str, market: str, category: str
) -> str:
    """Analysis B: Pricing Intelligence."""
    system_prompt = _load_prompt("pricing_analysis")

    user_content = f"""MARKET: {market.upper()}
PRODUCT CATEGORY: {category}

{own_site_summary}

{competitor_summary}

Analyze all competitor pricing data above and produce the Pricing Benchmark as described in your instructions."""

    return _call_claude(client, model, system_prompt, user_content)


def _run_content_gap_analysis(
    client: Anthropic, model: str, competitor_summary: str, own_site_summary: str,
    discovery_data: dict, market: str, category: str
) -> str:
    """Analysis C: Content & SEO Gap Map."""
    system_prompt = _load_prompt("content_gap_analysis")

    # Include SERP discovery data for context
    serp_context = f"""SERP DISCOVERY SUMMARY:
- Engines used: {', '.join(discovery_data.get('engines_used', []))}
- Total queries run: {discovery_data.get('queries_run', 0)}
- Competitors found: {len(discovery_data.get('competitors', []))}

Top competitors by SERP frequency:
"""
    for comp in discovery_data.get("competitors", [])[:15]:
        serp_context += f"- {comp['domain']}: appeared {comp['serp_frequency']} times"
        if comp.get("title"):
            serp_context += f" | \"{comp['title']}\""
        serp_context += "\n"

    user_content = f"""MARKET: {market.upper()}
PRODUCT CATEGORY: {category}

{serp_context}

{own_site_summary}

{competitor_summary}

Analyze the competitive content landscape and produce the Content & SEO Gap Map as described in your instructions."""

    return _call_claude(client, model, system_prompt, user_content)


def run(config: dict, env: dict, discovery_data: dict, scrape_data: dict) -> dict:
    """
    Run Step 3: AI Analysis.

    Args:
        config: Parsed config.yaml
        env: Environment variables
        discovery_data: Output from Step 1
        scrape_data: Output from Step 2

    Returns:
        dict with three analysis outputs
    """
    model = config["advanced"]["claude_model"]
    market = config["target_market"].lower()
    category = config["product"]["category"]

    console.print("\n[bold cyan]STEP 3: ANALYZE[/bold cyan] -- Turning raw data into competitive intelligence\n")

    client = Anthropic(api_key=env["ANTHROPIC_API_KEY"])

    # Prepare data summaries
    scraped = scrape_data["scraped_data"]
    competitor_summary = _prepare_competitor_summary(scraped)
    own_site_summary = _prepare_own_site_summary(scraped)

    console.print(f"  Competitor data prepared: [bold]{len(competitor_summary):,} chars[/bold]")
    console.print(f"  Own site data prepared: [bold]{len(own_site_summary):,} chars[/bold]")

    analyses = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Analysis A: Positioning Matrix
        task_a = progress.add_task("Running positioning analysis...", total=1)
        console.print("\n  [yellow]Analysis A:[/yellow] Positioning Matrix")
        analyses["positioning"] = _run_positioning_analysis(
            client, model, competitor_summary, own_site_summary, market, category
        )
        progress.update(task_a, completed=1)
        console.print("  [green]Positioning analysis complete[/green]")

        # Analysis B: Pricing Intelligence
        task_b = progress.add_task("Running pricing analysis...", total=1)
        console.print("  [yellow]Analysis B:[/yellow] Pricing Intelligence")
        analyses["pricing"] = _run_pricing_analysis(
            client, model, competitor_summary, own_site_summary, market, category
        )
        progress.update(task_b, completed=1)
        console.print("  [green]Pricing analysis complete[/green]")

        # Analysis C: Content & SEO Gap Map
        task_c = progress.add_task("Running content gap analysis...", total=1)
        console.print("  [yellow]Analysis C:[/yellow] Content & SEO Gap Map")
        analyses["content_gaps"] = _run_content_gap_analysis(
            client, model, competitor_summary, own_site_summary, discovery_data, market, category
        )
        progress.update(task_c, completed=1)
        console.print("  [green]Content gap analysis complete[/green]")

    # Save analysis outputs
    raw_dir = Path(__file__).parent.parent / "raw_data"
    analysis_dir = raw_dir / f"analysis_{market}"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    for name, content in analyses.items():
        filepath = analysis_dir / f"{name}.md"
        filepath.write_text(content, encoding="utf-8")

    console.print(f"\n  [dim]Analysis files saved to {analysis_dir}[/dim]")

    return {
        "analyses": analyses,
        "analysis_dir": str(analysis_dir),
    }
