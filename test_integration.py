"""
Integration test for main.py to verify CLI flow and grouping output format.
Mocks user CLI input/output, LLMPlanner, and SearchClient.
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from main import run_agent

class TestIntegrationCLI(unittest.TestCase):

    @patch('main.Config')
    @patch('main.LLMPlanner')
    @patch('main.SearchClient')
    @patch('builtins.input')
    def test_cli_integration_success(self, mock_input, mock_search_cls, mock_planner_cls, mock_config):
        """Verify that main CLI loop works correctly and groups search results."""
        # 1. Mock Configuration validation
        mock_config.validate.return_value = True

        # 2. Mock Planner query generation
        mock_planner = MagicMock()
        mock_planner.generate_queries.return_value = [
            "Query One",
            "Query Two",
            "Query Three"
        ]
        mock_planner_cls.return_value = mock_planner

        # 3. Mock Search Client queries search results
        mock_search = MagicMock()
        mock_search.search.side_effect = lambda query, max_results: [
            {
                "title": f"Result 1 for {query}",
                "url": f"https://example.com/r1?q={query}",
                "snippet": f"Snippet 1 for {query}"
            },
            {
                "title": f"Result 2 for {query}",
                "url": f"https://example.com/r2?q={query}",
                "snippet": f"Snippet 2 for {query}"
            }
        ]
        mock_search_cls.return_value = mock_search

        # 4. Mock user CLI input: first enter a question, then exit
        mock_input.side_effect = ["How is AI impacting jobs?", "exit"]

        # Capture print outputs
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            run_agent()
        finally:
            sys.stdout = sys.__stdout__

        output_text = captured_output.getvalue()

        # Assertions to verify correct console printing and layout
        self.assertIn("Welcome to Research Agent v4", output_text)
        self.assertIn("Generated 3 research queries:", output_text)
        self.assertIn("1. Query One", output_text)
        self.assertIn("2. Query Two", output_text)
        self.assertIn("3. Query Three", output_text)
        
        # Check grouping formatting
        self.assertIn("Query:\nQuery One", output_text)
        self.assertIn("Results:", output_text)
        self.assertIn("Result 1 for Query One", output_text)
        self.assertIn("https://example.com/r1?q=Query One", output_text)
        self.assertIn("Snippet 1 for Query One", output_text)
        
        self.assertIn("Query:\nQuery Two", output_text)
        self.assertIn("Result 1 for Query Two", output_text)
        
        self.assertIn("Query:\nQuery Three", output_text)
        self.assertIn("Result 1 for Query Three", output_text)
        
        self.assertIn("Goodbye!", output_text)

if __name__ == '__main__':
    unittest.main()
