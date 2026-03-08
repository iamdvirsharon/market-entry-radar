# Market Entry Radar

**Regional GTM Intelligence Pipeline -- Powered by Bright Data + Claude**

Companies pay consultants $200K for market entry research. This pipeline produces 80% of it in under 2 hours.

Pick your target market. Drop in your product category. Get a complete Market Entry Brief with competitive landscape, pricing benchmark, content gap analysis, and localization recommendations.

## What It Does

A 5-step intelligence pipeline:

1. **DISCOVER** -- Runs 30-50 geo-targeted SERP queries across the RIGHT search engines (not just Google -- Yahoo Japan, Naver for Korea, Baidu for China). Discovers the real local competitive set.
2. **SCRAPE** -- Deep-reads every discovered competitor's homepage, pricing, features, and about pages using Bright Data Web Unlocker. Handles bot detection, JS rendering, and geo-targeting automatically.
3. **ANALYZE** -- Claude produces three analyses: Positioning Matrix (how competitors position), Pricing Benchmark (what they charge), and Content Gap Map (where you can win in SEO).
4. **ENRICH** -- Layers market-specific intelligence from pre-built profiles: buyer behavior, sales cycles, regulatory requirements, cultural norms, channel strategies. This is the data you'd normally pay a consultant for.
5. **DELIVER** -- Generates a complete Market Entry Brief in Markdown -- competitive landscape, pricing recommendations, content opportunities, localization warnings, and a 90-day entry plan.

## Supported Markets

| Market | Search Engines | Profile Depth |
|---|---|---|
| Japan | Google.co.jp + Yahoo Japan | Detailed (buyer behavior, ringi-seido, channel strategy) |
| Korea | Naver + Google.co.kr | Detailed (Naver SEO, KakaoTalk, chaebol navigation) |
| Australia | Google.com.au | Detailed (APAC beachhead strategy) |
| Singapore | Google.com.sg | Detailed (regional HQ positioning) |
| Germany | Google.de | Detailed (GDPR, Mittelstand, DACH bundling) |
| UK | Google.co.uk | Detailed (post-Brexit, G-Cloud) |
| France | Google.fr | Detailed (CNIL, La French Tech) |
| Brazil | Google.com.br | Detailed (LGPD, PIX, NF-e tax system) |

You can add custom markets by creating a new YAML file in `market_profiles/`.

## Quick Start

### Prerequisites

- Python 3.10+
- A [Bright Data](https://brightdata.com) account with:
  - A SERP API zone
  - A Web Unlocker zone
- An [Anthropic](https://console.anthropic.com) API key

### Setup (5 minutes)

```bash
# Clone the repo
git clone https://github.com/iamdvirsharon/market-entry-radar.git
cd market-entry-radar

# Install dependencies
pip install -r requirements.txt
```

### Option A: One-Click (Windows)

Double-click **`start.bat`** -- it installs dependencies and opens the app in your browser. Done.

### Option B: Web UI

```bash
python -m streamlit run app.py
```

A browser tab opens. Fill in your product details, choose a target market from the dropdown, paste your API keys, and click **Run Market Entry Analysis**. The report renders right in the browser with a download button.

### Option C: Command Line

```bash
# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Configure your product and target market
# Edit config.yaml with your details

python run.py
```

Both options run the same 5-step pipeline and save the Market Entry Brief to `output/`.

## Configuration

Edit `config.yaml`:

```yaml
product:
  description: "Project management SaaS for B2B teams"
  category: "project management software"
  homepage_url: "https://your-product.com"
  pricing_url: "https://your-product.com/pricing"

target_market: "japan"  # japan, korea, australia, singapore, germany, uk, france, brazil

known_competitors:
  - "https://competitor1.com"
  - "https://competitor2.com"
```

### Advanced Settings

```yaml
advanced:
  max_competitors: 15        # More = better coverage, higher API cost
  max_queries: 40            # More = better discovery, higher API cost
  request_delay: 1.0         # Seconds between API calls
  claude_model: "claude-sonnet-4-20250514"  # Which Claude model to use
```

## Output

The pipeline generates a structured Market Entry Brief in Markdown with:

- **Executive Summary** -- Go/no-go signal with key findings
- **Competitive Landscape** -- Positioning matrix, competitor map, key insights
- **Pricing Benchmark** -- Pricing comparison table, model analysis, recommendations
- **Content & SEO Gaps** -- Ranked content opportunities with difficulty/opportunity scores
- **Market Intelligence** -- Buyer behavior, channel strategy, localization warnings, regulatory notes
- **Entry Sequence** -- 90-day phased action plan (Foundation, Launch, Optimize)

Reports are saved to `output/` with timestamps and a `_latest` copy for easy access.

## Project Structure

```
market-entry-radar/
├── app.py                         # Web UI (Streamlit) -- recommended
├── run.py                         # CLI entry point
├── pipeline.py                    # Shared pipeline logic
├── config.yaml                    # Product + target market config (CLI only)
├── .env.example                   # API key template (CLI only)
├── requirements.txt               # Python dependencies
│
├── steps/                         # Pipeline steps
│   ├── step_01_discover.py        # SERP API discovery
│   ├── step_02_scrape.py          # Web Unlocker scraping
│   ├── step_03_analyze.py         # Claude competitive analysis
│   ├── step_04_enrich.py          # Market profile enrichment
│   └── step_05_deliver.py         # Report generation
│
├── market_profiles/               # Pre-built market intelligence
│   ├── japan.yaml
│   ├── korea.yaml
│   ├── australia.yaml
│   ├── singapore.yaml
│   ├── germany.yaml
│   ├── uk.yaml
│   ├── france.yaml
│   └── brazil.yaml
│
├── prompts/                       # Claude analysis prompts
│   ├── positioning_analysis.md
│   ├── pricing_analysis.md
│   └── content_gap_analysis.md
│
├── output/                        # Generated reports
└── raw_data/                      # Raw scrapes and analysis files
```

## API Cost Estimate

Per market entry analysis (default settings):

| Service | Estimated Usage | Estimated Cost |
|---|---|---|
| Bright Data SERP API | ~40-80 queries | $2-5 |
| Bright Data Web Unlocker | ~60-120 page scrapes | $3-8 |
| Anthropic Claude API | ~4 analysis calls | $2-5 |
| **Total** | | **$7-18 per market** |

Compare to: $25,000-$150,000 for boutique consulting, $500,000+ for MBB firms.

## Adding Custom Markets

Create a new YAML file in `market_profiles/`:

```yaml
market: "Your Market"
overview: "..."
search_landscape:
  primary_engine: "..."
  secondary_engines: [...]
buyer_behavior:
  decision_making: "..."
  sales_cycle: "..."
# ... see existing profiles for full structure
```

Then set `target_market: "your_market"` in `config.yaml`.

## Built With

- [Bright Data](https://brightdata.com) -- SERP API + Web Unlocker for geo-targeted web intelligence
- [Anthropic Claude](https://anthropic.com) -- AI analysis pipeline
- [Claude Code](https://claude.ai/code) -- Built the entire project
- [Streamlit](https://streamlit.io) -- Web UI
- [Rich](https://github.com/Textualize/rich) -- Terminal UI

## Author

**Dvir Sharon** -- GTM Strategy Lead at Bright Data, specializing in regional market expansion across APAC and EMEA.

- [LinkedIn](https://linkedin.com/in/dvir-sharon)

---

*This tool was built in a weekend with Claude Code. It automates the market entry research process I've done manually for multiple regional launches at Bright Data. The market profiles contain intelligence from real expansion projects, not generic advice.*
