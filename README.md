# Market Entry Radar

Paste your homepage URL, pick a country, get a Market Entry Brief. The tool scrapes your site, figures out what you sell, finds local competitors in that market, analyzes their positioning and pricing, and tells you what to do first. ~$10-15 per market in API costs.

## Run It

### GitHub Codespaces (easiest -- nothing to install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/iamdvirsharon/market-entry-radar)

Click the button, wait for setup (~2 min), then run:

```
python -m streamlit run app.py
```

Browser opens. Paste your API keys in the sidebar, pick a market, enter your homepage URL, hit run.

### Run Locally

```
git clone https://github.com/iamdvirsharon/market-entry-radar.git
cd market-entry-radar
pip install -r requirements.txt
python -m streamlit run app.py
```

Windows users: double-click `start.bat`.

**You need:**
- [Bright Data](https://brightdata.com) API token (SERP API + Web Unlocker zones)
- [Anthropic](https://console.anthropic.com) API key

### CLI Alternative

```
cp .env.example .env   # add your 2 API keys
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

| API | Per Market |
|---|---|
| Bright Data (SERP + Unlocker) | $5-13 |
| Anthropic Claude | $2-5 |
| **Total** | **~$10-15** |

## Author

**Dvir Sharon** -- [LinkedIn](https://www.linkedin.com/in/dvirsharon/)

Built with [Bright Data](https://brightdata.com) + [Anthropic Claude](https://anthropic.com) + [Claude Code](https://claude.ai/code)
