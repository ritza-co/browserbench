#!/usr/bin/env python3
"""
Test 2: Multi-Page Navigation (Product → Details)
Goal: Navigate to product page, click to view details, extract information
Platform: Browserless (Playwright + CDP)
Target: books.toscrape.com - Navigate from listing to book detail page
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

def test_multipage_navigation():
    """
    Navigate from product listing to product detail page and extract data

    Returns:
        dict: Test results including timing, success status, and extracted data
    """

    start_time = time.time()

    print("Testing multi-page navigation...")
    print("Step 1: Load product listing page")
    print("Step 2: Click on first product")
    print("Step 3: Extract details from product page")

    try:
        with sync_playwright() as p:
            # Connect to Browserless
            browser = p.chromium.connect_over_cdp(ENDPOINT)
            context = browser.new_context()
            page = context.new_page()

            # Step 1: Navigate to listing page
            step1_start = time.time()
            page.goto("http://books.toscrape.com/", wait_until="domcontentloaded")
            page.wait_for_selector("article.product_pod", timeout=10000)
            step1_duration = time.time() - step1_start
            print(f"  ✓ Step 1 complete ({step1_duration:.2f}s)")

            # Step 2: Click on first product to go to detail page
            step2_start = time.time()
            first_product = page.locator("article.product_pod h3 a").first
            product_title = first_product.get_attribute("title")
            print(f"  Clicking on: {product_title}")

            # Click the product link
            first_product.click()

            # Wait for detail page to load
            page.wait_for_selector("div.product_main", timeout=10000)
            step2_duration = time.time() - step2_start
            print(f"  ✓ Step 2 complete ({step2_duration:.2f}s)")

            # Step 3: Extract details from product page
            step3_start = time.time()

            # Extract detailed information
            title = page.locator("div.product_main h1").text_content().strip()
            price = page.locator("p.price_color").text_content().strip()
            availability = page.locator("p.instock.availability").text_content().strip()

            # Get product description
            description = ""
            try:
                desc_element = page.locator("#product_description + p")
                if desc_element.count() > 0:
                    description = desc_element.text_content().strip()
            except:
                description = "No description available"

            # Get product information table
            product_info = {}
            rows = page.locator("table.table.table-striped tr").all()
            for row in rows:
                key = row.locator("th").text_content().strip()
                value = row.locator("td").text_content().strip()
                product_info[key] = value

            step3_duration = time.time() - step3_start
            print(f"  ✓ Step 3 complete ({step3_duration:.2f}s)")

            browser.close()

            total_duration = time.time() - start_time

            # Print results
            print(f"\n✓ SUCCESS: Multi-page navigation completed in {total_duration:.2f}s\n")
            print(f"Product Details:")
            print(f"  Title: {title}")
            print(f"  Price: {price}")
            print(f"  Availability: {availability}")
            print(f"  Description: {description[:100]}...")
            print(f"  Product Info: {len(product_info)} fields extracted")

            # Return test results
            return {
                'success': True,
                'duration': total_duration,
                'step_timings': {
                    'step1_listing_page': step1_duration,
                    'step2_navigation': step2_duration,
                    'step3_extraction': step3_duration
                },
                'product_details': {
                    'title': title,
                    'price': price,
                    'availability': availability,
                    'description': description,
                    'product_info': product_info
                },
                'api_method': 'Playwright + CDP',
                'features_used': [
                    'CDP connection',
                    'Multi-page navigation',
                    'Click interactions',
                    'wait_for_selector',
                    'Table data extraction'
                ]
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
    print("Test 2: Multi-Page Navigation")
    print("Platform: Browserless (Playwright + CDP)")
    print("=" * 60)

    result = test_multipage_navigation()

    # Save results
    output_file = "test2_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Total Duration: {result['duration']:.2f}s")

    if result['success']:
        print("\n" + "=" * 60)
        print("Test demonstrates:")
        print("- Stable multi-page navigation")
        print("- Click interactions")
        print("- Page transition handling")
        print("- Complex data extraction (text, tables)")
        print("=" * 60)
