#!/usr/bin/env python3
"""
Test 1: Basic Product Search & Extract
Goal: Scrape book listing site, extract first 10 results (title, price)
Platform: Browserless (Playwright + CDP)
Note: Using books.toscrape.com as it's designed for scraping practice
"""

from playwright.sync_api import sync_playwright
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

def scrape_products(max_results=10):
    """
    Scrape book products from books.toscrape.com

    Args:
        max_results: Maximum number of results to extract

    Returns:
        dict: Test results including timing, success status, and extracted data
    """

    start_time = time.time()

    print(f"Scraping books.toscrape.com...")
    target_url = "http://books.toscrape.com/"
    print(f"Target URL: {target_url}")

    try:
        with sync_playwright() as p:
            # Connect to Browserless
            browser = p.chromium.connect_over_cdp(ENDPOINT)
            context = browser.new_context()
            page = context.new_page()

            # Navigate to site
            page.goto(target_url, wait_until="domcontentloaded")

            # Wait for product listings
            page.wait_for_selector("article.product_pod", timeout=10000)

            # Extract product data
            products = []
            items = page.locator("article.product_pod").all()[:max_results]

            for item in items:
                try:
                    # Extract title
                    title_element = item.locator("h3 a")
                    title = title_element.get_attribute("title")

                    # Extract price
                    price_element = item.locator("p.price_color")
                    price = price_element.text_content().strip()

                    # Extract rating
                    rating_element = item.locator("p.star-rating")
                    rating_class = rating_element.get_attribute("class")
                    rating = rating_class.replace("star-rating ", "")

                    products.append({
                        'title': title,
                        'price': price,
                        'rating': rating
                    })

                except Exception as e:
                    print(f"Error extracting item: {e}")
                    continue

            browser.close()

            duration = time.time() - start_time

            # Print results
            print(f"\n✓ SUCCESS: Found {len(products)} products in {duration:.2f}s\n")
            for i, product in enumerate(products, 1):
                print(f"{i}. {product['title']}")
                print(f"   Price: {product['price']} | Rating: {product['rating']}\n")

            # Return test results
            return {
                'success': len(products) > 0,
                'duration': duration,
                'products_found': len(products),
                'products': products,
                'api_method': 'Playwright + CDP',
                'target_site': 'books.toscrape.com',
                'features_used': ['CDP connection', 'Playwright selectors', 'wait_for_selector', 'get_attribute'],
                'note': 'Using scraping-friendly test site to demonstrate data extraction capability'
            }

    except Exception as e:
        duration = time.time() - start_time
        print(f"✗ FAILED: {type(e).__name__}: {e}")

        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'duration': duration
        }

if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Basic Product Search & Extract")
    print("Platform: Browserless (Playwright + CDP)")
    print("=" * 60)

    result = scrape_products(max_results=10)

    # Save results
    output_file = "test1_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Duration: {result['duration']:.2f}s")
    if result['success']:
        print(f"Products extracted: {result['products_found']}")

    print("\n" + "=" * 60)
    print("Test demonstrates:")
    print("- CDP connection to Browserless")
    print("- Basic navigation and data extraction")
    print("- Multiple selector types (text, attributes)")
    print("- Reliable extraction from structured HTML")
    print("=" * 60)
