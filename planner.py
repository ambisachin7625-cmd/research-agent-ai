"""
LLM Planner implementation for the Research Agent.

This module handles communication with the OpenAI API (or other configured LLM) 
and parses the response into structured Python lists.
"""

import json
from openai import OpenAI
from config import Config
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

class LLMPlanner:
    """Planner class that utilizes an LLM to generate research queries."""

    def __init__(self):
        """Initializes the OpenAI client using settings from config.py."""
        # Config.validate() is called to ensure credentials exist before API calls
        Config.validate()
        
        # Initialize client. The base_url parameter is passed if configured.
        # This makes it easy to point to alternative backends like Ollama, LM Studio, etc.
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
        self.model = Config.OPENAI_MODEL

    def _clean_json_response(self, response_text: str) -> str:
        """
        Cleans LLM response text, handling potential markdown code block wrappers
        like ```json ... ``` or ``` ... ```.
        
        Args:
            response_text (str): The raw response string from the LLM.
            
        Returns:
            str: Cleaned JSON string.
        """
        cleaned = response_text.strip()
        
        # Handle markdown blocks if the LLM wrapped the JSON array in them
        if cleaned.startswith("```"):
            # Split by markdown fences and extract the block body
            lines = cleaned.splitlines()
            # If the first line is ```json or ```, skip it
            if lines[0].startswith("```"):
                lines = lines[1:]
            # If the last line is ```, skip it
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            
        return cleaned

    def generate_queries(self, question: str) -> list[str]:
        """
        Accepts a user research question, sends it to the LLM, parses the
        structured response, and returns a Python list of 3 queries.
        
        Args:
            question (str): The user's research question.
            
        Returns:
            list[str]: A list of exactly 3 search queries.
            
        Raises:
            Exception: For API, schema validation, or parsing failures.
        """
        # Format the user input using the template defined in prompts.py
        user_content = USER_PROMPT_TEMPLATE.format(question=question)

        try:
            # Call the OpenAI Chat Completion API.
            # We configure json_object response format to enforce structured output.
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                # If we're using OpenAI, we can enforce JSON response format
                response_format={"type": "json_object"},
                temperature=0.2  # Lower temperature for more focused, deterministic generation
            )
            
            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("Received empty response from the LLM.")
                
            # Clean the response in case there are any markdown artifacts
            cleaned_json = self._clean_json_response(raw_content)
            
            # Parse the clean JSON text into Python object
            parsed_data = json.loads(cleaned_json)
            
            # We expect a JSON list (Python list). Validate its type and size.
            if not isinstance(parsed_data, list):
                # Sometimes models wrap the list in a dict, e.g., {"queries": [...]}
                if isinstance(parsed_data, dict):
                    # Try to extract list from common keys
                    for key in ["queries", "search_queries", "results"]:
                        if key in parsed_data and isinstance(parsed_data[key], list):
                            parsed_data = parsed_data[key]
                            break
                
                # Re-validate
                if not isinstance(parsed_data, list):
                    raise ValueError(f"Expected a JSON list, but got {type(parsed_data)}: {parsed_data}")
            
            # Enforce exactly 3 queries (or handle variations if needed)
            # If size is not 3, we logs a warning but keep what we got or trim/pad it.
            # Let's enforce exactly 3 as per requirements, or slice it if longer.
            queries = [str(item).strip() for item in parsed_data]
            
            if len(queries) != 3:
                # Pad or slice to return exactly 3 queries
                if len(queries) > 3:
                    queries = queries[:3]
                else:
                    while len(queries) < 3:
                        queries.append(f"Additional context for: {question}")
            
            return queries

        except Exception as e:
            # Capture and raise/handle API or network level exceptions.
            # This provides a clean traceback or error details for downstream systems.
            raise RuntimeError(f"Failed to generate search queries: {str(e)}") from e
