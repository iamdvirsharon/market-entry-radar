"""
Step 5: DELIVER -- Generate the final Market Entry Brief.

Uses Claude to synthesize all previous steps into a polished, structured
Markdown report that covers competitive landscape, pricing benchmarks,
content gaps, localization warnings, and entry recommendations.

Output: A complete Market Entry Brief in the /output/ directory.
"""

import os
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from rich.console import Console

console = Console()

REPORT_SYSTEM_PROMPT = """You are a world-class GTM strategy analyst producing a Market Entry Brief. Your report will be read by a VP of Marketing or Head of Growth at a Series A-B SaaS company who is deciding whether and how to enter a new market.

You are given the complete analysis pipeline output:
1. Positioning analysis of local competitors
2. Pricing benchmark data
3. Content & SEO gap analysis
4. Market-specific intelligence (buyer behavior, regulations, cultural norms)
5. Localization warnings and entry recommendations

Your job is to synthesize ALL of this into a single, polished Market Entry Brief using the exact structure provided below. Do NOT add new analysis. Organize, clean up, and present the existing analysis clearly.

Rules:
- Use "--" instead of em dashes. Never use the em dash character (Unicode U+2014).
- Be specific. Every claim must reference data from the analysis.
- Name competitors by name. Don't say "several competitors" when you can say "Asana, Monday.com, and Backlog."
- Include numbers. Pricing in local currency AND USD. Percentages. Timeframes.
- The Executive Summary should be readable in 60 seconds and give a clear go/no-go signal.
- Tables are preferred for comparative data (positioning, pricing, content gaps).
- The report should be immediately actionable -- someone should be able to hand this to their team and start executing.

OUTPUT FORMAT (use this exact structure):

# Market Entry Brief: [Category] → [Market]

**Generated:** [date]
**Product:** [product description]
**Target Market:** [market]
**Competitors Analyzed:** [count]
**Data Sources:** Bright Data SERP API (geo-targeted), Web Unlocker, Claude AI analysis

---

## Executive Summary

[3 paragraphs max. First paragraph: is this market worth entering and why. Second paragraph: competitive density and positioning white space. Third paragraph: primary risk and primary opportunity.]

---

## 1. Competitive Landscape

### 1.1 Competitor Map

[Table with columns: Competitor | URL | Positioning | Target Buyer | SERP Frequency]

### 1.2 Positioning Matrix

[From positioning analysis. Side-by-side comparison of how each competitor positions. Identify white space.]

### 1.3 Key Competitive Insights

[3-5 bullet points with the most important competitive findings]

---

## 2. Pricing Benchmark

### 2.1 Pricing Comparison Table

[Table with columns: Competitor | Tiers | Price Range (Local) | Price Range (USD) | Free Tier | Annual Discount]

### 2.2 Pricing Strategy Recommendations

[Where to price relative to local competitors. What model to use. Data-backed.]

---

## 3. Content & SEO Opportunity Map

### 3.1 Search Landscape Summary

[Which engines matter in this market. Overall competitive density.]

### 3.2 Top Content Gaps

[Table with columns: Topic/Keyword | Current Top Ranker | Difficulty | Opportunity | Recommended Format]

### 3.3 Quick Win Content Opportunities

[3-5 specific content pieces that could rank with moderate effort]

---

## 4. Market Intelligence

### 4.1 Buyer Behavior

[How buyers in this market discover, evaluate, and purchase SaaS. Decision-making process. Sales cycle length.]

### 4.2 Channel Strategy

[Direct vs. partner vs. reseller. What works in this market. Data points.]

### 4.3 Localization Warnings

[Specific conflicts between user's current approach and local norms. From enrichment step.]

### 4.4 Regulatory Notes

[Data residency, payment methods, entity requirements. Keep brief but specific.]

---

## 5. Recommended Entry Sequence

### Phase 1: Weeks 1-4 (Foundation)
[From enrichment recommendations. Every action must name specific companies, platforms, certifications, or tools.]

### Phase 2: Weeks 5-8 (Launch)
[From enrichment recommendations. Same specificity.]

### Phase 3: Weeks 9-12 (Optimize)
[From enrichment recommendations. Same specificity.]

---

## 6. Launch Readiness Checklist

A binary checklist of what must be done before entering this market. Pull from the localization warnings, regulatory notes, and market intelligence.

Format each item as:
- [ ] **[Item]** - [Why required] - Estimated effort: [time] - Priority: [Critical/High/Medium]

Categories to cover:
- Website & Product (localization, currency, payment methods)
- Legal & Regulatory (data residency, entity, certifications)
- Team & Support (local hires, language coverage, timezone)
- Partnerships & Channels (who to sign, where to list)
- Content & Marketing (what must exist before launch)

---

## 7. Do This Week: Top 5 Immediate Actions

The 5 most important things to do THIS WEEK based on the entire analysis. These should be tactical, not strategic. Someone should be able to read this list on Monday morning and start executing.

Format each action as:
1. **[Action]**: [Exactly what to do, who to contact, what to change]. Why: [1-sentence data reference]. Time: [estimated hours/days].

Examples of the right level of specificity:
- "Email [Company X] partnership team to discuss reseller agreement" not "explore partnerships"
- "Brief your designer on a Japanese-language landing page using [Competitor Y]'s layout as reference" not "localize your website"
- "Add annual pricing toggle to your pricing page, default to annual with 20% discount" not "adjust pricing"

---

## Appendix: Data Sources & Methodology

[Brief description of how data was collected: SERP API queries, Web Unlocker scrapes, Claude analysis. Include counts.]
"""


