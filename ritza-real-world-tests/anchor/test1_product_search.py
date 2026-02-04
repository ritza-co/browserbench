#!/usr/bin/env python3
"""
Test 1: Product Search & Extract

Target: books.toscrape.com
Task: Search for products, extract first 10 results (title, price)
Tests: Basic navigation + data extraction reliability
Platform Feature Focus: Standard Playwright scraping (baseline)
"""

import asyncio
import json
import os
import time
from anchorbrowser import Anchorbrowser
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def main():
    start_time = time.time()

    print("=" * 60)
    print("Test 1: Product Search & Extract")
    print("=" * 60)

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    # Create session with reasonable timeout
    session_config = {
        "session": {
            "max_duration": 5,  # 5 minutes max
            "idle_timeout": 2   # 2 minutes idle
        }
    }

    session = client.sessions.create(browser=session_config)
    session_id = session.data.id
    cdp_url = session.data.cdp_url
    live_view_url = session.data.live_view_url

    print(f"\n✓ Session created: {session_id}")
    print(f"  CDP URL: {cdp_url[:50]}...")
    print(f"\n{'!'*60}")
    print(f"! LIVE VIEW URL (open now to watch in real-time):")
    print(f"! {live_view_url}")
    print(f"{'!'*60}\n")

    results = []

    try:
        async with async_playwright() as p:
            # Connect to Anchor session via CDP
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            print(f"\n→ Navigating to books.toscrape.com...")
            await page.goto("https://books.toscrape.com/")

            # Wait for products to load
            await page.wait_for_selector(".product_pod", timeout=10000)
            print(f"✓ Page loaded successfully")

            # Extract product data
            products = await page.query_selector_all(".product_pod")
            print(f"\n→ Extracting data from {min(len(products), 10)} products...")

            for i, product in enumerate(products[:10], 1):
                try:
                    title_elem = await product.query_selector("h3 a")
                    price_elem = await product.query_selector(".price_color")

                    title = await title_elem.get_attribute("title")
                    price = await price_elem.text_content()

                    results.append({
                        "position": i,
                        "title": title,
                        "price": price
                    })

                    print(f"  {i}. {title[:50]}... - {price}")

                except Exception as e:
                    print(f"  ✗ Error extracting product {i}: {e}")

            # Take screenshot
            await page.screenshot(path="test1_product_search.png")
            print(f"\n✓ Screenshot saved: test1_product_search.png")

            await browser.close()

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        results = []

    finally:
        # Clean up session
        print(f"\n→ Cleaning up session...")
        client.sessions.delete(session_id)
        print(f"✓ Session deleted: {session_id}")

    # Calculate metrics
    duration = time.time() - start_time
    success = len(results) == 10

    # Save results
    result_data = {
        "test": "Test 1: Product Search & Extract",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "success": success,
        "products_extracted": len(results),
        "session_id": session_id,
        "live_view_url": live_view_url,
        "products": results,
        "approach": "SDK + Playwright CDP (standard scraping)",
        "estimated_cost": "$0.01 (creation) + ~$0.0004 (time)"
    }

    with open("test1_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
    print(f"Duration: {duration:.2f}s")
    print(f"Products extracted: {len(results)}/10")
    print(f"Session ID: {session_id}")
    print(f"Results saved: test1_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
