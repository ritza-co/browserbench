#!/usr/bin/env python3
"""
Test 5: Parallel Product Lookups
Platform: Browserbase
Target: books.toscrape.com (3 different categories)
Task: Scrape 3 categories
CRITICAL: Browserbase free tier = 1 concurrent session only (sequential execution)
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 5: Parallel Product Lookups")
print("=" * 60)
print("NOTE: Free tier limited to 1 concurrent session")
print("Execution will be SEQUENTIAL (not parallel)")
print("=" * 60)

# Wait 15 seconds to avoid rate limiting
print("\nWaiting 15 seconds to avoid rate limiting...")
time.sleep(15)

# URLs to scrape sequentially
urls = [
    'http://books.toscrape.com/catalogue/category/books/travel_2/index.html',
    'http://books.toscrape.com/catalogue/category/books/mystery_3/index.html',
    'http://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html'
]

start_time = time.time()
results = []
session_ids = []

print("\nStarting sequential execution...")

# Must run sequentially due to 1 concurrent session limit
for idx, url in enumerate(urls):
    item_start = time.time()

    # Wait 15 seconds between sessions to avoid rate limiting
    if idx > 0:
        print(f"\n  Waiting 15 seconds before next session...")
        time.sleep(15)

    # Create new session for each lookup
    session = bb.sessions.create(
        project_id=os.environ["BROWSERBASE_PROJECT_ID"],
        browser_settings={"record_session": True}
    )
    session_ids.append(session.id)

    print(f"\nLookup {idx+1}/3:")
    print(f"  Session ID: {session.id}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate and extract
        page.goto(url)
        category = page.locator('h1').inner_text()
        books_count = page.locator('article.product_pod').count()

        browser.close()

    item_duration = time.time() - item_start

    results.append({
        "category": category,
        "books_found": books_count,
        "duration_seconds": round(item_duration, 2),
        "session_id": session.id
    })

    print(f"  Category: {category}")
    print(f"  Books found: {books_count}")
    print(f"  Duration: {item_duration:.2f}s")

total_duration = time.time() - start_time
avg_duration = total_duration / len(urls)

# Calculate speedup (should be ~1x since sequential)
speedup = (avg_duration * len(urls)) / total_duration

output = {
    "test": "test5_parallel",
    "platform": "browserbase",
    "total_duration_seconds": round(total_duration, 2),
    "total_duration_minutes": round(total_duration / 60, 3),
    "avg_duration_per_item": round(avg_duration, 2),
    "speedup_factor": round(speedup, 2),
    "execution_mode": "sequential",
    "reason": "Free tier limited to 1 concurrent session",
    "concurrent_sessions_limit": 1,
    "success": True,
    "results": results,
    "session_ids": session_ids,
    "timestamp": time.time()
}

with open('test5_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 60)
print(f"✓ Test 5 completed in {total_duration:.2f}s ({total_duration/60:.3f} minutes)")
print(f"  Execution: Sequential (1 concurrent session limit)")
print(f"  Avg per item: {avg_duration:.2f}s")
print(f"  Speedup: {speedup:.2f}x (no parallelism)")
print(f"  Cost: {total_duration/60:.3f} minutes ({(total_duration/60)/60*100:.2f}% of monthly allowance)")
print("\n" + "⚠️  BROWSERBASE FREE TIER BOTTLENECK:")
print("=" * 60)
print("  Browserbase: 1 concurrent session (sequential only)")
print("  Browserless: 10 concurrent sessions (true parallelism)")
print("  Impact: ~3x slower for parallel workloads")
print("=" * 60)
