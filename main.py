"""
Main entry point for the Research Agent.

This module provides the Command Line Interface (CLI) for interacting with the 
LLM Planner, SearchClient, and Scraper. It orchestrates the configuration 
validation, query generation, web search, and page text extraction loop.
"""

import sys
from config import Config
from planner import LLMPlanner
from search import SearchClient
from scraper import fetch_text  # fetches and cleans full page text from a URL
from memory import MemoryStore  # provides vector storage and semantic search

def run_agent():
    """
    Validates configuration, prompts the user for a research question, 
    passes it to the LLMPlanner, executes web searches for generated queries, 
    and displays the results.
    """
    print("=" * 60)
    print("           Welcome to Research Agent v4 (Vector Memory)     ")
    print("=" * 60)

    # Validate that environmental configuration is set up correctly
    try:
        Config.validate()
    except ValueError:
        # Config.validate already prints help text to stderr.
        print("\nExiting due to missing configuration.")
        sys.exit(1)

    # Instantiate the planner and search client.
    try:
        print("[*] Initializing LLM Planner, Search Client, and Memory...")
        planner = LLMPlanner()
        search_client = SearchClient()
        memory = MemoryStore()
        print("[+] Components ready.\n")
    except Exception as e:
        print(f"[-] Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

    while True:
        try:
            # Prompt the user for their research question
            question = input("Enter your research question (or 'exit' to quit):\n> ").strip()
            
            if not question:
                continue
                
            if question.lower() == 'exit':
                print("Goodbye!")
                break

            print("\n[*] Analyzing question and generating search queries...")
            
            # Clear memory from previous questions
            memory.clear()

            # Generate the queries using the LLM Planner
            queries = planner.generate_queries(question)
            
            print(f"[+] Generated {len(queries)} research queries:")
            for i, q in enumerate(queries, 1):
                print(f"  {i}. {q}")
            
            print("\n[*] Executing web searches...")
            
            # Execute search for each query and display results grouped by query
            for q in queries:
                print(f"\nQuery:\n{q}")
                print("\nResults:")
                
                try:
                    results = search_client.search(q, max_results=5)
                    if not results:
                        print("  No results found.")
                    else:
                        # --- Display all search results (title, url, snippet) ---
                        for i, r in enumerate(results, 1):
                            print(f"\n{i}. {r['title']}")
                            print(f"   {r['url']}")
                            print(f"   {r['snippet']}")

                        # --- Scrape the top 2 URLs for full page content ---
                        # We only scrape the top 2 to keep things fast.
                        # fetch_text() returns empty string "" silently on any error.
                        print("\n[*] Scraping top 2 URLs for full page content...")
                        top_2_results = results[:2]

                        for i, r in enumerate(top_2_results, 1):
                            url = r["url"]
                            print(f"\n  Scraping [{i}]: {url}")
                            page_text = fetch_text(url)

                            if page_text:
                                # Add the scraped content to our vector memory
                                print(f"  [+] Saving scraped content to memory...")
                                memory.add(text=page_text, url=url, query=q)

                                # Print only the first 500 characters as a preview
                                preview = page_text[:500]
                                print(f"  --- Scraped Content (first 500 chars) ---")
                                print(f"  {preview}")
                                print(f"  --- (total scraped: {len(page_text)} chars) ---")
                            else:
                                # fetch_text returned "" — page blocked, timed out, etc.
                                print("  [!] Could not scrape this page (blocked or timed out).")

                except Exception as search_err:
                    print(f"  [-] Search failed for this query: {search_err}", file=sys.stderr)
                
            print("\n" + "=" * 60)
            
            # --- Memory Search Test ---
            print("\n[*] Searching memory for most relevant facts...")
            retrieved_facts = memory.search(question, n_results=3)
            
            if retrieved_facts:
                for idx, fact in enumerate(retrieved_facts, 1):
                    print(f"\nFact {idx}:")
                    print(f"URL: {fact['url']}")
                    print(f"Excerpt: {fact['text']}")
            else:
                print("\n[-] No relevant facts found in memory.")

            print("\n" + "=" * 60 + "\n")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nGoodbye!")
            break
        except Exception as e:
            # General catch-all for errors to prevent CLI crash
            print(f"\n[-] An error occurred: {e}", file=sys.stderr)
            print("-" * 60 + "\n")

if __name__ == "__main__":
    run_agent()
