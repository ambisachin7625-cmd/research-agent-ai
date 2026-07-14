#!/usr/bin/env python
"""Complete test of localhost API"""
import requests
import sys

print('TESTING LOCALHOST API')
print('='*70)

# Test 1: Health
print('\n1. Testing Health Endpoint...')
try:
    r = requests.get('http://127.0.0.1:5000/health', timeout=5)
    print(f'   Status Code: {r.status_code}')
    if r.status_code == 200:
        print(f'   Response: {r.json()}')
        print('   ✓ HEALTH CHECK - OK')
    else:
        print(f'   ✗ ERROR: {r.text}')
except Exception as e:
    print(f'   ✗ FAILED: {e}')
    sys.exit(1)

# Test 2: API without validation (FAST)
print('\n2. Testing Links API (NO VALIDATION - FAST)...')
try:
    print('   Sending request... (please wait ~5-7 seconds)')
    r = requests.get('http://127.0.0.1:5000/api/links?q=github&max=3&validate=false', timeout=20)
    print(f'   Status Code: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        count = data.get('count', 0)
        print(f'   Found: {count} links')
        if data.get('links'):
            for i, link in enumerate(data['links'][:2], 1):
                print(f'   {i}. {link["title"][:50]}...')
                print(f'      {link["url"]}')
        print('   ✓ LINKS API - OK')
    else:
        print(f'   ✗ ERROR Status {r.status_code}')
        print(f'   Response: {r.text[:200]}')
except requests.exceptions.Timeout:
    print('   ✗ TIMEOUT - Request took too long')
except Exception as e:
    print(f'   ✗ FAILED: {e}')

# Test 3: API with validation (SLOW but thorough)
print('\n3. Testing Links API (WITH VALIDATION - SLOW)...')
try:
    print('   Sending request... (please wait ~15-20 seconds)')
    r = requests.get('http://127.0.0.1:5000/api/links?q=test&max=2&validate=true', timeout=30)
    print(f'   Status Code: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        count = data.get('count', 0)
        print(f'   Found: {count} links')
        if data.get('links'):
            for i, link in enumerate(data['links'][:1], 1):
                live = link.get('live', None)
                live_status = 'LIVE' if live else 'OFFLINE' if live is False else 'UNKNOWN'
                print(f'   {i}. {link["title"][:50]}...')
                print(f'      {link["url"]}')
                print(f'      Status: {live_status}')
        print('   ✓ VALIDATION API - OK')
    else:
        print(f'   ✗ ERROR Status {r.status_code}')
except requests.exceptions.Timeout:
    print('   ✗ TIMEOUT - Request took too long')
except Exception as e:
    print(f'   ✗ FAILED: {e}')

print('\n' + '='*70)
print('TESTING COMPLETE')
print('='*70)
print('\nWORKING LOCALHOST URLS:')
print('  ✓ http://127.0.0.1:5000/health')
print('  ✓ http://127.0.0.1:5000/api/links?q=github&validate=false')
print('  ✓ http://127.0.0.1:5000/api/links?q=python&validate=false')
print('='*70)
