import unittest
from unittest.mock import MagicMock, patch
from memory import MemoryStore

class TestMemoryStore(unittest.TestCase):
    
    @patch('memory.chromadb.EphemeralClient')
    def setUp(self, mock_client):
        # We mock chromadb so it doesn't try to download models or run actual DB logic during unit tests
        self.mock_client_instance = MagicMock()
        mock_client.return_value = self.mock_client_instance
        self.mock_collection = MagicMock()
        self.mock_client_instance.get_or_create_collection.return_value = self.mock_collection
        
        self.memory = MemoryStore()

    def test_chunk_text(self):
        text = "This is a short sentence."
        chunks = self.memory.chunk_text(text, chunk_size=10)
        
        # 'This is a' = 9 chars + 1 space = 10, next is 'short'
        self.assertTrue(len(chunks) > 1)
        self.assertIn("This is a", chunks[0])

    def test_add_empty_text(self):
        self.memory.add("   ", "http://example.com", "test query")
        self.mock_collection.add.assert_not_called()

    def test_add_valid_text(self):
        text = "Hello world! This is a test of the vector storage."
        self.memory.add(text, "http://example.com", "test query")
        
        # Check that add was called on the collection
        self.mock_collection.add.assert_called_once()
        
        # Verify the arguments passed to collection.add
        _, kwargs = self.mock_collection.add.call_args
        self.assertIn('documents', kwargs)
        self.assertIn('metadatas', kwargs)
        self.assertIn('ids', kwargs)
        
        self.assertEqual(kwargs['metadatas'][0]['url'], "http://example.com")
        self.assertEqual(kwargs['metadatas'][0]['source_query'], "test query")

    def test_search_empty_collection(self):
        self.mock_collection.count.return_value = 0
        results = self.memory.search("test")
        self.assertEqual(results, [])

    def test_search_with_results(self):
        self.mock_collection.count.return_value = 1
        self.mock_collection.query.return_value = {
            "documents": [["Test document content"]],
            "metadatas": [[{"url": "http://example.com", "source_query": "q"}]]
        }
        
        results = self.memory.search("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Test document content")
        self.assertEqual(results[0]["url"], "http://example.com")

    def test_clear(self):
        self.memory.clear()
        self.mock_client_instance.delete_collection.assert_called_with("research_memory")
        self.assertEqual(self.memory.chunk_id_counter, 0)

if __name__ == "__main__":
    unittest.main()
