"""
Visual Content helper for the Research Agent.

This module decides whether images are helpful for a research topic and
fetches relevant images using an optional image search API.
"""

import json
import requests
from openai import OpenAI
from config import Config
from typing import List, Dict, Any

class VisualAgent:
    """Determines when images are useful and performs image search."""

    def __init__(self):
        Config.validate()
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
        self.model = Config.OPENAI_MODEL
        self.bing_key = Config.BING_IMAGE_SEARCH_KEY
        self.bing_endpoint = Config.BING_IMAGE_SEARCH_ENDPOINT
        self.unsplash_key = Config.UNSPLASH_ACCESS_KEY

    def _heuristic_image_needed(self, question: str, facts: List[Dict[str, Any]]) -> bool:
        text = question.lower() + " " + " ".join([fact["text"].lower() for fact in facts])
        keywords = [
            "historical", "country", "place", "monument", "animal", "scientific object",
            "product", "technology", "device", "building", "landmark", "map", "diagram",
            "person", "portrait", "vehicle", "plant", "landscape", "architecture", "artifact",
            "statue", "museum", "planet", "chemical", "animal", "species"
        ]
        return any(keyword in text for keyword in keywords)

    def should_use_images(self, question: str, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determines if images would improve understanding and returns suggestions."""
        use_images = self._heuristic_image_needed(question, facts)
        if not use_images:
            return {"include_images": False, "image_queries": []}

        query = question
        if "how" in question.lower() or "why" in question.lower():
            image_queries = [f"{question} illustrative image", f"{question} diagram", f"{question} example image"]
        else:
            image_queries = [f"{question} image", f"{question} photo", f"{question} visual representation"]

        return {"include_images": True, "image_queries": image_queries[:3]}

    def search_images(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Searches for images using an optional configured image search provider."""
        if self.bing_key and self.bing_endpoint:
            return self._search_bing_images(query, max_results)
        if self.unsplash_key:
            return self._search_unsplash(query, max_results)
        return []

    def _search_bing_images(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_key
            }
            params = {
                "q": query,
                "count": max_results,
                "safeSearch": "Moderate"
            }
            response = requests.get(self.bing_endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("value", [])[:max_results]:
                results.append({
                    "title": item.get("name", "Image"),
                    "image_url": item.get("contentUrl"),
                    "thumbnail_url": item.get("thumbnailUrl"),
                    "source_page": item.get("hostPageUrl"),
                    "provider": item.get("provider", [{}])[0].get("name", "Unknown")
                })
            return results
        except Exception:
            return []

    def _search_unsplash(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
            params = {"query": query, "per_page": max_results}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("results", [])[:max_results]:
                results.append({
                    "title": item.get("alt_description") or item.get("description") or "Image",
                    "image_url": item.get("urls", {}).get("regular"),
                    "thumbnail_url": item.get("urls", {}).get("thumb"),
                    "source_page": item.get("links", {}).get("html"),
                    "provider": "Unsplash"
                })
            return results
        except Exception:
            return []
