"""
Bright Data client abstraction layer.

Two modes:
1. SDK mode (default): Uses brightdata-sdk. Auto-creates zones, only needs API token.
2. Legacy mode: Uses raw requests.post with manual zone names.

SDK mode activates by default. Legacy mode activates when BD_USE_SDK=false.
"""

import json
import time

import requests
from rich.console import Console

console = Console()

# Try to import the Bright Data SDK
try:
    from brightdata.sync_client import SyncBrightDataClient
    from brightdata import exceptions as bd_exceptions

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# SDK default zone names (auto-created by the SDK)
SDK_SERP_ZONE = "sdk_serp"
SDK_UNLOCKER_ZONE = "sdk_unlocker"

# Legacy default zone names
LEGACY_SERP_ZONE = "serp_api1"
LEGACY_UNLOCKER_ZONE = "web_unlocker1"


def is_sdk_mode(env: dict) -> bool:
    """Check if SDK mode is active."""
    if not SDK_AVAILABLE:
        return False
    return env.get("BD_USE_SDK", "true").lower() == "true"


def _get_sdk_client(env: dict) -> "SyncBrightDataClient":
    """Get or create a SyncBrightDataClient instance."""
    token = env["BRIGHT_DATA_API_KEY"]
    return SyncBrightDataClient(
        token=token,
        auto_create_zones=True,
    )


# -------------------------------------------------------------------
# SCRAPING (Web Unlocker) -- returns markdown content
# -------------------------------------------------------------------

def scrape_as_markdown(env: dict, url: str, country: str = None) -> dict:
    """
    Scrape a URL and return markdown content.

    Uses the direct API with data_format=markdown (both SDK and legacy mode
    use the same endpoint, but SDK mode uses auto-created zone names).

    Returns:
        dict with keys: success, content, url, content_length, error
    """
    api_key = env["BRIGHT_DATA_API_KEY"]

    if is_sdk_mode(env):
        zone = SDK_UNLOCKER_ZONE
        # Ensure zone exists by touching the SDK client
        try:
            _get_sdk_client(env)
        except Exception:
            pass  # Zone might already exist, or we proceed anyway
    else:
        zone = env.get("BRIGHT_DATA_UNLOCKER_ZONE", LEGACY_UNLOCKER_ZONE)

    return _raw_scrape(api_key, zone, url, country)


def _raw_scrape(api_key: str, zone: str, url: str, country: str = None) -> dict:
    """Make a direct API call for markdown scraping."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "zone": zone,
        "url": url,
        "format": "raw",
        "data_format": "markdown",
    }
    if country:
        payload["country"] = country

    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            headers=headers,
            json=payload,
            timeout=90,
        )
        if response.status_code == 200:
            content = response.text
            if len(content) > 200:
                return {
                    "success": True,
                    "content": content,
                    "url": url,
                    "content_length": len(content),
                }
            else:
                return {"success": False, "url": url, "error": "Content too short (likely blocked)"}
        else:
            return {
                "success": False,
                "url": url,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }
    except requests.exceptions.Timeout:
        return {"success": False, "url": url, "error": "Request timed out (90s)"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "url": url, "error": str(e)}


# -------------------------------------------------------------------
# SEARCH (SERP API) -- returns structured results
# -------------------------------------------------------------------

def search_serp(env: dict, query: str, engine: str = "google",
                gl: str = None, hl: str = None, search_url: str = None) -> dict:
    """
    Run a SERP search query.

    In SDK mode: uses brightdata-sdk's structured search API.
    In legacy mode: uses raw API with pre-built search URL.

    Returns:
        dict with organic/general results, or {"_error": True, ...} on failure.
    """
    if is_sdk_mode(env):
        return _sdk_search(env, query, engine, gl, hl)
    else:
        if not search_url:
            raise ValueError("search_url is required in legacy mode")
        return _legacy_search(env, search_url)


def _sdk_search(env: dict, query: str, engine: str, gl: str, hl: str) -> dict:
    """Search via brightdata-sdk."""
    try:
        client = _get_sdk_client(env)

        # Map engine name to SDK method
        location = _gl_to_location(gl)
        language = hl or "en"

        if engine in ("google", "yahoo_japan"):
            # Yahoo Japan queries go through Google with JP settings
            result = client.search.google(
                query=query,
                location=location,
                language=language,
                num_results=10,
            )
        elif engine == "naver":
            # Naver is not directly supported by SDK -- fall back to Google KR
            result = client.search.google(
                query=query,
                location=location,
                language=language,
                num_results=10,
            )
        elif engine == "yandex":
            result = client.search.yandex(
                query=query,
                location=location,
                language=language,
                num_results=10,
            )
        elif engine == "baidu":
            # Baidu not supported by SDK -- fall back to Google CN
            result = client.search.google(
                query=query,
                location=location,
                language=language,
                num_results=10,
            )
        else:
            result = client.search.google(
                query=query,
                location=location,
                language=language,
                num_results=10,
            )

        if not result.success:
            return {
                "_error": True,
                "status_code": 0,
                "body": result.error or "SDK search failed",
            }

        # Convert SDK SearchResult to the format step_01 expects
        # SDK returns result.data as a list of dicts with search results
        organic = []
        if result.data:
            for item in result.data:
                organic.append({
                    "link": item.get("url") or item.get("link", ""),
                    "title": item.get("title", ""),
                    "description": item.get("description") or item.get("snippet", ""),
                })

        return {"organic": organic}

    except Exception as e:
        return {
            "_error": True,
            "status_code": 0,
            "body": f"SDK error: {str(e)}",
        }


def _legacy_search(env: dict, search_url: str) -> dict:
    """Search via raw API (existing approach)."""
    api_key = env["BRIGHT_DATA_API_KEY"]
    zone = env.get("BRIGHT_DATA_SERP_ZONE", LEGACY_SERP_ZONE)

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
                return {"raw_html": response.text[:5000]}
        else:
            return {
                "_error": True,
                "status_code": response.status_code,
                "body": response.text[:500],
            }
    except requests.exceptions.RequestException as e:
        return {
            "_error": True,
            "status_code": 0,
            "body": str(e),
        }


def _gl_to_location(gl: str) -> str | None:
    """Convert a geo-location code to a location name for the SDK."""
    if not gl:
        return None
    mapping = {
        "jp": "Japan",
        "kr": "South Korea",
        "cn": "China",
        "ru": "Russia",
        "au": "Australia",
        "sg": "Singapore",
        "de": "Germany",
        "gb": "United Kingdom",
        "fr": "France",
        "br": "Brazil",
        "us": "United States",
    }
    return mapping.get(gl.lower())


# -------------------------------------------------------------------
# ERROR FORMATTING
# -------------------------------------------------------------------

def format_scrape_error(url: str, error: str) -> str:
    """Format a scrape error as a structured block."""
    return (
        "\n"
        "============================================================\n"
        "  SCRAPE ERROR -- Could not read page\n"
        "============================================================\n"
        "\n"
        f"  URL: {url}\n"
        f"  Error: {error}\n"
        "\n"
        "  --- Fix it ---\n"
        "  1. Verify the URL is correct and accessible in a browser\n"
        "  2. Check your Bright Data API token is active\n"
        "  3. If using SDK mode, ensure auto-zone creation is working\n"
        "  4. If using legacy mode, check your Web Unlocker zone\n"
        "\n"
        "  Copy this entire block and paste it to an AI assistant for help.\n"
        "============================================================\n"
    )
