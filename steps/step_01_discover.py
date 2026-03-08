"""
Step 1: DISCOVER -- Find the real local competitive set.

Uses Bright Data SERP API to run geo-targeted searches across the RIGHT
search engines for each market. Not just Google -- Yahoo Japan, Naver for
Korea, Baidu for China, Yandex for Russia.

Output: A deduplicated list of local competitors with URLs and frequency scores.
"""

import json
import os
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()

# Search engine routing per market
MARKET_ENGINES = {
    "japan": [
        {"engine": "google", "domain": "google.co.jp", "gl": "jp", "hl": "ja"},
        {"engine": "yahoo_japan", "domain": "search.yahoo.co.jp", "gl": "jp", "hl": "ja"},
    ],
    "korea": [
        {"engine": "naver", "domain": "search.naver.com", "gl": "kr", "hl": "ko"},
        {"engine": "google", "domain": "google.co.kr", "gl": "kr", "hl": "ko"},
    ],
    "china": [
        {"engine": "baidu", "domain": "www.baidu.com", "gl": "cn", "hl": "zh"},
    ],
    "russia": [
        {"engine": "yandex", "domain": "yandex.com", "gl": "ru", "hl": "ru"},
        {"engine": "google", "domain": "google.ru", "gl": "ru", "hl": "ru"},
    ],
    "australia": [
        {"engine": "google", "domain": "google.com.au", "gl": "au", "hl": "en"},
    ],
    "singapore": [
        {"engine": "google", "domain": "google.com.sg", "gl": "sg", "hl": "en"},
    ],
    "germany": [
        {"engine": "google", "domain": "google.de", "gl": "de", "hl": "de"},
    ],
    "uk": [
        {"engine": "google", "domain": "google.co.uk", "gl": "gb", "hl": "en"},
    ],
    "france": [
        {"engine": "google", "domain": "google.fr", "gl": "fr", "hl": "fr"},
    ],
    "brazil": [
        {"engine": "google", "domain": "google.com.br", "gl": "br", "hl": "pt"},
    ],
}

# Query templates -- filled with product category
QUERY_TEMPLATES = {
    "category": [
        "{category}",
        "best {category}",
        "{category} for enterprise",
        "{category} for small business",
        "{category} comparison",
        "{category} review",
    ],
    "problem": [
        "how to {category_verb}",
        "best tool for {category_verb}",
        "{category_verb} solution",
    ],
    "comparison": [
        "{category} vs",
        "{category} alternative",
        "top {category} tools",
        "{category} pricing",
    ],
    "buyer_intent": [
        "buy {category}",
        "{category} free trial",
        "{category} demo",
        "{category} pricing plans",
    ],
}

# Verb forms for problem queries
CATEGORY_VERBS = {
    "project management software": "manage projects",
    "crm software": "manage customer relationships",
    "marketing automation": "automate marketing",
    "email marketing": "send marketing emails",
    "analytics platform": "track analytics",
    "default": "solve business problems",
}


def _build_search_url(engine_config: dict, query: str) -> str:
    """Build the correct search URL for each engine."""
    encoded_query = quote_plus(query)
    engine = engine_config["engine"]
    gl = engine_config["gl"]
    hl = engine_config["hl"]

    if engine == "google":
        domain = engine_config["domain"]
        return f"https://www.{domain}/search?q={encoded_query}&gl={gl}&hl={hl}&brd_json=1"
    elif engine == "yahoo_japan":
        return f"https://search.yahoo.co.jp/search?p={encoded_query}&brd_json=1"
    elif engine == "naver":
        return f"https://search.naver.com/search.naver?query={encoded_query}&brd_json=1"
    elif engine == "baidu":
        return f"https://www.baidu.com/s?wd={encoded_query}&brd_json=1"
    elif engine == "yandex":
        return f"https://yandex.com/search/?text={encoded_query}&lr=213&brd_json=1"
    else:
        raise ValueError(f"Unknown engine: {engine}")


