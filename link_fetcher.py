"""
Live project link extraction via web search.

Searches the web for a query, returns structured link metadata,
and optionally validates that each URL responds.
"""

from urllib.parse import urlparse

import requests

from config import Config
from scraper import get_domain_score, get_source_quality_label
from search import SearchClient

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _check_url_live(url: str, timeout: int = 4) -> bool:
    """Return True if the URL responds with a success status (with faster timeout)."""
    try:
        # Use HEAD request first with reduced timeout for speed
        response = requests.head(
            url, timeout=timeout, headers=_BROWSER_HEADERS, allow_redirects=True
        )
        if response.status_code >= 400:
            # If HEAD fails, try GET with same timeout
            response = requests.get(
                url, timeout=timeout, headers=_BROWSER_HEADERS, allow_redirects=True
            )
        return response.status_code < 400
    except requests.exceptions.Timeout:
        # If URL is slow, assume it's live
        return True
    except Exception:
        # If any other error, assume offline
        return False


def fetch_live_links(
    query: str,
    max_results: int | None = None,
    validate: bool = True,
) -> list[dict]:
    """
    Search for a topic and return live project/source links.

    Args:
        query: Search topic or project name.
        max_results: Number of links to fetch (defaults to Config.MAX_SEARCH_RESULTS).
        validate: When True, ping each URL to confirm it is reachable.

    Returns:
        List of dicts with title, url, snippet, domain, score, quality, and live status.
    """
    if not query or not query.strip():
        return []

    limit = max_results or Config.MAX_SEARCH_RESULTS
    client = SearchClient()
    results = client.search(query.strip(), max_results=limit)

    links: list[dict] = []
    for result in results:
        url = (result.get("url") or "").strip()
        if not url:
            continue

        score = get_domain_score(url)
        links.append({
            "title": result.get("title", "No Title"),
            "url": url,
            "snippet": result.get("snippet", ""),
            "domain": urlparse(url).netloc,
            "score": score,
            "quality": get_source_quality_label(score),
            "live": _check_url_live(url) if validate else None,
        })

    return links
