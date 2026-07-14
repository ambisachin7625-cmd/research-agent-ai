"""
Unit tests for the SearchClient in search.py.
Uses unittest.mock to test logic without making real Tavily API calls.
"""

import unittest
from unittest.mock import MagicMock, patch
from search import SearchClient

class TestSearchClient(unittest.TestCase):

    @patch('search.Config')
    def setUp(self, mock_config):
        """Set up the mock configuration and instantiate search client."""
        mock_config.TAVILY_API_KEY = "mock-tavily-key"
        mock_config.validate.return_value = True
        
        # Patch the TavilyClient initialization
        with patch('search.TavilyClient') as mock_tavily_cls:
            self.mock_tavily = MagicMock()
            mock_tavily_cls.return_value = self.mock_tavily
            self.search_client = SearchClient()

    def test_search_empty_query(self):
        """Test that search returns an empty list immediately for empty inputs."""
        results = self.search_client.search("")
        self.assertEqual(results, [])
        self.mock_tavily.search.assert_not_called()

    def test_search_success_mapping(self):
        """Test that Tavily 'content' field is correctly mapped to 'snippet'."""
        # Mock Tavily SDK response
        self.mock_tavily.search.return_value = {
            "results": [
                {
                    "title": "AI Assistant Productivity",
                    "url": "https://example.com/productivity",
                    "content": "AI coding assistants increase speed by 25%."
                },
                {
                    "title": "Software Engineering Hiring",
                    "url": "https://example.com/hiring",
                    "content": "Hiring for AI skills is up 50% in 2026."
                }
            ]
        }

        results = self.search_client.search("AI productivity")
        self.assertEqual(len(results), 2)
        
        # Check first result structure
        self.assertEqual(results[0]["title"], "AI Assistant Productivity")
        self.assertEqual(results[0]["url"], "https://example.com/productivity")
        self.assertEqual(results[0]["snippet"], "AI coding assistants increase speed by 25%.")
        
        # Check second result structure
        self.assertEqual(results[1]["title"], "Software Engineering Hiring")
        self.assertEqual(results[1]["url"], "https://example.com/hiring")
        self.assertEqual(results[1]["snippet"], "Hiring for AI skills is up 50% in 2026.")
        
        # Verify SDK call was made with expected arguments
        self.mock_tavily.search.assert_called_once_with(query="AI productivity", max_results=5)

    def test_search_api_failure(self):
        """Test that API errors are caught and wrapped in a RuntimeError."""
        self.mock_tavily.search.side_effect = Exception("API connection timed out")

        with self.assertRaises(RuntimeError) as context:
            self.search_client.search("AI jobs")
            
        self.assertIn("Tavily search failed for query 'AI jobs'", str(context.exception))
        self.assertIn("API connection timed out", str(context.exception))

if __name__ == '__main__':
    unittest.main()