def _generate_queries(category: str, custom_queries: list = None) -> list[str]:
    """Generate search queries from templates + custom queries."""
    # Determine verb form
    category_verb = CATEGORY_VERBS.get(category.lower(), category.lower().replace("software", "").strip())

    queries = []
    for template_group in QUERY_TEMPLATES.values():
        for template in template_group:
            q = template.format(category=category, category_verb=category_verb)
            queries.append(q)

    # Add custom queries
    if custom_queries:
        queries.extend(custom_queries)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)

    return unique


def _call_serp_api(api_key: str, zone: str, search_url: str) -> dict | None:
    """Make a single SERP API call."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "zone": zone,
        "url": search_url,
        "format": "raw",
    }

    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                # Some engines return non-JSON -- try to parse organic results
                return {"raw_html": response.text[:5000]}
        else:
            console.print(f"  [dim]SERP API returned {response.status_code}[/dim]")
            return None
    except requests.exceptions.RequestException as e:
        console.print(f"  [dim]SERP request failed: {e}[/dim]")
        return None


def _extract_urls_from_results(results: dict) -> list[dict]:
    """Extract competitor URLs from SERP results."""
    urls = []

    # Handle parsed JSON format (brd_json=1)
    if "organic" in results:
        for item in results["organic"]:
            if "link" in item:
                urls.append({
                    "url": item["link"],
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                })

    # Handle general results format
    if "general" in results:
        for item in results["general"]:
            if "link" in item:
                urls.append({
                    "url": item["link"],
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                })

    # Handle paid results
    if "paid" in results:
        for item in results["paid"]:
            if "link" in item:
                urls.append({
                    "url": item["link"],
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "is_paid": True,
                })

    return urls


def _extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def _is_noise_domain(domain: str) -> bool:
    """Filter out non-competitor domains (search engines, social media, etc.)."""
    noise_patterns = [
        "google.", "youtube.", "facebook.", "twitter.", "linkedin.",
        "reddit.", "wikipedia.", "amazon.", "instagram.", "tiktok.",
        "pinterest.", "quora.", "medium.", "github.", "stackoverflow.",
        "apple.", "microsoft.", "bing.", "yahoo.", "naver.", "baidu.",
        "yandex.", "duckduckgo.", "wp.com", "wordpress.com",
        "blogspot.", "tumblr.", "t.co", "bit.ly", "goo.gl",
        "play.google.", "apps.apple.",
        "g2.com", "capterra.com", "trustradius.com", "getapp.com",
        "softwareadvice.com",  # Review sites -- useful but not competitors
    ]
    return any(pattern in domain for pattern in noise_patterns)


def run(config: dict, env: dict) -> dict:
    """
    Run Step 1: SERP Discovery.

    Args:
        config: Parsed config.yaml
        env: Environment variables (API keys, zones)

    Returns:
        dict with discovered competitors and raw SERP data
    """
    api_key = env["BRIGHT_DATA_API_KEY"]
    zone = env["BRIGHT_DATA_SERP_ZONE"]
    market = config["target_market"].lower()
    category = config["product"]["category"]
    homepage = config["product"]["homepage_url"]
    custom_queries = config.get("custom_queries", [])
    max_queries = config["advanced"]["max_queries"]
    max_competitors = config["advanced"]["max_competitors"]
    delay = config["advanced"]["request_delay"]

    console.print("\n[bold cyan]STEP 1: DISCOVER[/bold cyan] -- Finding the real local competitive set\n")

    # Validate market
    if market not in MARKET_ENGINES:
        console.print(f"[red]Unknown market: {market}. Supported: {', '.join(MARKET_ENGINES.keys())}[/red]")
        raise ValueError(f"Unknown market: {market}")

    engines = MARKET_ENGINES[market]
    console.print(f"  Target market: [bold]{market.upper()}[/bold]")
    console.print(f"  Search engines: [bold]{', '.join(e['engine'] for e in engines)}[/bold]")

    # Generate queries
    queries = _generate_queries(category, custom_queries)[:max_queries]
    console.print(f"  Search queries: [bold]{len(queries)}[/bold]")

    # Extract own domain for filtering
    own_domain = _extract_domain(homepage)

    # Run SERP queries across all engines
    all_results = []
    competitor_frequency = {}  # domain -> count of appearances
    competitor_info = {}  # domain -> best title/description

    total_calls = len(queries) * len(engines)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running SERP queries...", total=total_calls)

        for engine_config in engines:
            for query in queries:
                search_url = _build_search_url(engine_config, query)
                results = _call_serp_api(api_key, zone, search_url)

                if results:
                    urls = _extract_urls_from_results(results)
                    for item in urls:
                        domain = _extract_domain(item["url"])

                        # Skip own domain, noise domains
                        if domain == own_domain or _is_noise_domain(domain):
                            continue

                        # Track frequency
                        competitor_frequency[domain] = competitor_frequency.get(domain, 0) + 1

                        # Keep best info (longest description)
                        if domain not in competitor_info or len(item.get("description", "")) > len(
                            competitor_info[domain].get("description", "")
                        ):
                            competitor_info[domain] = item

                    all_results.append({
                        "engine": engine_config["engine"],
                        "query": query,
                        "url_count": len(urls),
                    })

                progress.advance(task)
                time.sleep(delay)

    # Rank competitors by frequency
    ranked = sorted(competitor_frequency.items(), key=lambda x: x[1], reverse=True)
    top_competitors = ranked[:max_competitors]

    # Build competitor list
    competitors = []
    for domain, freq in top_competitors:
        info = competitor_info.get(domain, {})
        competitors.append({
            "domain": domain,
            "url": info.get("url", f"https://{domain}"),
            "title": info.get("title", ""),
            "description": info.get("description", ""),
            "serp_frequency": freq,
            "is_paid": info.get("is_paid", False),
        })

    # Add known competitors if not already discovered
    known = config.get("known_competitors", []) or []
    known_domains = set()
    for url in known:
        domain = _extract_domain(url)
        known_domains.add(domain)
        if not any(c["domain"] == domain for c in competitors):
            competitors.append({
                "domain": domain,
                "url": url,
                "title": "",
                "description": "",
                "serp_frequency": 0,
                "is_paid": False,
                "known_competitor": True,
            })

    # Display results
    console.print(f"\n  [green]Discovered {len(competitors)} competitors[/green]\n")

    table = Table(title="Top Competitors by SERP Frequency")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Domain", style="cyan")
    table.add_column("Frequency", justify="right", style="green")
    table.add_column("Title", max_width=50)

    for i, comp in enumerate(competitors[:20], 1):
        freq_str = str(comp["serp_frequency"])
        if comp.get("known_competitor"):
            freq_str += " (known)"
        table.add_row(str(i), comp["domain"], freq_str, comp["title"][:50])

    console.print(table)

    # Save raw data
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "raw_data")
    os.makedirs(raw_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    discovery_file = os.path.join(raw_dir, f"discovery_{market}_{timestamp}.json")

    with open(discovery_file, "w", encoding="utf-8") as f:
        json.dump({
            "market": market,
            "category": category,
            "engines_used": [e["engine"] for e in engines],
            "queries_run": len(queries) * len(engines),
            "competitors": competitors,
            "serp_summary": all_results,
            "timestamp": timestamp,
        }, f, indent=2, ensure_ascii=False)

    console.print(f"\n  [dim]Raw data saved to {discovery_file}[/dim]")

    return {
        "competitors": competitors,
        "market": market,
        "engines_used": [e["engine"] for e in engines],
        "queries_run": len(queries) * len(engines),
        "discovery_file": discovery_file,
    }
