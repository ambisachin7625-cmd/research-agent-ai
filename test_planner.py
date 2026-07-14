"""
Unit tests for the LLMPlanner in planner.py.
Uses unittest.mock to test logic without making real OpenAI API calls.
"""

import unittest
from unittest.mock import MagicMock, patch
from planner import LLMPlanner

class TestLLMPlanner(unittest.TestCase):

    @patch('planner.Config')
    def setUp(self, mock_config):
        """Set up the mock configuration and instantiate planner."""
        mock_config.OPENAI_API_KEY = "mock-key-for-testing"
        mock_config.OPENAI_MODEL = "gpt-4o-mini"
        mock_config.OPENAI_BASE_URL = None
        mock_config.validate.return_value = True
        
        # Patch the OpenAI client instantiation
        with patch('planner.OpenAI') as mock_openai_cls:
            self.mock_client = MagicMock()
            mock_openai_cls.return_value = self.mock_client
            self.planner = LLMPlanner()

    def test_clean_json_response_raw_json(self):
        """Test cleaning standard raw JSON string."""
        raw = '["q1", "q2", "q3"]'
        self.assertEqual(self.planner._clean_json_response(raw), raw)

    def test_clean_json_response_markdown_json(self):
        """Test cleaning JSON wrapped in markdown json block."""
        raw = '```json\n["q1", "q2", "q3"]\n```'
        expected = '["q1", "q2", "q3"]'
        self.assertEqual(self.planner._clean_json_response(raw), expected)

    def test_clean_json_response_markdown_generic(self):
        """Test cleaning JSON wrapped in standard markdown code block."""
        raw = '```\n["q1", "q2", "q3"]\n```'
        expected = '["q1", "q2", "q3"]'
        self.assertEqual(self.planner._clean_json_response(raw), expected)

    def test_generate_queries_success(self):
        """Test standard successful generation of exactly 3 queries."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='["query 1", "query 2", "query 3"]'))
        ]
        self.mock_client.chat.completions.create.return_value = mock_completion

        queries = self.planner.generate_queries("test question")
        self.assertEqual(queries, ["query 1", "query 2", "query 3"])

    def test_generate_queries_nested_dict(self):
        """Test parsing when the model returns a dictionary wrapping the list."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"queries": ["q1", "q2", "q3"]}'))
        ]
        self.mock_client.chat.completions.create.return_value = mock_completion

        queries = self.planner.generate_queries("test question")
        self.assertEqual(queries, ["q1", "q2", "q3"])

    def test_generate_queries_too_few_elements(self):
        """Test that list is padded when the model returns fewer than 3 queries."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='["q1", "q2"]'))
        ]
        self.mock_client.chat.completions.create.return_value = mock_completion

        queries = self.planner.generate_queries("some question")
        self.assertEqual(len(queries), 3)
        self.assertEqual(queries[0], "q1")
        self.assertEqual(queries[1], "q2")
        self.assertTrue(queries[2].startswith("Additional context for:"))

    def test_generate_queries_too_many_elements(self):
        """Test that list is sliced to exactly 3 when the model returns more than 3 queries."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='["q1", "q2", "q3", "q4"]'))
        ]
        self.mock_client.chat.completions.create.return_value = mock_completion

        queries = self.planner.generate_queries("some question")
        self.assertEqual(queries, ["q1", "q2", "q3"])

    def test_generate_queries_invalid_json(self):
        """Test error handling when JSON is malformed."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='invalid json here'))
        ]
        self.mock_client.chat.completions.create.return_value = mock_completion

        with self.assertRaises(RuntimeError) as context:
            self.planner.generate_queries("some question")
        self.assertIn("Failed to generate search queries", str(context.exception))

if __name__ == '__main__':
    unittest.main()
