"""
Market Entry Radar -- Streamlit Web UI

A non-developer-friendly web interface for the Market Entry Radar pipeline.
Run with: streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from steps.step_01_discover import MARKET_ENGINES
from pipeline import run_pipeline

# Page config
st.set_page_config(
    page_title="Market Entry Radar",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------
# Available markets -- cross-reference engines with profile files
# ---------------------------------------------------------------

def _get_available_markets() -> list[dict]:
    """Build market list with profile availability info."""
    profiles_dir = PROJECT_ROOT / "market_profiles"
    available_profiles = set()
    if profiles_dir.exists():
        for f in profiles_dir.glob("*.yaml"):
            available_profiles.add(f.stem.lower())

    markets = []
    for market_key in MARKET_ENGINES:
        engines = [e["engine"] for e in MARKET_ENGINES[market_key]]
        has_profile = market_key in available_profiles
        label = market_key.replace("_", " ").title()
        suffix = "full profile" if has_profile else "SERP only"
        display = f"{label} ({suffix})"
        markets.append({
            "key": market_key,
            "label": label,
            "display": display,
            "engines": engines,
            "has_profile": has_profile,
        })

    # Sort: markets with full profiles first
    markets.sort(key=lambda m: (not m["has_profile"], m["label"]))
    return markets


AVAILABLE_MARKETS = _get_available_markets()

# ---------------------------------------------------------------
# Sidebar -- API Keys
# ---------------------------------------------------------------

with st.sidebar:
    st.title("API Configuration")
    st.caption("Keys are stored in memory only -- never saved to disk.")

    bright_data_key = st.text_input(
        "Bright Data API Key",
        type="password",
        help="Get yours at https://brightdata.com/cp/setting/api_token",
    )
    serp_zone = st.text_input(
        "SERP Zone Name",
        value="serp_api1",
        help="Your Bright Data SERP API zone name",
    )
    unlocker_zone = st.text_input(
        "Web Unlocker Zone Name",
        value="web_unlocker1",
        help="Your Bright Data Web Unlocker zone name",
    )
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Get yours at https://console.anthropic.com",
    )

    st.divider()

    # Key status
    keys_ready = all([bright_data_key, serp_zone, unlocker_zone, anthropic_key])
    if keys_ready:
        st.success("All API keys configured")
    else:
        missing = []
        if not bright_data_key:
            missing.append("Bright Data API Key")
        if not serp_zone:
            missing.append("SERP Zone")
        if not unlocker_zone:
            missing.append("Unlocker Zone")
        if not anthropic_key:
            missing.append("Anthropic API Key")
        st.warning(f"Missing: {', '.join(missing)}")

# ---------------------------------------------------------------
# Main Area
# ---------------------------------------------------------------

st.title("Market Entry Radar")
st.markdown("**Regional GTM Intelligence Pipeline** -- Powered by Bright Data + Claude")
st.markdown("Pick your target market. Drop in your product category. Get a complete Market Entry Brief.")

st.divider()

# Product info
col1, col2 = st.columns(2)

with col1:
    product_description = st.text_input(
        "Product Description",
        placeholder="e.g., Project management SaaS for B2B teams",
        help="One sentence describing what your product does",
    )
    homepage_url = st.text_input(
        "Homepage URL",
        placeholder="https://your-product.com",
        help="Your product's homepage (scraped for positioning comparison)",
    )

with col2:
    product_category = st.text_input(
        "Product Category",
        placeholder="e.g., project management software",
        help="Used to generate search queries for competitor discovery",
    )
    pricing_url = st.text_input(
        "Pricing Page URL (optional)",
        placeholder="https://your-product.com/pricing",
        help="Your pricing page for benchmark comparison",
    )

# Market selection
st.subheader("Target Market")

market_options = [m["display"] for m in AVAILABLE_MARKETS]
market_keys = [m["key"] for m in AVAILABLE_MARKETS]

selected_idx = st.selectbox(
    "Choose your target market",
    range(len(market_options)),
    format_func=lambda i: market_options[i],
    help="Markets with 'full profile' include buyer behavior, regulations, cultural norms, and channel strategy data",
)

selected_market = AVAILABLE_MARKETS[selected_idx]

# Show market details
market_info_col1, market_info_col2 = st.columns(2)
with market_info_col1:
    st.markdown(f"**Search engines:** {', '.join(selected_market['engines'])}")
with market_info_col2:
    if selected_market["has_profile"]:
        st.markdown("**Intelligence profile:** Full (buyer behavior, regulations, cultural norms)")
    else:
        st.markdown("**Intelligence profile:** SERP discovery only (no enrichment data)")

# Optional inputs
with st.expander("Known Competitors & Custom Queries (optional)"):
    known_competitors_text = st.text_area(
        "Known Competitors (one URL per line)",
        placeholder="https://competitor1.com\nhttps://competitor2.com",
        help="Add competitors you already know about -- they'll be included even if not found in search",
        height=100,
    )
    custom_queries_text = st.text_area(
        "Custom Search Queries (one per line)",
        placeholder="best project management tool for enterprises\nproject management software comparison",
        help="Additional search queries beyond the auto-generated ones",
        height=100,
    )

# Advanced settings
with st.expander("Advanced Settings"):
    adv_col1, adv_col2 = st.columns(2)
    with adv_col1:
        max_competitors = st.slider("Max Competitors", 5, 30, 15, help="More = better coverage, higher API cost")
        max_queries = st.slider("Max Queries", 10, 80, 40, help="More = better discovery, higher API cost")
    with adv_col2:
        request_delay = st.slider("Request Delay (seconds)", 0.5, 3.0, 1.0, 0.5, help="Delay between API calls")
        claude_model = st.selectbox(
            "Claude Model",
            ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
            help="Sonnet is recommended for best quality",
        )

st.divider()

# ---------------------------------------------------------------
# Run Button
# ---------------------------------------------------------------

can_run = all([product_description, product_category, homepage_url, keys_ready])

if st.button(
    "Run Market Entry Analysis",
    type="primary",
    disabled=not can_run,
    use_container_width=True,
):
    # Build config dict (same shape as config.yaml)
    known_competitors = [
        url.strip() for url in known_competitors_text.strip().split("\n")
        if url.strip()
    ] if known_competitors_text.strip() else []

    custom_queries = [
        q.strip() for q in custom_queries_text.strip().split("\n")
        if q.strip()
    ] if custom_queries_text.strip() else []

    config = {
        "product": {
            "description": product_description,
            "category": product_category,
            "homepage_url": homepage_url,
            "pricing_url": pricing_url or "",
        },
        "target_market": selected_market["key"],
        "known_competitors": known_competitors,
        "custom_queries": custom_queries,
        "output": {
            "directory": "output",
            "format": "markdown",
        },
        "advanced": {
            "max_competitors": max_competitors,
            "max_queries": max_queries,
            "request_delay": request_delay,
            "claude_model": claude_model,
        },
    }

    env = {
        "BRIGHT_DATA_API_KEY": bright_data_key,
        "BRIGHT_DATA_SERP_ZONE": serp_zone,
        "BRIGHT_DATA_UNLOCKER_ZONE": unlocker_zone,
        "ANTHROPIC_API_KEY": anthropic_key,
    }

    # Run pipeline with progress display
    step_names = {
        1: "DISCOVER -- Finding local competitors via geo-targeted SERP",
        2: "SCRAPE -- Deep-reading competitor websites",
        3: "ANALYZE -- Running Claude AI competitive analysis",
        4: "ENRICH -- Layering market-specific intelligence",
        5: "DELIVER -- Generating Market Entry Brief",
    }

    with st.status("Running Market Entry Radar pipeline...", expanded=True) as status:
        progress_bar = st.progress(0)
        step_log = st.empty()

        def on_progress(step: int, message: str):
            progress_bar.progress(step / 5)
            step_log.markdown(f"**Step {step}/5:** {message}")

        try:
            results = run_pipeline(config, env, progress_callback=on_progress)
            progress_bar.progress(1.0)
            status.update(label="Pipeline complete!", state="complete", expanded=False)
        except RuntimeError as e:
            status.update(label=f"Pipeline failed: {e}", state="error")
            st.error(str(e))
            st.stop()
        except Exception as e:
            status.update(label="Pipeline failed", state="error")
            st.error(f"An error occurred: {e}")
            st.stop()

    # Display results
    st.success(
        f"Analysis complete! "
        f"Discovered {len(results['discovery_data']['competitors'])} competitors, "
        f"scraped {results['scrape_data']['success_count']} pages."
    )

    # Read and display the report
    report_path = results["report_data"]["report_path"]
    try:
        report_content = Path(report_path).read_text(encoding="utf-8")

        st.divider()
        st.subheader("Market Entry Brief")

        # Download button
        st.download_button(
            label="Download Report (Markdown)",
            data=report_content,
            file_name=Path(report_path).name,
            mime="text/markdown",
            use_container_width=True,
        )

        # Render the report
        st.markdown(report_content)
    except FileNotFoundError:
        st.warning(f"Report file not found at {report_path}")

elif not can_run:
    missing_fields = []
    if not product_description:
        missing_fields.append("Product Description")
    if not product_category:
        missing_fields.append("Product Category")
    if not homepage_url:
        missing_fields.append("Homepage URL")
    if not keys_ready:
        missing_fields.append("API Keys (see sidebar)")
    st.info(f"Fill in required fields to run: {', '.join(missing_fields)}")

# ---------------------------------------------------------------
# Footer
# ---------------------------------------------------------------

st.divider()
st.caption(
    "Built by [Dvir Sharon](https://linkedin.com/in/dvir-sharon) | "
    "Powered by [Bright Data](https://brightdata.com) + "
    "[Anthropic Claude](https://anthropic.com) | "
    "Built with [Claude Code](https://claude.ai/claude-code)"
)
