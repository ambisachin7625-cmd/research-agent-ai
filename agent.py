"""
Agent Orchestrator for Web Backend.

Orchestrates the LLM Planner, Search, Scraper, Memory, Reflection Agent, Visual Agent,
and Writer. Supports new research sessions, continuation mode, question editing,
and export-ready report payload generation.
"""

import re
import uuid
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from config import Config
from planner import LLMPlanner
from search import SearchClient
from scraper import fetch_text, get_domain_score, get_source_quality_label
from memory import MemoryStore
from writer import ReportWriter
from reflection import ReflectionAgent
from visual import VisualAgent

SESSION_STORE: Dict[str, Any] = {}

class ResearchSession:
    def __init__(self, question: str):
        self.session_id = str(uuid.uuid4())
        self.original_question = question
        self.current_question = question
        self.memory = MemoryStore()
        self.sources = set()
        self.source_details: List[Dict[str, Any]] = []
        self.source_url_to_id: Dict[str, str] = {}
        self.searched_queries = set()
        self.iteration_history: List[Dict[str, Any]] = []
        self.follow_up_suggestions: List[str] = []
        self.report_payload: Dict[str, Any] = {}
        self.image_results: List[Dict[str, Any]] = []
        self.memory_snippets: List[Dict[str, Any]] = []

    def add_source(self, url: str, title: str, snippet: str, query: str, score: int) -> bool:
        if url in self.sources:
            return False

        self.sources.add(url)
        src_id = f"src-{len(self.sources)}"
        self.source_url_to_id[url] = src_id
        self.source_details.append({
            "id": src_id,
            "url": url,
            "title": title,
            "snippet": snippet,
            "publication_date": "",
            "score": score,
            "quality": get_source_quality_label(score),
            "citation_ids": []
        })
        self.searched_queries.add(query.strip().lower())
        return True

    def add_query(self, query: str) -> None:
        normalized = query.strip().lower()
        if normalized:
            self.searched_queries.add(normalized)

    def has_query(self, query: str) -> bool:
        return query.strip().lower() in self.searched_queries

    def add_iteration_entry(self, entry: Dict[str, Any]) -> None:
        self.iteration_history.append(entry)

    def update_memory_snippets(self, query: str, n_results: int = 6) -> None:
        self.memory_snippets = self.memory.search(query, n_results=n_results)


def _normalize_query(query: str) -> str:
    return query.strip()


