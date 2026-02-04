#!/usr/bin/env python3
"""
Test 1: Basic Product Search & Extract
Platform: Browserbase
Target: books.toscrape.com
Task: Extract first 10 product listings (title, price)
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 1: Product Search & Extract")
print("=" * 60)

start_time = time.time()

# Create session with recording
session = bb.sessions.create(
    project_id=os.environ["BROWSERBASE_PROJECT_ID"],
    browser_settings={"record_session": True, "log_session": True}
)

print(f"Session ID: {session.id}")
print(f"Recording URL: https://browserbase.com/sessions/{session.id}")

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate to search
        print("\nNavigating to books.toscrape.com...")
        page.goto('http://books.toscrape.com/')

        # Extract first 10 products
        print("Extracting product data...")
        products = page.locator('article.product_pod').all()[:10]

        results = []
        for idx, product in enumerate(products):
            title = product.locator('h3 a').get_attribute('title')
            price = product.locator('.price_color').inner_text()
            results.append({"title": title, "price": price})
            print(f"  {idx+1}. {title} - {price}")

        browser.close()

    duration = time.time() - start_time

    # Save results
    output = {
        "test": "test1_product_search",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 3),
        "success": True,
        "products_extracted": len(results),
        "results": results,
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test1_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Test 1 completed in {duration:.2f}s ({duration/60:.3f} minutes)")
    print(f"  Extracted {len(results)} products")
    print(f"  Cost: {duration/60:.3f} minutes ({(duration/60)/60*100:.2f}% of monthly allowance)")
    print(f"  View recording: {output['recording_url']}")
    print("=" * 60)

except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ Test 1 failed: {e}")

    output = {
        "test": "test1_product_search",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "success": False,
        "error": str(e),
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test1_results.json', 'w') as f:
        json.dump(output, f, indent=2)
