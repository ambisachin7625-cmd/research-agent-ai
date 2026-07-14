"""
Report Writer module for the Research Agent.

This module builds a polished, citation-aware markdown report from extracted facts,
then extracts key highlights and important facts for the dashboard.
"""

import json
from openai import OpenAI
from config import Config
from typing import List, Dict, Any

class ReportWriter:
    """Report Writer that uses an LLM to synthesize a final research report."""

    def __init__(self):
        Config.validate()
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL
        )
        self.model = Config.OPENAI_MODEL

    def _clean_json_response(self, response_text: str) -> str:
        """Removes markdown fences around JSON output."""
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        return cleaned

    def _extract_json_array(self, content: str, instructions: str) -> List[str]:
        """Extracts a JSON array of strings from the model given a content block."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a structured data extraction assistant."},
                    {
                        "role": "user",
                        "content": (
                            f"{instructions}\n\nContent:\n{content}\n\n"
                            "Return ONLY a JSON array of strings."
                        )
                    }
                ],
                response_format={"type": "json_array"},
                temperature=0.2
            )
            raw = response.choices[0].message.content
            parsed = json.loads(self._clean_json_response(raw))
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return []

    def write_report(self, question: str, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesizes a markdown report and returns structured report metadata.
        """
        if not facts:
            return {
                "report": "No relevant facts could be found to answer your question.",
                "highlights": [],
                "important_facts": [],
                "citation_map": {},
                "citation_urls": {},
                "references": []
            }

        citation_map: Dict[str, str] = {}
        citation_urls: Dict[str, str] = {}
        citation_counter = 1
        facts_text = ""

        for i, fact in enumerate(facts, 1):
            url = fact.get("url") or "Unknown"
            score = int(fact.get("score", 4))
            if url not in citation_urls.values():
                citation_id = f"[{citation_counter}]"
                citation_map[citation_id] = url
                citation_urls[citation_id] = url
                citation_counter += 1

            citation_id = next((cid for cid, src in citation_map.items() if src == url), "[Unknown]")
            facts_text += (
                f"Fact {i}:\n"
                f"{fact['text']}\n"
                f"Source Query: {fact.get('source_query', 'Unknown')}\n"
                f"Citation: {citation_id}\n"
                f"Trust Score: {score}/10\n\n"
            )

        reference_definitions = "\n\n## References\n"
        for citation_id, url in citation_map.items():
            reference_definitions += f"{citation_id}: {url}\n"

        system_prompt = (
            "You are an expert research analyst. Write a polished markdown research report using ONLY the facts provided.\n"
            "Your report MUST include these sections in order:\n"
            "- Executive Summary\n"
            "- Key Highlights\n"
            "- Important Facts\n"
            "- Detailed Analysis\n"
            "- Conclusion\n\n"
            "Use inline citations for every claim using the provided citation IDs.\n"
            "Do not invent claims beyond the facts supplied.\n"
            "Do not include the References section; it will be appended automatically.\n"
        )

        user_content = (
            f"Research Question: {question}\n\n"
            f"Facts:\n{facts_text}\n"
            "Create the final report only from the facts above."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.35
            )
            report_text = response.choices[0].message.content.strip()
        except Exception as e:
            report_text = f"An error occurred while writing the report: {str(e)}"

        report_with_references = report_text + reference_definitions
        highlights = self._extract_json_array(
            report_text,
            "Extract 3 to 5 concise key highlights from the report as a JSON array of brief statements."
        )
        important_facts = self._extract_json_array(
            report_text,
            "Extract the 3 most important facts from the report as a JSON array of short statements."
        )

        return {
            "report": report_with_references,
            "highlights": highlights,
            "important_facts": important_facts,
            "citation_map": citation_map,
            "citation_urls": citation_urls,
            "references": [
                {"id": cid, "url": url} for cid, url in citation_map.items()
            ]
        }
