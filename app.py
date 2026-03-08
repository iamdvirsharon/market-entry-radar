"""
Market Entry Radar -- Streamlit Web UI

Paste your homepage URL, pick a market, run.
The tool auto-detects what your product is and finds local competitors.

Run with: python -m streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from steps.step_01_discover import MARKET_ENGINES
from pipeline import run_multi_market_pipeline

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
# Sidebar -- API Keys (simplified: 2 required, zones in advanced)
# ---------------------------------------------------------------

with st.sidebar:
    st.title("API Keys")
    st.caption("Keys are stored in memory only -- never saved to disk.")

    bright_data_key = st.text_input(
        "Bright Data API Key",
        type="password",
        help="Get yours at https://brightdata.com/cp/setting/api_token",
    )
    anthropic_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Get yours at https://console.anthropic.com",
    )

    with st.expander("Zone Configuration (advanced)"):
        st.caption("Default zone names work for most setups. Only change if you've customized your Bright Data zones.")
        serp_zone = st.text_input(
            "SERP Zone Name",
            value="serp_api1",
        )
        unlocker_zone = st.text_input(
            "Web Unlocker Zone Name",
            value="web_unlocker1",
        )

    st.divider()

    # Key status -- only check the 2 main keys
    keys_ready = all([bright_data_key, anthropic_key])
    if keys_ready:
        st.success("API keys configured")
    else:
        missing = []
        if not bright_data_key:
            missing.append("Bright Data API Key")
        if not anthropic_key:
            missing.append("Anthropic API Key")
        st.warning(f"Missing: {', '.join(missing)}")

# ---------------------------------------------------------------
# Main Area
# ---------------------------------------------------------------

st.title("Market Entry Radar")
st.markdown("**Regional GTM Intelligence Pipeline** -- Powered by Bright Data + Claude")
st.markdown("Paste your homepage URL and pick a market. The tool figures out the rest.")

st.divider()

# Product info -- simplified: just the homepage URL
homepage_url = st.text_input(
    "Your Product Homepage URL",
    placeholder="https://your-product.com",
    help="We scrape your homepage and auto-detect your product description and category",
)

with st.expander("Override Auto-Detection (optional)"):
    st.caption("Leave these empty to auto-detect from your homepage. Fill in only if you want to override.")
    override_col1, override_col2 = st.columns(2)
    with override_col1:
        product_description = st.text_input(
            "Product Description",
            placeholder="Leave empty to auto-detect",
            help="One sentence describing what your product does",
        )
    with override_col2:
        product_category = st.text_input(
            "Product Category",
            placeholder="Leave empty to auto-detect",
            help="The product category used for search queries (e.g., 'project management software')",
        )
    pricing_url = st.text_input(
        "Pricing Page URL",
        placeholder="Leave empty -- tool tries /pricing automatically",
        help="Your pricing page for benchmark comparison",
    )

# Market selection -- multiselect
st.subheader("Target Market(s)")

market_display_to_key = {m["display"]: m["key"] for m in AVAILABLE_MARKETS}
market_key_to_info = {m["key"]: m for m in AVAILABLE_MARKETS}
market_options = [m["display"] for m in AVAILABLE_MARKETS]

selected_displays = st.multiselect(
    "Choose one or more target markets",
    options=market_options,
    default=[],
    help="Select multiple markets for individual reports + a cross-market comparison. Markets with 'full profile' include buyer behavior, regulations, cultural norms, and channel strategy data.",
)

selected_market_keys = [market_display_to_key[d] for d in selected_displays]

# Show details for selected markets
if selected_market_keys:
    if len(selected_market_keys) == 1:
        m = market_key_to_info[selected_market_keys[0]]
        mc1, mc2 = st.columns(2)
        with mc1:
            st.markdown(f"**Search engines:** {', '.join(m['engines'])}")
        with mc2:
            profile_label = "Full (buyer behavior, regulations, cultural norms)" if m["has_profile"] else "SERP discovery only (no enrichment data)"
            st.markdown(f"**Intelligence profile:** {profile_label}")
    else:
        st.markdown(f"**{len(selected_market_keys)} markets selected** -- individual reports per market + cross-market comparison")
        for key in selected_market_keys:
            m = market_key_to_info[key]
            profile_icon = "✅" if m["has_profile"] else "⚠️"
            st.markdown(f"- {m['label']}: {', '.join(m['engines'])} {profile_icon}")

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
# Cost Estimate
# ---------------------------------------------------------------

if selected_market_keys:
    n_markets = len(selected_market_keys)
    est_low = n_markets * 10
    est_high = n_markets * 15
    st.caption(f"Estimated cost: ${est_low}-${est_high} ({n_markets} market{'s' if n_markets > 1 else ''} x ~$10-15 each)")

# ---------------------------------------------------------------
# Run Button
# ---------------------------------------------------------------

can_run = all([homepage_url, keys_ready, selected_market_keys])

if st.button(
    f"Run Market Entry Analysis ({len(selected_market_keys)} market{'s' if len(selected_market_keys) != 1 else ''})" if selected_market_keys else "Run Market Entry Analysis",
    type="primary",
    disabled=not can_run,
    use_container_width=True,
):
    # Build config dict
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
            "description": product_description or "",  # empty = auto-detect
            "category": product_category or "",  # empty = auto-detect
            "homepage_url": homepage_url,
            "pricing_url": pricing_url or "",
        },
        "target_markets": selected_market_keys,
        "target_market": selected_market_keys[0],
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
    n_markets = len(selected_market_keys)

    with st.status(f"Running Market Entry Radar for {n_markets} market{'s' if n_markets > 1 else ''}...", expanded=True) as status:
        progress_bar = st.progress(0)
        step_log = st.empty()

        def on_progress(step: int, message: str):
            progress_bar.progress(min(max(step, 0) / 5, 1.0))
            step_label = "0 (detect)" if step == 0 else str(step)
            step_log.markdown(f"**Step {step_label}/5:** {message}")

        try:
            results = run_multi_market_pipeline(config, env, progress_callback=on_progress)
            progress_bar.progress(1.0)
            status.update(label="Pipeline complete!", state="complete", expanded=False)
        except RuntimeError as e:
            error_text = str(e)
            status.update(label="Pipeline failed", state="error")
            st.error("The pipeline hit an error. See details below.")
            st.code(error_text, language=None)
            st.caption("Copy the error block above and paste it to an AI assistant for troubleshooting help.")
            st.stop()
        except Exception as e:
            status.update(label="Pipeline failed", state="error")
            st.error("An unexpected error occurred. See details below.")
            st.code(f"Error type: {type(e).__name__}\nError: {e}", language=None)
            st.caption("Copy the error block above and paste it to an AI assistant for troubleshooting help.")
            st.stop()

    # Display results
    markets = results["markets"]
    per_market = results["per_market"]

    st.success(f"Analysis complete for {len(markets)} market{'s' if len(markets) > 1 else ''}!")

    # Cross-market comparison (show first if available)
    if results.get("comparison"):
        comparison_path = results["comparison"]["comparison_path"]
        try:
            comparison_content = Path(comparison_path).read_text(encoding="utf-8")

            st.divider()
            st.subheader("Cross-Market Comparison")
            st.markdown(f"*Which market to enter first and why*")

            st.download_button(
                label="Download Comparison Report (Markdown)",
                data=comparison_content,
                file_name=Path(comparison_path).name,
                mime="text/markdown",
                use_container_width=True,
            )

            with st.expander("View Cross-Market Comparison", expanded=True):
                st.markdown(comparison_content)
        except FileNotFoundError:
            st.warning(f"Comparison report not found at {comparison_path}")

    # Per-market reports in tabs
    if len(markets) > 1:
        st.divider()
        st.subheader("Individual Market Reports")
        tabs = st.tabs([m.upper() for m in markets])

        for tab, market in zip(tabs, markets):
            with tab:
                result = per_market[market]
                st.markdown(
                    f"**{market.upper()}**: "
                    f"{len(result['discovery_data']['competitors'])} competitors discovered, "
                    f"{result['scrape_data']['success_count']} pages scraped"
                )

                report_path = result["report_data"]["report_path"]
                try:
                    report_content = Path(report_path).read_text(encoding="utf-8")

                    st.download_button(
                        label=f"Download {market.upper()} Report (Markdown)",
                        data=report_content,
                        file_name=Path(report_path).name,
                        mime="text/markdown",
                        use_container_width=True,
                        key=f"download_{market}",
                    )

                    st.markdown(report_content)
                except FileNotFoundError:
                    st.warning(f"Report not found at {report_path}")
    else:
        # Single market -- show inline
        market = markets[0]
        result = per_market[market]
        st.markdown(
            f"Discovered {len(result['discovery_data']['competitors'])} competitors, "
            f"scraped {result['scrape_data']['success_count']} pages."
        )

        report_path = result["report_data"]["report_path"]
        try:
            report_content = Path(report_path).read_text(encoding="utf-8")

            st.divider()
            st.subheader("Market Entry Brief")

            st.download_button(
                label="Download Report (Markdown)",
                data=report_content,
                file_name=Path(report_path).name,
                mime="text/markdown",
                use_container_width=True,
            )

            st.markdown(report_content)
        except FileNotFoundError:
            st.warning(f"Report file not found at {report_path}")

elif not can_run:
    missing_fields = []
    if not homepage_url:
        missing_fields.append("Homepage URL")
    if not selected_market_keys:
        missing_fields.append("Target Market(s)")
    if not keys_ready:
        missing_fields.append("API Keys (see sidebar)")
    st.info(f"Fill in required fields to run: {', '.join(missing_fields)}")

# ---------------------------------------------------------------
# Footer
# ---------------------------------------------------------------

st.divider()
st.caption(
    "Built by [Dvir Sharon](https://www.linkedin.com/in/dvirsharon/) | "
    "Powered by [Bright Data](https://brightdata.com) + "
    "[Anthropic Claude](https://anthropic.com) | "
    "Built with [Claude Code](https://claude.ai/claude-code)"
)
