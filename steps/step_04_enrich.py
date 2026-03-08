"""
Step 4: ENRICH -- Layer market-specific intelligence.

Loads pre-built market profile templates (buyer behavior, sales cycles,
regulatory notes, cultural considerations) and uses Claude to merge them
with the competitive analysis from Step 3.

This is the layer that makes the output genuinely valuable to someone
entering a new market for the first time.

Output: Localization warnings and market-specific recommendations.
"""

import os
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from steps.llm_client import call_llm

console = Console()

ENRICHMENT_SYSTEM_PROMPT = """You are a senior GTM strategy consultant specializing in international SaaS expansion. You have led market entry projects across APAC, EMEA, and LATAM.

You are given:
1. A competitive analysis of a target market (positioning, pricing, content gaps)
2. A market intelligence profile with hard data about the target country (buyer behavior, sales cycles, regulations, cultural norms)
3. The user's product information

Your job is to produce FOUR sections:

## LOCALIZATION WARNINGS
Specific conflicts between the user's current approach and local market norms. Be very concrete.
Format each warning as:
- **[Area]**: What the user is likely doing now (based on their site) vs. what this market requires. Include specific data points from the market profile.

Example:
- **Pricing Model**: Your site shows monthly per-seat pricing. In Japan, 65% of enterprise buyers prefer annual contracts. 3 of your top 5 local competitors offer annual-only pricing. Recommendation: Add annual pricing with 15-20% discount as the default display.

## MARKET ENTRY RECOMMENDATIONS
A prioritized 90-day action plan. Every action must be specific enough that someone could execute it without asking follow-up questions.

Format as three phases:
### Phase 1: Weeks 1-4 (Foundation)
- 5-7 specific actions, each with rationale from the data
- USE ACTUAL NAMES from the market profile: specific companies to partner with, specific platforms to list on, specific certifications to pursue, specific job titles to hire
- NOT "find a local partner" but "approach [Company X] or [Company Y] from the market profile's channel strategy section"
- NOT "ensure regulatory compliance" but "register for [specific certification], file [specific paperwork], implement [specific requirement]"
- NOT "build a local team" but "hire a [specific language]-speaking [specific role] with [specific experience]"

### Phase 2: Weeks 5-8 (Launch)
- 5-7 specific actions (same level of specificity)

### Phase 3: Weeks 9-12 (Optimize)
- 5-7 specific actions (same level of specificity)

## LAUNCH READINESS CHECKLIST
A binary yes/no checklist of everything that must be true BEFORE entering this market. Pull items from the localization warnings and market intelligence profile.

Format as:
- [ ] **[Item]**: [Why it's required]. Estimated effort: [time]. Priority: [Critical/High/Medium].

Include at minimum:
- Website localization requirements (language, currency display, payment methods)
- Legal/regulatory requirements (data residency, entity registration, certifications)
- Team requirements (local hires, language support, timezone coverage)
- Technology requirements (local payment integration, CDN/hosting, compliance)
- Partnership requirements (channel partners, resellers, marketplace listings)
- Content requirements (localized content, local case studies, translated documentation)

## SALES PLAYBOOK NOTES
Based on the market intelligence profile, provide tactical guidance for the sales team:
- How to structure the first meeting (what the local buyer expects)
- Decision-making process (who's involved, how long it takes, what kills deals)
- Pricing negotiation norms (do they negotiate? how much? what leverage do they have?)
- What competitors will say about you (and how to counter it)
- Trust-building tactics specific to this market (not generic "build relationships")

Rules:
- Every recommendation must cite specific data from the competitive analysis or market profile
- Do not give generic advice like "localize your website." Be specific: WHAT to localize, HOW, and WHY based on competitive evidence
- If a competitor is doing something well that the user should copy, name the competitor
- If a market norm conflicts with standard US SaaS practices, flag it explicitly with the specific data point
- Use actual company names, platform names, certification names from the market profile. No placeholders.
- Use "--" instead of em dashes. Never use the em dash character.
"""


