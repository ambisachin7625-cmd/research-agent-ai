"""
Web Search Client module for the Research Agent.

This module integrates with the Tavily Search API to perform web searches 
and retrieve structured metadata (title, URL, and snippet) for query results.
"""

from tavily import TavilyClient
from config import Config

class SearchClient:
    """Client for interacting with the Tavily Search API."""

    def __init__(self):
        """Initializes the TavilyClient with credentials from config.py."""
        Config.validate_search()
        self.client = TavilyClient(api_key=Config.TAVILY_API_KEY)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Executes a web search for the given query and retrieves top results.

        Args:
            query (str): The search query.
            max_results (int): The number of search results to return (default 5).

        Returns:
            list[dict]: A list of dictionaries, where each dictionary represents 
                        a search result with keys: 'title', 'url', and 'snippet'.
        
        Raises:
            RuntimeError: If the API request fails or returns an unexpected response.
        """
        if not query:
            return []

        try:
            # Execute search using Tavily Python SDK.
            # We fetch standard search depth ("basic") with max_results constraint.
            response = self.client.search(query=query, max_results=max_results)
            
            # Extract results. Tavily SDK returns a dict with a "results" list.
            raw_results = response.get("results", [])
            
            formatted_results = []
            for result in raw_results:
                formatted_results.append({
                    "title": result.get("title", "No Title").strip(),
                    "url": result.get("url", "").strip(),
                    # Tavily's API returns the web page snippet in the 'content' field.
                    # We map this content to 'snippet' as per requirements.
                    "snippet": result.get("content", "No Snippet Available").strip()
                })
                
            return formatted_results

        except Exception as e:
            # Handle client, network, credentials, or remote service errors gracefully
            raise RuntimeError(f"Tavily search failed for query '{query}': {str(e)}") from e
