#!/usr/bin/env python3
"""
Test 4: Intentional Selector Failure
Goal: Build workflow with broken selector, let it fail, test debugging tools
Platform: Browserless (Playwright + CDP)
Focus: Debugging capabilities on free tier (no session replay)
"""

from playwright.sync_api import sync_playwright
import os
import time
import json
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BROWSERLESS_API_KEY")
if not TOKEN:
    raise ValueError("BROWSERLESS_API_KEY not found in .env file")

ENDPOINT = f"wss://production-sfo.browserless.io?token={TOKEN}"

def test_selector_failure():
    """
    Intentionally use a broken selector and test debugging capabilities

    Returns:
        dict: Test results including error details and debugging info
    """

    start_time = time.time()

    print("Testing intentional selector failure and debugging tools...")

    debugging_info = {
        'console_logs': [],
        'network_requests': [],
        'page_errors': []
    }

    try:
        with sync_playwright() as p:
            # Connect to Browserless
            browser = p.chromium.connect_over_cdp(ENDPOINT)
            context = browser.new_context()
            page = context.new_page()

            # Set up event listeners for debugging
            page.on("console", lambda msg: debugging_info['console_logs'].append({
                'type': msg.type,
                'text': msg.text
            }))

            page.on("pageerror", lambda err: debugging_info['page_errors'].append(str(err)))

            page.on("request", lambda req: debugging_info['network_requests'].append({
                'method': req.method,
                'url': req.url,
                'type': 'request'
            }))

            # Navigate to test page
            print("\nStep 1: Navigate to test site...")
            page.goto("http://books.toscrape.com/", wait_until="domcontentloaded")
            print("  ✓ Navigation successful")

            # Try to find an element that exists (baseline)
            print("\nStep 2: Test with CORRECT selector...")
            try:
                page.wait_for_selector("article.product_pod", timeout=5000)
                print("  ✓ Correct selector found")
            except Exception as e:
                print(f"  ✗ Unexpected: Correct selector failed - {e}")

            # Now try with a broken selector (intentional failure)
            print("\nStep 3: Test with BROKEN selector...")
            print("  Attempting to find: 'div.this-selector-does-not-exist'")

            error_occurred = None
            try:
                page.wait_for_selector("div.this-selector-does-not-exist", timeout=5000)
                print("  ✗ Unexpected: Broken selector succeeded (shouldn't happen)")
            except Exception as e:
                error_occurred = e
                print(f"  ✓ Expected error occurred: {type(e).__name__}")
                print(f"  Error message: {str(e)[:100]}...")

            # Debugging steps
            print("\nStep 4: Gather debugging information...")

            # Get current page state
            current_url = page.url
            page_title = page.title()
            print(f"  Current URL: {current_url}")
            print(f"  Page title: {page_title}")

            # Take screenshot for visual debugging
            screenshot_path = "test4_error_state.png"
            page.screenshot(path=screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Save page HTML for inspection
            html_path = "test4_page_content.html"
            content = page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Page HTML saved: {html_path} ({len(content)} bytes)")

            # Check what selectors ARE available
            print("\nStep 5: Identify available selectors...")
            available_selectors = []
            test_selectors = [
                "article.product_pod",
                "h1",
                "div.page_inner",
                "ul.nav"
            ]

            for selector in test_selectors:
                count = page.locator(selector).count()
                if count > 0:
                    available_selectors.append({'selector': selector, 'count': count})
                    print(f"  Found: {selector} ({count} elements)")

            browser.close()

            duration = time.time() - start_time

            print(f"\n✓ SUCCESS: Debugging test completed in {duration:.2f}s")

            return {
                'success': True,
                'duration': duration,
                'error_handled': error_occurred is not None,
                'error_details': {
                    'type': type(error_occurred).__name__ if error_occurred else None,
                    'message': str(error_occurred) if error_occurred else None
                },
                'debugging_tools_used': [
                    'Screenshots',
                    'Page HTML capture',
                    'Console logs',
                    'Network monitoring',
                    'Selector validation',
                    'Page state inspection'
                ],
                'debugging_info': {
                    'page_url': current_url,
                    'page_title': page_title,
                    'screenshot': screenshot_path,
                    'html_dump': html_path,
                    'console_logs': len(debugging_info['console_logs']),
                    'network_requests': len(debugging_info['network_requests']),
                    'page_errors': len(debugging_info['page_errors']),
                    'available_selectors': available_selectors
                },
                'free_tier_limitations': [
                    'No live debugger (Enterprise only)',
                    'No session replay (Enterprise only)',
                    'Debugging relies on Playwright built-in tools'
                ],
                'api_method': 'Playwright + CDP'
            }

    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'duration': duration
        }

if __name__ == "__main__":
    print("=" * 60)
    print("Test 4: Intentional Selector Failure (Debugging)")
    print("Platform: Browserless (Playwright + CDP)")
    print("=" * 60)

    result = test_selector_failure()

    # Save results
    output_file = "test4_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
    print(f"Duration: {result['duration']:.2f}s")

    if result['success']:
        print("\n" + "=" * 60)
        print("Debugging Tools Available on Free Tier:")
        print("=" * 60)
        for tool in result['debugging_tools_used']:
            print(f"  - {tool}")

        print("\nFree Tier Limitations:")
        for limitation in result['free_tier_limitations']:
            print(f"  - {limitation}")
        print("=" * 60)
