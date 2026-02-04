#!/usr/bin/env python3
"""
Test 2: Multi-Page Navigation (Product → Details)

Target: books.toscrape.com
Task: Navigate to product, click to details, extract data
Tests: Multi-step navigation stability
Platform Feature Focus: Session stability across page transitions
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
    print("Test 2: Multi-Page Navigation (Product → Details)")
    print("=" * 60)

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    # Create session with recording enabled for debugging
    session_config = {
        "session": {
            "recording": True,
            "max_duration": 5,
            "idle_timeout": 2
        }
    }

    session = client.sessions.create(browser=session_config)
    session_id = session.data.id
    cdp_url = session.data.cdp_url
    live_view_url = session.data.live_view_url

    print(f"\n✓ Session created: {session_id}")

    result = {}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Step 1: Navigate to catalog
            print(f"\n→ Step 1: Navigating to catalog page...")
            await page.goto("https://books.toscrape.com/catalogue/category/books_1/index.html")
            await page.wait_for_selector(".product_pod", timeout=10000)
            print(f"✓ Catalog page loaded")

            # Step 2: Click first product
            print(f"\n→ Step 2: Clicking first product...")
            first_product = await page.query_selector(".product_pod h3 a")
            product_title_preview = await first_product.get_attribute("title")
            print(f"  Target: {product_title_preview[:50]}...")

            await first_product.click()

            # Step 3: Wait for detail page and extract data
            print(f"\n→ Step 3: Extracting product details...")
            await page.wait_for_selector(".product_main", timeout=10000)

            title = await page.locator(".product_main h1").text_content()
            price = await page.locator(".product_main .price_color").text_content()
            availability = await page.locator(".product_main .availability").text_content()

            # Try to get description (not all books have one)
            try:
                description = await page.locator("#product_description + p").text_content()
            except:
                description = "No description available"

            result = {
                "title": title.strip(),
                "price": price.strip(),
                "availability": availability.strip(),
                "description": description.strip()[:100] + "..." if len(description) > 100 else description.strip()
            }

            print(f"\n✓ Product Details Extracted:")
            print(f"  Title: {result['title']}")
            print(f"  Price: {result['price']}")
            print(f"  Availability: {result['availability']}")
            print(f"  Description: {result['description'][:80]}...")

            # Take screenshot
            await page.screenshot(path="test2_navigation.png")
            print(f"\n✓ Screenshot saved: test2_navigation.png")

            await browser.close()

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        result = {"error": str(e)}

    finally:
        # Clean up session
        print(f"\n→ Cleaning up session...")
        client.sessions.delete(session_id)
        print(f"✓ Session deleted: {session_id}")

    # Calculate metrics
    duration = time.time() - start_time
    success = "title" in result and "price" in result

    # Save results
    result_data = {
        "test": "Test 2: Multi-Page Navigation",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "success": success,
        "session_id": session_id,
        "live_view_url": live_view_url,
        "product_data": result,
        "approach": "SDK + Playwright CDP (multi-step workflow)",
        "estimated_cost": "$0.01 (creation) + ~$0.0008 (time)"
    }

    with open("test2_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
    print(f"Duration: {duration:.2f}s")
    print(f"Navigation: Catalog → Product Details")
    print(f"Session ID: {session_id}")
    print(f"Results saved: test2_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