def run(config: dict, env: dict, discovery_data: dict, scrape_data: dict, analysis_data: dict, enrichment_data: dict) -> dict:
    """
    Run Step 5: Generate the final Market Entry Brief.

    Args:
        config: Parsed config.yaml
        env: Environment variables
        discovery_data: Output from Step 1
        scrape_data: Output from Step 2
        analysis_data: Output from Step 3
        enrichment_data: Output from Step 4

    Returns:
        dict with report path and metadata
    """
    market = config["target_market"].lower()
    model = config["advanced"]["claude_model"]
    category = config["product"]["category"]
    product_desc = config["product"]["description"]

    console.print("\n[bold cyan]STEP 5: DELIVER[/bold cyan] -- Generating the Market Entry Brief\n")

    # Build the full context for Claude
    context_parts = []

    # Product info
    context_parts.append(f"""PRODUCT INFORMATION:
- Description: {product_desc}
- Category: {category}
- Homepage: {config['product']['homepage_url']}
- Target Market: {market.upper()}
- Date: {datetime.now().strftime('%Y-%m-%d')}
""")

    # Discovery summary
    context_parts.append(f"""DISCOVERY DATA:
- Search engines used: {', '.join(discovery_data.get('engines_used', []))}
- Total SERP queries: {discovery_data.get('queries_run', 0)}
- Competitors discovered: {len(discovery_data.get('competitors', []))}

Top competitors by SERP frequency:""")
    for comp in discovery_data.get("competitors", [])[:20]:
        line = f"- {comp['domain']} (frequency: {comp['serp_frequency']})"
        if comp.get("title"):
            line += f" -- \"{comp['title']}\""
        context_parts.append(line)

    # Scraping summary
    context_parts.append(f"""
SCRAPING DATA:
- Pages successfully scraped: {scrape_data.get('success_count', 0)}
- Pages failed: {scrape_data.get('fail_count', 0)}
""")

    # Analysis outputs
    analyses = analysis_data.get("analyses", {})
    context_parts.append("\n--- POSITIONING ANALYSIS ---")
    context_parts.append(analyses.get("positioning", "(not available)"))

    context_parts.append("\n--- PRICING ANALYSIS ---")
    context_parts.append(analyses.get("pricing", "(not available)"))

    context_parts.append("\n--- CONTENT & SEO GAP ANALYSIS ---")
    context_parts.append(analyses.get("content_gaps", "(not available)"))

    # Enrichment output
    context_parts.append("\n--- MARKET INTELLIGENCE & RECOMMENDATIONS ---")
    context_parts.append(enrichment_data.get("enrichment", "(not available)"))

    # Market profile
    context_parts.append("\n--- MARKET PROFILE DATA ---")
    context_parts.append(enrichment_data.get("market_profile_text", "(not available)"))

    full_context = "\n\n".join(context_parts)

    console.print(f"  Total context for report: [bold]{len(full_context):,} chars[/bold]")

    # Generate the report
    client = Anthropic(api_key=env["ANTHROPIC_API_KEY"])

    console.print("  Generating report (this may take 30-60 seconds)...")

    response = client.messages.create(
        model=model,
        max_tokens=16384,
        system=REPORT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Here is the complete analysis pipeline output. Synthesize this into the Market Entry Brief format described in your instructions.

{full_context}

Generate the full Market Entry Brief now.""",
        }],
    )

    report = response.content[0].text

    # Save the report
    output_dir = Path(__file__).parent.parent / config["output"]["directory"]
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"market_entry_brief_{market}_{timestamp}.md"
    report_path = output_dir / report_filename

    report_path.write_text(report, encoding="utf-8")

    # Also save a "latest" symlink/copy
    latest_path = output_dir / f"market_entry_brief_{market}_latest.md"
    latest_path.write_text(report, encoding="utf-8")

    console.print(f"\n  [bold green]Report generated successfully![/bold green]")
    console.print(f"  [bold]Report:[/bold] {report_path}")
    console.print(f"  [bold]Latest:[/bold] {latest_path}")
    console.print(f"  [bold]Length:[/bold] {len(report):,} chars")

    return {
        "report_path": str(report_path),
        "latest_path": str(latest_path),
        "report_length": len(report),
    }


COMPARISON_SYSTEM_PROMPT = """You are a GTM strategy analyst producing a Cross-Market Comparison for a SaaS company evaluating multiple markets for expansion.

You are given individual Market Entry Briefs for each market. Your job is to compare them side-by-side and produce a clear recommendation on WHERE TO ENTER FIRST and WHY.

Rules:
- Use "--" instead of em dashes. Never use the em dash character.
- Be specific. Reference actual data from each market's analysis.
- Name competitors. Use real numbers.
- The output should help a Head of Growth make a decision THIS WEEK.

OUTPUT FORMAT:

# Cross-Market Comparison: [Category]

**Generated:** [date]
**Product:** [product description]
**Markets Compared:** [list]

---

## Recommendation: Enter [Market X] First

[2-3 paragraphs. Clear recommendation with data-backed rationale. Why this market over the others. What makes it the best first move.]

---

## Market Attractiveness Ranking

| Rank | Market | Opportunity Score | Risk Level | Competitive Density | Estimated Time to Revenue | Key Advantage |
|---|---|---|---|---|---|---|
| 1 | [market] | [1-10] | [Low/Med/High] | [Low/Med/High] | [months] | [1 sentence] |

---

## Side-by-Side Comparison

### Competitive Landscape
[Which market has the weakest competitors? Where is positioning white space widest?]

### Pricing Opportunity
[Which market lets you charge the most? Which has the widest pricing gaps?]

### Content & SEO
[Which market is easiest to rank in? Where is content competition lowest?]

### Regulatory & Localization Effort
[Which market requires the least setup? Which has the highest compliance burden?]

### Channel & Partnership
[Which market has the most accessible channel partners?]

---

## Recommended Sequence

If entering multiple markets:
1. **Start with [Market X]** (months 1-3): [why first, what to achieve]
2. **Then [Market Y]** (months 4-6): [why second, what carries over from market 1]
3. **Then [Market Z]** (months 7+): [why last, what requires from earlier markets]

---

## Combined "Do This Week" Actions

Top 5 actions across all markets, prioritized by impact:
1. **[Action]**: [what, why, time estimate]
"""


def run_comparison(config: dict, env: dict, markets: list, all_results: dict) -> dict:
    """
    Generate a cross-market comparison report from individual market results.

    Args:
        config: Configuration dict
        env: Environment variables
        markets: List of market keys
        all_results: Dict of market -> pipeline results

    Returns:
        dict with comparison report path
    """
    model = config["advanced"]["claude_model"]
    category = config["product"]["category"]
    product_desc = config["product"]["description"]

    console.print("\n[bold cyan]CROSS-MARKET COMPARISON[/bold cyan] -- Ranking markets for entry\n")

    # Build context from all market reports
    context_parts = [
        f"PRODUCT: {product_desc}",
        f"CATEGORY: {category}",
        f"MARKETS COMPARED: {', '.join(m.upper() for m in markets)}",
        f"DATE: {datetime.now().strftime('%Y-%m-%d')}",
    ]

    for market in markets:
        result = all_results[market]
        report_path = result["report_data"]["latest_path"]

        try:
            report_content = Path(report_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            report_content = "(Report not available)"

        context_parts.append(f"\n{'='*60}")
        context_parts.append(f"MARKET ENTRY BRIEF: {market.upper()}")
        context_parts.append(f"{'='*60}")

        # Include key stats
        discovery = result["discovery_data"]
        scrape = result["scrape_data"]
        context_parts.append(f"Competitors found: {len(discovery['competitors'])}")
        context_parts.append(f"Pages scraped: {scrape['success_count']}")

        # Truncate report if very long to fit context
        if len(report_content) > 12000:
            report_content = report_content[:12000] + "\n\n[... report truncated for comparison ...]"

        context_parts.append(report_content)

    full_context = "\n\n".join(context_parts)

    console.print(f"  Total context for comparison: [bold]{len(full_context):,} chars[/bold]")
    console.print("  Generating comparison (this may take 30-60 seconds)...")

    client = Anthropic(api_key=env["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=COMPARISON_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Here are the individual Market Entry Briefs for each market. Compare them and produce the Cross-Market Comparison.

{full_context}

Generate the Cross-Market Comparison now.""",
        }],
    )

    comparison = response.content[0].text

    # Save comparison report
    output_dir = Path(__file__).parent.parent / config.get("output", {}).get("directory", "output")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markets_slug = "_vs_".join(markets)
    comparison_filename = f"cross_market_comparison_{markets_slug}_{timestamp}.md"
    comparison_path = output_dir / comparison_filename

    comparison_path.write_text(comparison, encoding="utf-8")

    # Latest copy
    latest_path = output_dir / f"cross_market_comparison_latest.md"
    latest_path.write_text(comparison, encoding="utf-8")

    console.print(f"\n  [bold green]Comparison report generated![/bold green]")
    console.print(f"  [bold]Report:[/bold] {comparison_path}")

    return {
        "comparison_path": str(comparison_path),
        "latest_path": str(latest_path),
        "comparison_length": len(comparison),
    }
