"""
Reflection Agent module for the Research Agent.

This module evaluates gathered facts against the original question to determine
if we have enough information or if we need to run another search iteration.
"""

import json
from openai import OpenAI
from config import Config
from typing import List, Dict, Any

class ReflectionAgent:
    """Evaluates research progress and generates follow-up queries if needed."""

    def __init__(self):
        Config.validate()
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
        self.model = Config.OPENAI_MODEL

    def _clean_json_response(self, response_text: str) -> str:
        """Cleans markdown blocks from JSON responses."""
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return cleaned

    def evaluate(self, question: str, facts: List[Dict[str, Any]]) -> dict:
        """
        Evaluates the current facts against the question.
        Returns a dict: {
            "sufficient": bool,
            "conflicting": bool,
            "missing_authoritative": bool,
            "confidence": int,
            "follow_up_queries": list[str]
        }
        """
        if not facts:
            return {
                "sufficient": False,
                "conflicting": False,
                "missing_authoritative": True,
                "confidence": 0,
                "follow_up_queries": [f"Basic information about {question}"]
            }

        total_score = 0
        high_quality_facts = 0
        facts_text = ""
        for i, fact in enumerate(facts, 1):
            score = int(fact.get("score", 4))
            total_score += score
            if score >= 8:
                high_quality_facts += 1
            facts_text += (
                f"Fact {i} [Trust Score: {score}/10, Source Query: {fact.get('source_query', 'Unknown')}]:\n"
                f"{fact['text']}\n\n"
            )

        average_score = total_score / len(facts) if facts else 0
        authoritative_missing = high_quality_facts == 0

        system_prompt = (
            "You are a critical research evaluator. Analyze the provided facts against the original question.\n"
            "Assess the following:\n"
            "1. Is the information sufficient to write a comprehensive report?\n"
            "2. Are there conflicting facts that need clarification?\n"
            "3. Are we missing authoritative sources (high trust score >= 8)?\n"
            "4. What is your overall confidence (0-100) that the question is fully answered?\n\n"
            "If confidence < 80, information is insufficient, or authoritative sources are missing, provide 1 to 3 specific follow-up search queries to fill the gaps.\n"
            "If there are conflicting facts, note the conflict in the response.\n\n"
            "Output MUST be valid JSON in this exact format:\n"
            "{\n"
            '  "sufficient": boolean,\n'
            '  "conflicting": boolean,\n'
            '  "missing_authoritative": boolean,\n'
            '  "confidence": integer,\n'
            '  "follow_up_queries": ["query1", "query2"]\n'
            "}"
        )

        user_content = (
            f"Original Question: {question}\n\n"
            f"Gathered Facts: {len(facts)} items\n"
            f"Average source trust score: {average_score:.1f}/10\n"
            f"High quality sources present: {'Yes' if not authoritative_missing else 'No'}\n\n"
            f"Facts:\n{facts_text}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            raw_content = response.choices[0].message.content
            cleaned_json = self._clean_json_response(raw_content)
            parsed_data = json.loads(cleaned_json)
            
            follow_up_queries = list(parsed_data.get("follow_up_queries", []))
            if not follow_up_queries:
                follow_up_queries = [f"Deep dive into {question}"]

            return {
                "sufficient": bool(parsed_data.get("sufficient", False)),
                "conflicting": bool(parsed_data.get("conflicting", False)),
                "missing_authoritative": bool(parsed_data.get("missing_authoritative", authoritative_missing)),
                "confidence": int(parsed_data.get("confidence", 0)),
                "follow_up_queries": follow_up_queries
            }
            
        except Exception as e:
            print(f"Reflection Agent failed: {e}")
            return {
                "sufficient": False,
                "conflicting": False,
                "missing_authoritative": authoritative_missing,
                "confidence": int(min(max(average_score * 10, 40), 75)),
                "follow_up_queries": [f"Deep dive into {question}"]
            }
