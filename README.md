# Market Entry Radar

I kept doing the same thing every time we evaluated a new market at Bright Data -- manually searching local search engines, scraping competitor sites, comparing pricing page by page. So I automated it.

You paste your homepage URL, pick a country. The tool does the rest: finds local competitors, reads their sites, and gives you a Market Entry Brief with what to do first.

## What You Get

A full Market Entry Brief with actionable intelligence. Here's a snippet from a real run (project management software → Japan):

<details>
<summary><strong>Example: Competitive Landscape</strong></summary>

> **White space:** No competitor strongly owns "mid-market Japanese companies modernizing from Excel-based project tracking." This is a viable entry position.

| Competitor | Positioning | Target Buyer | SERP Frequency |
|---|---|---|---|
| Backlog | "Work management for teams who ship" | Dev + PM teams | 18 |
| Asana (JP) | "Work management platform" | Enterprise | 15 |
| Monday.com (JP) | "Work OS" | SMB-Enterprise | 12 |
| Jooto | "Kanban for Japanese teams" | SMB | 11 |
| Brabio! | "Free Gantt chart tool" | SMB, freelancers | 9 |

</details>

<details>
<summary><strong>Example: Pricing Benchmark</strong></summary>

| Competitor | Price Range (JPY) | Price Range (USD) | Free Tier | Annual Discount |
|---|---|---|---|---|
| Backlog | 0 - 28,215/mo | $0 - $190/mo | Yes (10 users) | 17% |
| Asana | USD only | $0 - $30.49/user/mo | Yes (15 users) | 25% |
| Jooto | 0 - 1,078/user/mo | $0 - $7.25/user/mo | Yes (4 users) | ~15% |

> **Recommendation:** Price in JPY at 980-1,500/user/month. Only 2 of 12 competitors do this today.

</details>

<details>
<summary><strong>Example: "Do This Week" Actions</strong></summary>

1. **Register a .co.jp domain and set up a Japanese landing page** -- Use Backlog's layout as reference. 8 of 12 competitors have dedicated JP domains. Time: 2-3 days.

2. **Email Nulab's partnership team about integration** -- Backlog is the market leader with 200k+ users. An integration partnership gives instant credibility. Time: 1 hour.

3. **Create a comparison page targeting "プロジェクト管理ツール 比較"** -- Only 2 competitors have comparison content in Japanese. High purchase intent keyword. Time: 1 day.

4. **Set up JPY pricing with annual invoicing** -- Japanese procurement teams expect JPY + formal contracts. Only 2 of 12 competitors do this. Time: 1-2 days.

5. **Join the IT導入補助金 (IT Subsidy) vendor registry** -- Government subsidizes up to 50% of SaaS costs for SMBs. Time: 2-3 hours.

</details>

The full report also includes content & SEO gaps, buyer behavior analysis, localization warnings, regulatory notes, and a 12-week entry sequence.

Pick multiple markets and you get individual reports plus a cross-market comparison with a recommended entry sequence.

## Run It

### GitHub Codespaces (easiest -- nothing to install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/iamdvirsharon/market-entry-radar)

Click the button, wait for setup (~2 min), then run:

```
python -m streamlit run app.py
```

Browser opens. Pick your LLM provider, paste your API keys, pick a market, enter your homepage URL, hit run.

### Run Locally

```
git clone https://github.com/iamdvirsharon/market-entry-radar.git
cd market-entry-radar
pip install -r requirements.txt
python -m streamlit run app.py
```

Windows users: double-click `start.bat`.

**You need:**
- [Bright Data](https://brightdata.com) API token -- SDK mode auto-creates zones, free tier available (5,000 req/month)
- **One** LLM API key (pick either):
  - [Anthropic Claude](https://console.anthropic.com) -- best quality
  - [Google Gemini](https://aistudio.google.com/apikey) -- free tier, no credit card needed

### CLI Alternative

```
cp .env.example .env   # add your API keys
python run.py           # edit config.yaml first
```

## Supported Markets

| Market | Search Engines | Profile |
|---|---|---|
| Japan | Google.co.jp, Yahoo Japan | Full |
| Korea | Naver, Google.co.kr | Full |
| Australia | Google.com.au | Full |
| Singapore | Google.com.sg | Full |
| Germany | Google.de | Full |
| UK | Google.co.uk | Full |
| France | Google.fr | Full |
| Brazil | Google.com.br | Full |

Add your own by dropping a YAML file in `market_profiles/`.

Pick multiple markets and you get individual reports plus a cross-market comparison.

## What It Costs

| Component | Per Market | Notes |
|---|---|---|
| Bright Data (SERP + Unlocker) | $3-8 | SDK mode, free tier: 5,000 req/month |
| Claude (Anthropic) | $2-5 | Sonnet for analysis |
| Gemini (Google) | $0 | Free tier: 5-15 req/min |
| **Total with Claude** | **~$5-13** | |
| **Total with Gemini** | **~$3-8** | LLM calls are free |

## How It Works

1. **DETECT** -- Scrapes your homepage, auto-detects what your product is
2. **DISCOVER** -- Runs geo-targeted SERP queries across local search engines
3. **SCRAPE** -- Deep-reads competitor homepages, pricing pages, features, about pages
4. **ANALYZE** -- AI analysis: positioning matrix, pricing benchmark, content gaps
5. **ENRICH** -- Adds market-specific intelligence: buyer behavior, regulations, cultural norms
6. **DELIVER** -- Synthesizes everything into an actionable Market Entry Brief

## Author

**Dvir Sharon** -- [LinkedIn](https://www.linkedin.com/in/dvirsharon/)

Built with [Bright Data](https://brightdata.com) + [Claude](https://anthropic.com)/[Gemini](https://aistudio.google.com) + [Claude Code](https://claude.ai/code)