def _load_market_profile(market: str) -> dict:
    """Load the market profile YAML for the target market."""
    profiles_dir = Path(__file__).parent.parent / "market_profiles"
    profile_file = profiles_dir / f"{market}.yaml"

    if not profile_file.exists():
        console.print(f"  [yellow]Warning: No market profile found for '{market}'. Using generic template.[/yellow]")
        # Return a minimal generic profile
        return {
            "market": market,
            "overview": f"No pre-built profile for {market}. Analysis will rely on scraped competitive data.",
            "buyer_behavior": {},
            "regulatory": {},
            "cultural": {},
        }

    with open(profile_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _format_market_profile(profile: dict) -> str:
    """Format market profile YAML into readable text for Claude."""
    parts = []

    parts.append(f"# MARKET INTELLIGENCE PROFILE: {profile.get('market', 'Unknown').upper()}\n")

    if "overview" in profile:
        parts.append(f"## Overview\n{profile['overview']}\n")

    if "search_landscape" in profile:
        parts.append("## Search & Discovery Landscape")
        sl = profile["search_landscape"]
        for key, value in sl.items():
            if isinstance(value, list):
                parts.append(f"- **{key}**: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "buyer_behavior" in profile:
        parts.append("## Buyer Behavior")
        bb = profile["buyer_behavior"]
        for key, value in bb.items():
            if isinstance(value, dict):
                parts.append(f"### {key}")
                for k, v in value.items():
                    parts.append(f"- **{k}**: {v}")
            elif isinstance(value, list):
                parts.append(f"- **{key}**:")
                for item in value:
                    parts.append(f"  - {item}")
            else:
                parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "pricing_norms" in profile:
        parts.append("## Pricing Norms")
        pn = profile["pricing_norms"]
        for key, value in pn.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "sales_process" in profile:
        parts.append("## Sales Process")
        sp = profile["sales_process"]
        for key, value in sp.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "content_preferences" in profile:
        parts.append("## Content & Marketing Preferences")
        cp = profile["content_preferences"]
        for key, value in cp.items():
            if isinstance(value, list):
                parts.append(f"- **{key}**: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "regulatory" in profile:
        parts.append("## Regulatory & Compliance")
        reg = profile["regulatory"]
        for key, value in reg.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "cultural" in profile:
        parts.append("## Cultural Considerations")
        cul = profile["cultural"]
        for key, value in cul.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "channel_strategy" in profile:
        parts.append("## Channel & Partnership Landscape")
        cs = profile["channel_strategy"]
        for key, value in cs.items():
            if isinstance(value, list):
                parts.append(f"- **{key}**: {', '.join(str(v) for v in value)}")
            else:
                parts.append(f"- **{key}**: {value}")
        parts.append("")

    if "success_patterns" in profile:
        parts.append("## Success Patterns (What Worked for Others)")
        for pattern in profile["success_patterns"]:
            parts.append(f"- {pattern}")
        parts.append("")

    if "failure_patterns" in profile:
        parts.append("## Failure Patterns (What to Avoid)")
        for pattern in profile["failure_patterns"]:
            parts.append(f"- {pattern}")
        parts.append("")

    return "\n".join(parts)


def run(config: dict, env: dict, analysis_data: dict, scrape_data: dict) -> dict:
    """
    Run Step 4: Market Profile Enrichment.

    Args:
        config: Parsed config.yaml
        env: Environment variables
        analysis_data: Output from Step 3
        scrape_data: Output from Step 2

    Returns:
        dict with enrichment output (localization warnings + recommendations)
    """
    market = config["target_market"].lower()
    category = config["product"]["category"]
    product_desc = config["product"]["description"]

    console.print("\n[bold cyan]STEP 4: ENRICH[/bold cyan] -- Layering market-specific intelligence\n")

    # Load market profile
    profile = _load_market_profile(market)
    profile_text = _format_market_profile(profile)
    console.print(f"  Market profile loaded: [bold]{market.upper()}[/bold] ({len(profile_text):,} chars)")

    # Combine all analysis outputs
    analyses = analysis_data["analyses"]
    combined_analysis = ""
    for name, content in analyses.items():
        combined_analysis += f"\n## {name.upper()} ANALYSIS\n{content}\n"

    # Build the enrichment prompt
    user_content = f"""PRODUCT: {product_desc}
CATEGORY: {category}
TARGET MARKET: {market.upper()}

--- COMPETITIVE ANALYSIS (from scraped data) ---
{combined_analysis}

--- MARKET INTELLIGENCE PROFILE ---
{profile_text}

Based on the competitive analysis and market intelligence profile above, produce the Localization Warnings and Market Entry Recommendations as described in your instructions."""

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating market-specific insights...", total=1)
        enrichment = call_llm(
            env=env,
            system_prompt=ENRICHMENT_SYSTEM_PROMPT,
            user_content=user_content,
            step_name="Step 4: ENRICH",
        )
        progress.update(task, completed=1)

    console.print("  [green]Market enrichment complete[/green]")

    # Save enrichment output
    raw_dir = Path(__file__).parent.parent / "raw_data"
    enrichment_file = raw_dir / f"analysis_{market}" / "enrichment.md"
    enrichment_file.write_text(enrichment, encoding="utf-8")

    console.print(f"  [dim]Enrichment saved to {enrichment_file}[/dim]")

    return {
        "enrichment": enrichment,
        "market_profile": profile,
        "market_profile_text": profile_text,
    }


