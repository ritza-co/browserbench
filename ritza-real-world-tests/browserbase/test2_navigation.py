#!/usr/bin/env python3
"""
Test 2: Multi-Page Navigation (Product → Details)
Platform: Browserbase
Target: books.toscrape.com
Task: Navigate from catalog to product detail page, extract complex data
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 2: Multi-Page Navigation")
print("=" * 60)

# Wait 15 seconds to avoid rate limiting
print("Waiting 15 seconds to avoid rate limiting...")
time.sleep(15)

start_time = time.time()

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

        # Navigate to catalog
        print("\nNavigating to books catalog...")
        page.goto('http://books.toscrape.com/catalogue/category/books_1/index.html')

        books_visited = []

        # Visit three different books
        for i in range(3):
            print(f"\nVisiting book {i+1}...")

            # Navigate back to catalog if not first iteration
            if i > 0:
                print("  Navigating back to catalog...")
                page.goto('http://books.toscrape.com/catalogue/category/books_1/index.html')
                page.wait_for_load_state('networkidle')

            # Click a different book each time (first, second, third)
            print(f"  Clicking book #{i+1} in catalog...")
            page.locator('article.product_pod h3 a').nth(i).click()
            page.wait_for_load_state('networkidle')

            # Extract product details
            print("  Extracting product details...")
            title = page.locator('h1').inner_text()
            price = page.locator('.product_main .price_color').inner_text()

            # Try to get description (may not exist for all books)
            try:
                description = page.locator('#product_description + p').inner_text()
            except:
                description = "No description available"

            availability = page.locator('.product_main .availability').inner_text().strip()

            print(f"    Title: {title}")
            print(f"    Price: {price}")
            print(f"    Availability: {availability}")

            books_visited.append({
                "title": title,
                "price": price,
                "description": description,
                "availability": availability
            })

        browser.close()

    duration = time.time() - start_time

    output = {
        "test": "test2_navigation",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 3),
        "success": True,
        "books_visited": books_visited,
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test2_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Test 2 completed in {duration:.2f}s ({duration/60:.3f} minutes)")
    print(f"  Visited {len(books_visited)} books with back-and-forth navigation")
    print(f"  Cost: {duration/60:.3f} minutes ({(duration/60)/60*100:.2f}% of monthly allowance)")
    print(f"  View recording: {output['recording_url']}")
    print("=" * 60)

except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ Test 2 failed: {e}")

    output = {
        "test": "test2_navigation",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "success": False,
        "error": str(e),
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test2_results.json', 'w') as f:
        json.dump(output, f, indent=2)
