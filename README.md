# Market Entry Radar

I've run GTM research for market entries across APAC and EMEA at Bright Data. Every time, the process was the same: manually searching local search engines, scraping competitor sites, comparing pricing, figuring out cultural nuances. Hours of tab-switching for each market.

So I built a pipeline that does it in one run.

You give it your product category and one or more target markets. It runs geo-targeted SERP queries on the right search engines (not just Google, Yahoo Japan for Japan, Naver for Korea, Baidu for China), scrapes every competitor it finds, runs three analysis passes through Claude, layers in market-specific intelligence, and spits out a structured Market Entry Brief with specific next actions.

Pick multiple markets and it runs each one, then generates a cross-market comparison that ranks them and tells you where to enter first.

Is it as good as hiring McKinsey? No. Does it get you 80% of the way there for $10-15 per market in API costs? Yeah, it does.

## How It Works

Five steps, fully automated:

1. **DISCOVER** - Runs 30-50 geo-targeted SERP queries across the search engines that actually matter in your target market. Yahoo Japan still has ~25% search share. Naver dominates Korea. If you're only checking Google, you're missing half the competitive landscape.

2. **SCRAPE** - Hits every discovered competitor's homepage, pricing page, features page, and about page using Bright Data Web Unlocker. Returns clean Markdown, not raw HTML. Handles bot detection and geo-targeting automatically.

3. **ANALYZE** - Claude runs three separate analysis passes: a positioning matrix (how each competitor positions and where the white space is), a pricing benchmark (tiers, local currency, feature gates), and a content gap map (topics competitors rank for that you don't cover).

4. **ENRICH** - This is the part that normally costs $50K+ in consulting fees. Pre-built market profiles with real data: buyer behavior patterns, typical sales cycles, regulatory requirements, cultural considerations, channel strategies. I built these from actual market entry projects, not generic advice.

5. **DELIVER** - Synthesizes everything into one Market Entry Brief with an executive summary, competitive landscape, pricing recommendations, content opportunities, localization warnings, a 90-day phased entry plan, launch readiness checklist, and a "do this week" action list. If you ran multiple markets, it also generates a cross-market comparison.

## Supported Markets

| Market | Search Engines | What's in the Profile |
|---|---|---|
| Japan | Google.co.jp, Yahoo Japan | Ringi-seido consensus buying, 12+ month enterprise cycles, local vendor preferences |
| Korea | Naver, Google.co.kr | Naver SEO specifics, KakaoTalk business comms, chaebol navigation |
| Australia | Google.com.au | Easiest English-speaking APAC entry, APAC beachhead strategy |
| Singapore | Google.com.sg | Regional HQ positioning, government grants, 5.9M population reality check |
| Germany | Google.de | GDPR strictness (real enforcement data), Mittelstand, DACH bundling |
| UK | Google.co.uk | Post-Brexit UK GDPR, G-Cloud framework, London tech hub |
| France | Google.fr | CNIL enforcement patterns, La French Tech ecosystem, Toubon Law |
| Brazil | Google.com.br | LGPD, PIX payment system, NF-e electronic invoicing, complex tax system |

You can add your own markets by dropping a YAML file in `market_profiles/`.

## Quick Start

**You need:**
- Python 3.10+
- A [Bright Data](https://brightdata.com) account (SERP API zone + Web Unlocker zone)
- An [Anthropic](https://console.anthropic.com) API key

```bash
git clone https://github.com/iamdvirsharon/market-entry-radar.git
cd market-entry-radar
pip install -r requirements.txt
```

### Run It

**Windows users:** Double-click `start.bat`. That's it. Browser opens, fill in the form, hit run.

**Everyone else:**
```bash
python -m streamlit run app.py
```

The web UI lets you pick one or more markets, enter your product info, and paste your API keys. No config files to edit. Select multiple markets and you get individual reports plus a cross-market comparison.

**Prefer the CLI?**
```bash
cp .env.example .env    # add your API keys
# edit config.yaml      # add your product details
python run.py
```

## What the Output Looks Like

The pipeline generates a Markdown report with these sections:

- **Executive Summary** - Go/no-go signal. Is this market worth entering and why.
- **Competitive Landscape** - Positioning matrix, competitor map with SERP frequency data, recommended positioning angle with specific value prop language
- **Pricing Benchmark** - Comparison table with local currency and USD, specific entry price recommendation, tier structure, payment methods
- **Content & SEO Gaps** - Ranked content opportunities with difficulty scores, 90-day content calendar with specific titles and keywords
- **Market Intelligence** - Buyer behavior, channel strategy, localization warnings, regulatory flags
- **Entry Sequence** - 90-day phased plan with named partners, certifications, and hire recommendations
- **Launch Readiness Checklist** - Binary checklist of what must be done before entering the market
- **This Week Actions** - Top 5 tactical things to do this week, not strategy, execution

If you run multiple markets, you also get a **Cross-Market Comparison** that ranks markets by attractiveness and recommends entry sequence.

Reports save to `output/` with timestamps.

## What It Costs

Per market analysis with default settings:

| API | Usage | Cost |
|---|---|---|
| Bright Data SERP API | ~40-80 queries | $2-5 |
| Bright Data Web Unlocker | ~60-120 pages | $3-8 |
| Anthropic Claude | ~4 analysis calls | $2-5 |
| **Total** | | **~$10-15** |

## Project Structure

```
market-entry-radar/
├── app.py                    # Web UI (Streamlit)
├── run.py                    # CLI entry point
├── pipeline.py               # Shared pipeline logic
├── config.yaml               # Product config (CLI only)
├── .env.example              # API key template
├── requirements.txt
├── start.bat                 # Windows one-click launcher
│
├── steps/
│   ├── step_01_discover.py   # SERP API discovery
│   ├── step_02_scrape.py     # Web Unlocker scraping
│   ├── step_03_analyze.py    # Claude competitive analysis
│   ├── step_04_enrich.py     # Market profile enrichment
│   └── step_05_deliver.py    # Report generation
│
├── market_profiles/          # Pre-built market intelligence (8 markets)
├── prompts/                  # Claude analysis prompts
├── output/                   # Generated reports
└── raw_data/                 # Raw scrapes and intermediate files
```

## Built With

- [Bright Data](https://brightdata.com) SERP API + Web Unlocker
- [Anthropic Claude](https://anthropic.com) for analysis
- [Streamlit](https://streamlit.io) for the web UI
- [Claude Code](https://claude.ai/code) to build the whole thing

## Author

**Dvir Sharon** - I run GTM strategy at Bright Data, focused on regional expansion across APAC and EMEA. The market profiles in this repo come from real expansion projects I've worked on.

[LinkedIn](https://www.linkedin.com/in/dvirsharon/) | Built with [Claude Code](https://claude.ai/code)
