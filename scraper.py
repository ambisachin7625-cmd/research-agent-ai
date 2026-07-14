"""
Web Scraper module for the Research Agent.

This module is responsible for fetching the full HTML content of a URL,
stripping all HTML tags using BeautifulSoup, and returning clean readable
plain text from the page.

--- Install Instructions ---
# pip install requests
# pip install beautifulsoup4
----------------------------
"""

# 'requests' lets us download raw HTML from any URL on the internet
import requests

# BeautifulSoup is a library that reads HTML and lets us pull out the text
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_domain_score(url: str) -> int:
    """Assigns a trust score to a source based on its domain."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.endswith('.gov') or domain.endswith('.int'):
            return 10
        if domain.endswith('.edu') or 'arxiv.org' in domain or 'nature.com' in domain or 'sciencedirect.com' in domain:
            return 9
        if 'nytimes.com' in domain or 'bbc.co' in domain or 'wsj.com' in domain or 'reuters.com' in domain or 'cnn.com' in domain or 'theguardian.com' in domain:
            return 7
        if 'reddit.com' in domain or 'quora.com' in domain or 'stackexchange.com' in domain:
            return 2
        return 4  # Default standard site / blog
    except Exception:
        return 4


def get_source_quality_label(score: int) -> str:
    """Returns a human-readable quality label for a numeric trust score."""
    if score >= 10:
        return "Government"
    if score >= 9:
        return "Research / Educational"
    if score >= 7:
        return "Major News"
    if score >= 4:
        return "Blog / Standard Site"
    return "Forum / Community"


def fetch_text(url: str) -> str:
    """
    Fetches the full HTML page at the given URL, strips all HTML tags,
    and returns clean plain text capped at 3000 characters.

    Args:
        url (str): The web page URL to fetch.

    Returns:
        str: Clean plain text content of the page (max 3000 characters).
             Returns an empty string "" if anything fails.
    """
    try:
        # --- Step 1: Download the page HTML ---
        # We set a timeout=10 so that slow/unresponsive pages don't freeze
        # the program. If the page takes more than 10 seconds, we give up.
        # headers mimic a real browser so most websites don't block our request.
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, timeout=10, headers=headers)

        # If the server returned an error (e.g. 404, 403, 500), stop here
        response.raise_for_status()

        # --- Step 2: Parse the raw HTML with BeautifulSoup ---
        # 'html.parser' is Python's built-in HTML parser — no extra install needed
        soup = BeautifulSoup(response.text, "html.parser")

        # --- Step 3: Remove script and style tags ---
        # These contain JavaScript code and CSS styling — not useful text.
        # We remove them before extracting text so they don't pollute output.
        for tag in soup(["script", "style"]):
            tag.decompose()  # completely removes the tag and its contents

        # --- Step 4: Extract all visible text from the remaining HTML ---
        # get_text() pulls out all readable text from the page.
        # separator="\n" puts each paragraph/block on a new line.
        # strip=True removes extra whitespace from each line.
        raw_text = soup.get_text(separator="\n", strip=True)

        # --- Step 5: Clean up blank lines ---
        # After stripping tags, there are often many consecutive empty lines.
        # We filter them out so the result is dense and readable.
        lines = [line for line in raw_text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # --- Step 6: Cap at 3000 characters ---
        # Web pages can be very long. We only keep the first 3000 characters
        # to stay focused and avoid using too many tokens later.
        return clean_text[:3000]

    except Exception:
        # --- Silent error handling ---
        # If ANYTHING goes wrong (network error, timeout, bad HTML, blocked
        # by website, etc.) we return an empty string instead of crashing.
        # The agent will simply skip this URL and move on to the next one.
        return ""
