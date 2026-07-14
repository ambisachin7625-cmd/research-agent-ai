"""
Memory module for the Research Agent.

This module provides vector storage using ChromaDB to store and retrieve
scraped web page content. It chunks large text, generates embeddings,
and allows for semantic search.
"""

import chromadb
from typing import List, Dict, Any

class MemoryStore:
    def __init__(self):
        """
        Initializes an in-memory ChromaDB client and creates a collection.
        Using an EphemeralClient means the data is cleared when the program exits.
        """
        self.client = chromadb.EphemeralClient()
        # Create a new collection (or get it if it somehow exists)
        self.collection = self.client.get_or_create_collection(name="research_memory")
        # Keep track of a global ID counter for chunks
        self.chunk_id_counter = 0

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Splits a long string of text into smaller chunks of approximately 'chunk_size' characters.
        We split by lines/paragraphs to avoid cutting sentences in half where possible.
        """
        chunks = []
        current_chunk = []
        current_length = 0

        # Split by whitespace or lines (simple approach)
        # Using words makes it easier to reconstruct roughly chunk_size segments
        words = text.split()
        
        for word in words:
            # +1 for the space
            word_len = len(word) + 1
            if current_length + word_len > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_len
            else:
                current_chunk.append(word)
                current_length += word_len
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def add(self, text: str, url: str, query: str, score: int = 4):
        """
        Chunks the input text and adds it to the ChromaDB vector store.
        """
        if not text.strip():
            return

        chunks = self.chunk_text(text)
        
        if not chunks:
            return

        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            documents.append(chunk)
            # Store metadata so we know where this chunk came from
            metadatas.append({"url": url, "source_query": query, "source_score": score})
            ids.append(f"chunk_{self.chunk_id_counter}")
            self.chunk_id_counter += 1

        # Add to the collection
        # ChromaDB automatically handles embedding generation using its default model
        # (all-MiniLM-L6-v2) under the hood.
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the vector database for the top 'n_results' chunks that are most 
        semantically similar to the provided query.
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )

        # Format results into a cleaner list of dictionaries
        formatted_results = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            
            for doc, meta in zip(docs, metas):
                formatted_results.append({
                    "text": doc,
                    "url": meta.get("url", "Unknown"),
                    "source_query": meta.get("source_query", "Unknown"),
                    "score": meta.get("source_score", 4)
                })
                
        return formatted_results

    def clear(self):
        """
        Deletes the collection, resetting the memory for a new session.
        """
        try:
            self.client.delete_collection("research_memory")
            self.collection = self.client.get_or_create_collection(name="research_memory")
            self.chunk_id_counter = 0
        except ValueError:
            pass
