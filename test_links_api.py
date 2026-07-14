#!/usr/bin/env python
"""
Quick test script for the ResearchAI Links API.

Usage:
    python test_links_api.py [--url http://localhost:5000] [--query "your topic"]

Example:
    python test_links_api.py --query "machine learning projects"
    python test_links_api.py --url https://researchai.onrender.com --query "react"
"""

import sys
import argparse
import json
import requests
from datetime import datetime

DEFAULT_URL = "http://localhost:5000"
DEFAULT_QUERY = "machine learning"


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_health(base_url):
    """Test the health endpoint."""
    print_header("Testing Health Endpoint")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✓ Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_links_api(base_url, query, max_results=5, validate=False):
    """Test the links API endpoint."""
    print_header(f"Fetching Live Links: '{query}'")
    print(f"Max results: {max_results}")
    print(f"URL validation: {'Enabled' if validate else 'Disabled'}")
    
    try:
        response = requests.get(
            f"{base_url}/api/links",
            params={
                "q": query,
                "max": max_results,
                "validate": "true" if validate else "false"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return False
        
        data = response.json()
        
        if "error" in data:
            print(f"✗ API Error: {data['error']}")
            return False
        
        print(f"\n✓ Found {data['count']} link(s)\n")
        
        for i, link in enumerate(data.get("links", []), 1):
            print(f"{i}. {link.get('title', 'No Title')}")
            print(f"   URL: {link.get('url', 'N/A')}")
            print(f"   Domain: {link.get('domain', 'N/A')}")
            print(f"   Quality: {link.get('quality', 'N/A')} (Score: {link.get('score', 0)}/100)")
            
            if validate and 'live' in link:
                live_status = "✓ LIVE" if link['live'] else "✗ OFFLINE"
                print(f"   Status: {live_status}")
            
            snippet = link.get('snippet', '')
            if snippet:
                snippet_preview = snippet[:80] + "..." if len(snippet) > 80 else snippet
                print(f"   Snippet: {snippet_preview}")
            print()
        
        return True
    
    except requests.exceptions.Timeout:
        print("✗ Error: Request timeout (server took too long to respond)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Error: Could not connect to {base_url}")
        print(f"  Make sure the server is running: python app.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_full_test_suite(base_url):
    """Run comprehensive tests."""
    print_header("ResearchAI Links API Test Suite")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target URL: {base_url}")
    
    results = {}
    
    # Test 1: Health check
    print("\n[1/4] Testing server health...")
    results['health'] = test_health(base_url)
    
    if not results['health']:
        print("\n✗ Server is not responding. Cannot continue tests.")
        return results
    
    # Test 2: Basic link fetch (no validation)
    print("\n[2/4] Testing link extraction (no validation)...")
    results['fetch_no_validation'] = test_links_api(
        base_url,
        "python web frameworks",
        max_results=3,
        validate=False
    )
    
    # Test 3: Link fetch with validation
    print("\n[3/4] Testing link extraction (with validation)...")
    results['fetch_with_validation'] = test_links_api(
        base_url,
        "github open source",
        max_results=3,
        validate=True
    )
    
    # Test 4: Edge case - empty query
    print("\n[4/4] Testing error handling...")
    try:
        response = requests.get(f"{base_url}/api/links", params={"q": ""}, timeout=5)
        if response.status_code == 400:
            print("✓ Empty query correctly rejected")
            results['error_handling'] = True
        else:
            print(f"✗ Expected 400, got {response.status_code}")
            results['error_handling'] = False
    except Exception as e:
        print(f"✗ Error: {e}")
        results['error_handling'] = False
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test ResearchAI Links API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_links_api.py
  python test_links_api.py --query "machine learning"
  python test_links_api.py --url https://researchai.onrender.com --query "react"
        """
    )
    
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Base URL of the API (default: {DEFAULT_URL})"
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help=f"Search query (default: '{DEFAULT_QUERY}')"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Enable URL validation (check if links are live)"
    )
    parser.add_argument(
        "--full-test",
        action="store_true",
        help="Run complete test suite"
    )
    
    args = parser.parse_args()
    
    # Normalize URL
    base_url = args.url.rstrip("/")
    
    if args.full_test:
        run_full_test_suite(base_url)
    else:
        # Single test
        if test_health(base_url):
            test_links_api(base_url, args.query, args.max, args.validate)
        else:
            print("\n✗ Cannot proceed - server is not accessible")
            sys.exit(1)


if __name__ == "__main__":
    main()
