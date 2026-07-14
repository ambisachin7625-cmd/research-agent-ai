"""
Configuration module for the Research Agent.

This module is responsible for loading environment variables (e.g., API keys, 
model parameters) from a `.env` file and providing a centralized configuration 
interface for the rest of the application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists.
# This allows local development configuration without committing secrets.
load_dotenv()

class Config:
    """Centralized configuration class for the agent."""
    
    # The API key required to authenticate with OpenAI.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # The name of the LLM model to use (defaults to gpt-4o-mini).
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Optional base URL for OpenAI-compatible endpoints (e.g. OpenRouter, Local LLMs, etc.)
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

    # The API key required to authenticate with Tavily.
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # Optional image search configuration.
    BING_IMAGE_SEARCH_KEY = os.getenv("BING_IMAGE_SEARCH_KEY")
    BING_IMAGE_SEARCH_ENDPOINT = os.getenv("BING_IMAGE_SEARCH_ENDPOINT")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

    # Flask session secret (set in production)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # SQLite database path (use /tmp on Render for ephemeral writable storage)
    DATABASE_PATH = os.getenv("DATABASE_PATH", "researchai.db")

    # Faster research: fewer iterations, less scraping, skip images
    FAST_RESEARCH = os.getenv("FAST_RESEARCH", "true").lower() in ("1", "true", "yes")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2" if FAST_RESEARCH else "5"))
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "3" if FAST_RESEARCH else "5"))
    MAX_SCRAPE_PER_QUERY = int(os.getenv("MAX_SCRAPE_PER_QUERY", "1" if FAST_RESEARCH else "2"))
    CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD", "70" if FAST_RESEARCH else "80"))
    SKIP_IMAGES = os.getenv("SKIP_IMAGES", "true" if FAST_RESEARCH else "false").lower() in ("1", "true", "yes")

    @classmethod
    def validate_search(cls):
        """Validate only Tavily credentials (enough for live link fetching)."""
        if not cls.TAVILY_API_KEY or cls.TAVILY_API_KEY.startswith("your-tavily-key"):
            print("Error: TAVILY_API_KEY is not set or is still the placeholder value.", file=sys.stderr)
            print("Please create a `.env` file in the root directory (copying `.env.example`) and add your Tavily API key.", file=sys.stderr)
            raise ValueError("Missing configuration variables: TAVILY_API_KEY")

    @classmethod
    def validate(cls):
        """
        Validates the configuration to ensure the application has the necessary keys.
        Raises ValueError if required settings are missing.
        """
        missing_vars = []
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY.startswith("your-api-key"):
            print("Error: OPENAI_API_KEY is not set or is still the placeholder value.", file=sys.stderr)
            missing_vars.append("OPENAI_API_KEY")

        if not cls.TAVILY_API_KEY or cls.TAVILY_API_KEY.startswith("your-tavily-key"):
            print("Error: TAVILY_API_KEY is not set or is still the placeholder value.", file=sys.stderr)
            missing_vars.append("TAVILY_API_KEY")

        if missing_vars:
            print("Please create a `.env` file in the root directory (copying `.env.example`) and add your actual API keys.", file=sys.stderr)
            raise ValueError(f"Missing configuration variables: {', '.join(missing_vars)}")
