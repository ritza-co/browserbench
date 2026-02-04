#!/usr/bin/env python3
"""
Test 5: Parallel Product Lookups

Target: books.toscrape.com
Task: Look up 3 different categories simultaneously
Tests: Concurrent session handling
Platform Feature Focus: 5 concurrent sessions (vs 10 for Browserless, 1 for Browserbase)
"""

import asyncio
import json
import os
import time
from anchorbrowser import Anchorbrowser
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def scrape_category(client, category_name, category_id):
    """Scrape a single category in parallel"""
    session_start = time.time()

    # Create session for this category
    session = client.sessions.create()
    session_id = session.data.id
    cdp_url = session.data.cdp_url
    live_view_url = session.data.live_view_url

    print(f"  → Session created for {category_name}: {session_id[:20]}...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to category
            url = f"https://books.toscrape.com/catalogue/category/books/{category_name.lower().replace(' ', '-')}_{category_id}/index.html"
            await page.goto(url, timeout=30000)
            await page.wait_for_selector(".product_pod", timeout=10000)

            # Extract first 5 products
            products = await page.query_selector_all(".product_pod")
            results = []

            for product in products[:5]:
                try:
                    title_elem = await product.query_selector("h3 a")
                    price_elem = await product.query_selector(".price_color")

                    title = await title_elem.get_attribute("title")
                    price = await price_elem.text_content()

                    results.append({
                        "title": title,
                        "price": price
                    })
                except:
                    pass  # Skip if element not found

            await browser.close()
            duration = time.time() - session_start

            print(f"  ✓ {category_name}: {len(results)} products in {duration:.2f}s")

            return {
                "category": category_name,
                "category_id": category_id,
                "session_id": session_id,
        "live_view_url": live_view_url,
                "duration": duration,
                "products": results,
                "success": True
            }

    except Exception as e:
        duration = time.time() - session_start
        print(f"  ✗ {category_name}: FAILED - {str(e)[:50]}")

        return {
            "category": category_name,
            "category_id": category_id,
            "session_id": session_id,
        "live_view_url": live_view_url,
            "duration": duration,
            "error": str(e),
            "success": False
        }

    finally:
        # Clean up session
        client.sessions.delete(session_id)


async def main():
    start_time = time.time()

    print("=" * 60)
    print("Test 5: Parallel Product Lookups")
    print("=" * 60)

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    print(f"\n→ Testing 5 concurrent session limit...")
    print(f"  Running 3 categories in parallel")

    # Define 3 categories to scrape
    categories = [
        ("Travel", 2),
        ("Mystery", 3),
        ("Historical Fiction", 4)
    ]

    print(f"\n→ Creating 3 parallel sessions...")

    # Create tasks for parallel execution
    tasks = [scrape_category(client, name, cat_id) for name, cat_id in categories]

    # Run all tasks concurrently
    parallel_start = time.time()
    results = await asyncio.gather(*tasks)
    total_duration = time.time() - parallel_start

    # Calculate metrics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    avg_duration = sum(r["duration"] for r in results) / len(results)
    speedup = (avg_duration * len(results)) / total_duration if total_duration > 0 else 0

    # Save results
    result_data = {
        "test": "Test 5: Parallel Product Lookups",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_duration_seconds": round(total_duration, 2),
        "avg_duration_per_category": round(avg_duration, 2),
        "speedup_factor": round(speedup, 2),
        "success": len(successful) == len(categories),
        "successful_categories": len(successful),
        "failed_categories": len(failed),
        "concurrent_limit": 5,
        "categories_tested": len(categories),
        "results": results,
        "approach": "SDK + Async Playwright (3 concurrent sessions)",
        "estimated_cost": "$0.03 (creation) + ~$0.00125 (time)"
    }

    with open("test5_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if len(successful) == len(categories) else '⚠️  PARTIAL'}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Avg Per Category: {avg_duration:.2f}s")
    print(f"Speedup Factor: {speedup:.2f}x")
    print(f"\nResults: {len(successful)}/{len(categories)} successful")

    for result in results:
        status = "✓" if result["success"] else "✗"
        if result["success"]:
            print(f"  {status} {result['category']}: {len(result['products'])} products in {result['duration']:.2f}s")
        else:
            print(f"  {status} {result['category']}: FAILED")

    print(f"\nConcurrent Limit: 5 sessions")
    print(f"Categories Tested: {len(categories)}")
    print(f"Results saved: test5_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
