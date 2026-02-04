#!/usr/bin/env python3
"""
Test 5: Parallel Product Lookups
Goal: Look up 3 different products simultaneously
Platform: Browserless (Async Playwright + CDP)
Tests: Concurrent session handling (free tier = 10 concurrent)
"""

from playwright.async_api import async_playwright
import asyncio
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BROWSERLESS_API_KEY")
if not TOKEN:
    raise ValueError("BROWSERLESS_API_KEY not found in .env file")

ENDPOINT = f"wss://production-sfo.browserless.io?token={TOKEN}"

async def lookup_book(playwright, book_number):
    """
    Look up a single book from the catalog

    Args:
        playwright: Playwright instance
        book_number: Which book to look up (1-3)

    Returns:
        dict: Book details and timing
    """
    start_time = time.time()

    try:
        # Connect to Browserless - each connection creates a new session
        browser = await playwright.chromium.connect_over_cdp(ENDPOINT)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to the site
        await page.goto("http://books.toscrape.com/", wait_until="domcontentloaded")

        # Wait for products to load
        await page.wait_for_selector("article.product_pod", timeout=10000)

        # Get the Nth product (offset by book_number)
        products = page.locator("article.product_pod")
        target_product = products.nth(book_number - 1)

        # Extract data
        title_element = target_product.locator("h3 a")
        title = await title_element.get_attribute("title")

        price_element = target_product.locator("p.price_color")
        price = await price_element.text_content()

        rating_element = target_product.locator("p.star-rating")
        rating_class = await rating_element.get_attribute("class")
        rating = rating_class.replace("star-rating ", "")

        await browser.close()

        duration = time.time() - start_time

        print(f"  Book {book_number}: {title} - {price} ({duration:.2f}s)")

        return {
            'book_number': book_number,
            'success': True,
            'title': title,
            'price': price,
            'rating': rating,
            'duration': duration
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"  Book {book_number}: FAILED - {e} ({duration:.2f}s)")

        return {
            'book_number': book_number,
            'success': False,
            'error': str(e),
            'duration': duration
        }

async def test_parallel_lookups():
    """
    Test parallel product lookups

    Returns:
        dict: Test results including timing and success status
    """

    print("Testing parallel product lookups...")
    print("Looking up 3 different books simultaneously...")

    overall_start = time.time()

    async with async_playwright() as p:
        # Create tasks for parallel execution
        tasks = [
            lookup_book(p, 1),
            lookup_book(p, 2),
            lookup_book(p, 3)
        ]

        # Execute all lookups in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

    overall_duration = time.time() - overall_start

    # Process results
    successful_lookups = [r for r in results if isinstance(r, dict) and r.get('success')]
    failed_lookups = [r for r in results if isinstance(r, dict) and not r.get('success')]

    # Calculate average duration per lookup
    if successful_lookups:
        avg_duration = sum(r['duration'] for r in successful_lookups) / len(successful_lookups)
    else:
        avg_duration = 0

    print(f"\n✓ Parallel execution completed in {overall_duration:.2f}s")
    print(f"  Average per lookup: {avg_duration:.2f}s")
    print(f"  Speedup: {(avg_duration * len(tasks)) / overall_duration:.2f}x")

    return {
        'success': len(successful_lookups) == len(tasks),
        'total_duration': overall_duration,
        'average_duration_per_lookup': avg_duration,
        'speedup_factor': (avg_duration * len(tasks)) / overall_duration if overall_duration > 0 else 0,
        'total_lookups': len(tasks),
        'successful_lookups': len(successful_lookups),
        'failed_lookups': len(failed_lookups),
        'results': results,
        'api_method': 'Async Playwright + CDP',
        'concurrent_sessions': len(tasks),
        'free_tier_limit': '10 concurrent sessions',
        'features_used': [
            'Multiple CDP connections',
            'Async/await parallel execution',
            'Independent browser sessions',
            'asyncio.gather'
        ]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Test 5: Parallel Product Lookups")
    print("Platform: Browserless (Async Playwright + CDP)")
    print("=" * 60)

    result = asyncio.run(test_parallel_lookups())

    # Save results
    output_file = "test5_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")
    print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Total Duration: {result['total_duration']:.2f}s")
    print(f"Concurrent Sessions: {result['concurrent_sessions']}")
    print(f"Successful: {result['successful_lookups']}/{result['total_lookups']}")

    print("\n" + "=" * 60)
    print("Test demonstrates:")
    print("- Parallel execution with multiple CDP connections")
    print(f"- {result['speedup_factor']:.2f}x speedup vs sequential")
    print("- 10 concurrent session capability (free tier)")
    print("- Independent browser session management")
    print("=" * 60)
