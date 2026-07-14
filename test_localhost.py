#!/usr/bin/env python
"""Quick test for links API"""
import requests
import json

print("=" * 70)
print("  LOCALHOST TESTING - LINKS API")
print("=" * 70)

# Test 1: Without validation (fast)
print("\n1. Testing WITHOUT validation (FAST - ~5-10 seconds):")
print("-" * 70)
try:
    r = requests.get('http://127.0.0.1:5000/api/links?q=github&max=3&validate=false', timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f"✓ SUCCESS! Found {data.get('count')} links\n")
        for i, link in enumerate(data.get('links', [])[:2], 1):
            print(f"  {i}. {link['title'][:55]}")
            print(f"     {link['url']}\n")
    else:
        print(f"✗ ERROR: Status {r.status_code}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2: With validation (slow)
print("\n2. Testing WITH validation (SLOW - ~15-30 seconds):")
print("-" * 70)
try:
    r = requests.get('http://127.0.0.1:5000/api/links?q=test&max=2&validate=true', timeout=40)
    if r.status_code == 200:
        data = r.json()
        print(f"✓ SUCCESS! Found {data.get('count')} links\n")
        for i, link in enumerate(data.get('links', [])[:1], 1):
            live_status = "✓ LIVE" if link.get('live') else "✗ OFFLINE"
            print(f"  {i}. {link['title'][:55]}")
            print(f"     {link['url']}")
            print(f"     Status: {live_status}\n")
    else:
        print(f"✗ ERROR: Status {r.status_code}")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "=" * 70)
print("  IMPORTANT: API IS SLOW (10-30 seconds)")
print("  Use validate=false for faster results!")
print("=" * 70)