def _build_graph(session: ResearchSession, final_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    query_id_map: Dict[str, str] = {}
    query_nodes: List[Dict[str, Any]] = []

    for iteration_entry in session.iteration_history:
        for query in iteration_entry["queries"]:
            if query not in query_id_map:
                query_id = f"query-{len(query_id_map) + 1}"
                query_id_map[query] = query_id
                query_nodes.append({
                    "id": query_id,
                    "text": query,
                    "iteration": iteration_entry["iteration"]
                })

    graph_facts: List[Dict[str, Any]] = []
    graph_edges: List[Dict[str, Any]] = []
    citation_lookup = {src["url"]: src["citation_ids"] for src in session.source_details}

    for i, fact in enumerate(final_facts, 1):
        url = fact.get("url")
        src_id = session.source_url_to_id.get(url, "unknown")
        query_text = fact.get("source_query", "Unknown")
        query_id = query_id_map.get(query_text)
        fact_id = f"fact-{i}"
        citation_id = citation_lookup.get(url, ["[Unknown]"])[0] if url else "[Unknown]"

        graph_facts.append({
            "id": fact_id,
            "text": fact["text"],
            "url": url,
            "source_id": src_id,
            "query": query_text,
            "query_id": query_id,
            "citation_id": citation_id
        })

        if src_id != "unknown":
            graph_edges.append({"from": src_id, "to": fact_id, "label": "supports"})
        if query_id:
            graph_edges.append({"from": query_id, "to": src_id, "label": "searched"})

    report_node = {"id": "report", "text": "Final Research Report"}
    for fact_node in graph_facts:
        graph_edges.append({"from": fact_node["id"], "to": report_node["id"], "label": "cited in"})

    for query_node in query_nodes:
        graph_edges.append({"from": "question", "to": query_node["id"], "label": "generated"})

    return {
        "question": {"id": "question", "text": session.current_question},
        "queries": query_nodes,
        "sources": session.source_details,
        "facts": graph_facts,
        "report": report_node,
        "edges": graph_edges
    }


def _add_citation_ids_to_sources(session: ResearchSession, citation_map: Dict[str, str]) -> None:
    citation_ids_by_url: Dict[str, List[str]] = {}
    for cid, url in citation_map.items():
        citation_ids_by_url.setdefault(url, []).append(cid)

    for source in session.source_details:
        source["citation_ids"] = citation_ids_by_url.get(source["url"], [])


def _build_result(session: ResearchSession, logs: List[str]) -> Dict[str, Any]:
    final_facts = session.memory.search(session.current_question, n_results=20)
    session.update_memory_snippets(session.current_question)

    report_payload = session.report_payload
    citation_map = report_payload.get("citation_map", {})
    _add_citation_ids_to_sources(session, citation_map)

    return {
        "session_id": session.session_id,
        "question": session.current_question,
        "original_question": session.original_question,
        "log": logs,
        "sources": [source["url"] for source in session.source_details],
        "source_details": session.source_details,
        "facts": _build_graph(session, final_facts)["facts"],
        "iterations": len(session.iteration_history),
        "iteration_history": session.iteration_history,
        "graph_data": _build_graph(session, final_facts),
        "facts_count": len(final_facts),
        "sources_count": len(session.sources),
        "report": report_payload.get("report", ""),
        "highlights": report_payload.get("highlights", []),
        "important_facts": report_payload.get("important_facts", []),
        "citation_map": citation_map,
        "citations": report_payload.get("references", []),
        "follow_up_suggestions": session.follow_up_suggestions,
        "images": session.image_results,
        "memory_snippets": session.memory_snippets
    }


def _perform_search_iteration(
    session: ResearchSession,
    current_queries: List[str],
    planner: LLMPlanner,
    search_client: SearchClient,
    reflector: ReflectionAgent,
    visual_agent: VisualAgent,
    logs: List[str],
    max_iterations: int = 5
) -> None:
    iteration = len(session.iteration_history) + 1

    while iteration <= max_iterations:
        logs.append(f"\n--- [Iteration {iteration}] Started ---")
        logs.append(f"[+] Running {len(current_queries)} search queries.")

        iteration_entry = {
            "iteration": iteration,
            "queries": current_queries.copy(),
            "facts_extracted": 0,
            "confidence": 0,
            "sufficient": False,
            "missing_authoritative": False,
            "conflicting": False,
            "follow_up_queries": []
        }

        for q in current_queries:
            query_text = _normalize_query(q)
            if not query_text or session.has_query(query_text):
                logs.append(f"  Skipping repeated query: {q}")
                continue

            logs.append(f"-> Searching: {q}")
            session.add_query(query_text)
            results = search_client.search(q, max_results=Config.MAX_SEARCH_RESULTS)

            if not results:
                logs.append("  No results found.")
                continue

            top_results = results[:Config.MAX_SCRAPE_PER_QUERY]
            scrape_jobs = []
            for r in top_results:
                url = r["url"]
                if url in session.sources:
                    logs.append(f"  Already stored source: {url}")
                    continue
                scrape_jobs.append((r, q))

            def _scrape_one(item):
                r_item, query = item
                url = r_item["url"]
                page_text = fetch_text(url)
                return r_item, query, url, page_text

            if scrape_jobs:
                with ThreadPoolExecutor(max_workers=min(4, len(scrape_jobs))) as pool:
                    futures = [pool.submit(_scrape_one, job) for job in scrape_jobs]
                    for future in as_completed(futures):
                        r, query, url, page_text = future.result()
                        if not page_text:
                            logs.append(f"  [-] Failed to scrape: {url}")
                            continue

                        logs.append(f"  [+] Scraped: {url}")
                        score = get_domain_score(url)
                        added = session.add_source(
                            url=url,
                            title=r.get("title", "Source"),
                            snippet=r.get("snippet", ""),
                            query=query,
                            score=score
                        )
                        if added:
                            session.memory.add(text=page_text, url=url, query=query, score=score)
                            logs.append(f"  [+] Saved {len(page_text)} chars (Score: {score}/10).")

        logs.append("[*] Retrieving facts for reflection...")
        current_facts = session.memory.search(session.current_question, n_results=15)
        iteration_entry["facts_extracted"] = len(current_facts)

        if not current_facts:
            logs.append("[!] No facts found yet. Forcing another iteration.")
            iteration_entry["follow_up_queries"] = [f"Basic information about {session.current_question}"]
            session.add_iteration_entry(iteration_entry)
            current_queries = [f"Basic information about {session.current_question}"]
            iteration += 1
            continue

        logs.append("[*] Reflection Agent analyzing gathered facts...")
        eval_result = reflector.evaluate(session.current_question, current_facts)

        iteration_entry.update({
            "confidence": eval_result.get("confidence", 0),
            "sufficient": eval_result.get("sufficient", False),
            "missing_authoritative": eval_result.get("missing_authoritative", False),
            "conflicting": eval_result.get("conflicting", False),
            "follow_up_queries": eval_result.get("follow_up_queries", [])
        })
        session.follow_up_suggestions = eval_result.get("follow_up_queries", [])
        session.add_iteration_entry(iteration_entry)

        logs.append(f"  -> Confidence: {eval_result.get('confidence', 0)}% | Sufficient: {eval_result.get('sufficient', False)}")
        if eval_result.get("missing_authoritative"):
            logs.append("  -> Authoritative source warning detected.")
        if eval_result.get("conflicting"):
            logs.append("  -> Conflicting facts detected.")

        if eval_result.get("confidence", 0) >= Config.CONFIDENCE_THRESHOLD and eval_result.get("sufficient", False):
            logs.append("[+] Confidence threshold reached! Proceeding to report.")
            break

        if iteration >= max_iterations:
            logs.append("[!] Max iterations reached. Proceeding to report.")
            break

        logs.append("[-] Information insufficient. Generating follow-up queries...")
        current_queries = eval_result.get("follow_up_queries", [f"More details about {session.current_question}"])
        iteration += 1

    if session.follow_up_suggestions:
        logs.append(f"[*] Follow-up suggestions: {session.follow_up_suggestions}")

    if not Config.SKIP_IMAGES:
        image_decision = visual_agent.should_use_images(session.current_question, current_facts)
        if image_decision.get("include_images"):
            session.image_results = []
            for image_query in image_decision.get("image_queries", [])[:2]:
                images = visual_agent.search_images(image_query, max_results=2)
                for image in images:
                    if image.get("image_url"):
                        session.image_results.append(image)
                if len(session.image_results) >= 3:
                    break
            session.image_results = session.image_results[:3]


def _prepare_report(session: ResearchSession) -> None:
    final_facts = session.memory.search(session.current_question, n_results=20)
    report_writer = ReportWriter()
    session.report_payload = report_writer.write_report(session.current_question, final_facts)


def _save_session(session: ResearchSession) -> None:
    SESSION_STORE[session.session_id] = session


def get_session(session_id: str) -> Any:
    return SESSION_STORE.get(session_id)


def _friendly_error(exc: Exception) -> str:
    """Turn low-level API errors into actionable messages for the UI."""
    import ast

    msg = str(exc)
    lower = msg.lower()

    # If the exception contains a raw error dict string from the OpenAI client,
    # try to extract the inner message/type for a clearer user-facing message.
    try:
        parsed = None
        if msg.strip().startswith("{"):
            try:
                parsed = ast.literal_eval(msg)
            except Exception:
                parsed = None

        if parsed and isinstance(parsed, dict):
            err = parsed.get("error") or {}
            if isinstance(err, dict):
                e_msg = err.get("message")
                e_type = err.get("type")
                if e_type and "insufficient" in str(e_type).lower():
                    return (
                        "OpenAI quota exceeded. Please check your plan and billing at "
                        "https://platform.openai.com/account/usage and update your subscription."
                    )
                if e_msg:
                    msg = e_msg
                    lower = msg.lower()
    except Exception:
        # Fall back to the original message if parsing fails
        pass

    # Common, user-actionable mappings
    if "insufficient_quota" in lower or "quota exceeded" in lower or "429" in msg or "rate limit" in lower:
        return (
            "OpenAI quota or rate limit reached. Check your billing/usage on https://platform.openai.com/ "
            "or upgrade your plan. If you expect this to be transient, try again later."
        )

    if "invalid_api_key" in lower or "invalid api key" in lower or "401" in msg:
        provider = "Groq" if Config.OPENAI_BASE_URL and "groq" in Config.OPENAI_BASE_URL else "LLM"
        return (
            f"The {provider} API key is invalid or expired. "
            f"Update OPENAI_API_KEY in your Render environment variables "
            f"({provider} key from console.groq.com if using Groq)."
        )

    if "tavily" in lower:
        return "Tavily search failed. Check that TAVILY_API_KEY is set correctly in Render."

    if "missing configuration" in lower:
        return msg

    return f"Research failed: {msg}"


def _error_result(
    session: ResearchSession,
    question: str,
    logs: List[str],
    exc: Exception,
    *,
    preserve_session: bool = False,
) -> Dict[str, Any]:
    error_message = _friendly_error(exc)
    logs.append(f"[!] Critical Error: {error_message}")
    logs.append(traceback.format_exc())

    base = {
        "session_id": session.session_id,
        "question": question,
        "error": True,
        "error_message": error_message,
        "log": logs,
        "sources": [source["url"] for source in session.source_details] if preserve_session else [],
        "source_details": session.source_details if preserve_session else [],
        "facts": [],
        "iteration_history": session.iteration_history if preserve_session else [],
        "graph_data": {
            "question": {"id": "question", "text": question},
            "queries": [],
            "sources": session.source_details if preserve_session else [],
            "facts": [],
            "report": {"id": "report", "text": "Final Research Report"},
            "edges": []
        },
        "iterations": len(session.iteration_history) if preserve_session else 0,
        "facts_count": len(session.memory_snippets) if preserve_session else 0,
        "sources_count": len(session.sources) if preserve_session else 0,
        "report": error_message if not preserve_session else session.report_payload.get("report", error_message),
        "highlights": session.report_payload.get("highlights", []) if preserve_session else [],
        "important_facts": session.report_payload.get("important_facts", []) if preserve_session else [],
        "citation_map": session.report_payload.get("citation_map", {}) if preserve_session else {},
        "citations": session.report_payload.get("references", []) if preserve_session else [],
        "follow_up_suggestions": session.follow_up_suggestions if preserve_session else [],
        "images": session.image_results if preserve_session else [],
        "memory_snippets": session.memory_snippets if preserve_session else [],
    }
    return base


def start_research(question: str) -> Dict[str, Any]:
    logs: List[str] = []
    session = ResearchSession(question)
    _save_session(session)

    try:
        planner = LLMPlanner()
        search_client = SearchClient()
        reflector = ReflectionAgent()
        visual_agent = VisualAgent()

        logs.append("[*] Initialized components.")
        logs.append(f"[*] Original Question: '{question}'")

        initial_queries = planner.generate_queries(question)
        _perform_search_iteration(session, initial_queries, planner, search_client, reflector, visual_agent, logs, max_iterations=Config.MAX_ITERATIONS)
        _prepare_report(session)

        return _build_result(session, logs)
    except Exception as e:
        return _error_result(session, question, logs, e)


def continue_research(session_id: str, follow_up_prompt: str = None, edited_question: str = None) -> Dict[str, Any]:
    logs: List[str] = []
    session = get_session(session_id)

    if not session:
        return start_research(edited_question or follow_up_prompt or "")

    try:
        planner = LLMPlanner()
        search_client = SearchClient()
        reflector = ReflectionAgent()
        visual_agent = VisualAgent()

        logs.append("[*] Resuming research from existing session.")
        logs.append(f"[*] Current Question: '{session.current_question}'")

        if edited_question:
            session.current_question = edited_question
            logs.append(f"[*] Edited research question: '{edited_question}'")
            current_queries = planner.generate_queries(edited_question)
        elif follow_up_prompt:
            follow_up_context = f"{session.current_question}. Follow-up: {follow_up_prompt}"
            logs.append(f"[*] Follow-up prompt: '{follow_up_prompt}'")
            current_queries = planner.generate_queries(follow_up_context)
        else:
            current_queries = session.follow_up_suggestions or [f"More details about {session.current_question}"]

        _perform_search_iteration(session, current_queries, planner, search_client, reflector, visual_agent, logs, max_iterations=max(2, Config.MAX_ITERATIONS - 1))
        _prepare_report(session)

        return _build_result(session, logs)
    except Exception as e:
        return _error_result(session, session.current_question, logs, e, preserve_session=True)


def run_research(question: str) -> Dict[str, Any]:
    """Public API: Start a new research session."""
    return start_research(question)
