#!/usr/bin/env python3
"""
Test 3: CAPTCHA Challenge
Goal: Navigate to CAPTCHA page, attempt to solve it
Platform: Browserless (Playwright + CDP with Stealth + CAPTCHA solving)

WARNING: CAPTCHA solving costs 10 units per attempt (free tier = 1,000 units total)
This is ~1% of free tier monthly allowance per CAPTCHA solve
"""

from playwright.async_api import async_playwright
import asyncio
import os
import time
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BROWSERLESS_API_KEY")
if not TOKEN:
    raise ValueError("BROWSERLESS_API_KEY not found in .env file")

# Use stealth endpoint with CAPTCHA solving enabled
CAPTCHA_ENDPOINT = f"wss://production-sfo.browserless.io/stealth?token={TOKEN}&solveCaptchas=true"

async def test_captcha_solving():
    """
    Test CAPTCHA solving capability

    Returns:
        dict: Test results including timing, success status, and CAPTCHA details
    """

    start_time = time.time()

    print("Testing CAPTCHA solving capability...")
    print("⚠️  WARNING: This test costs 10 units per CAPTCHA solve attempt")

    # Test URL with reCAPTCHA
    test_url = "https://www.google.com/recaptcha/api2/demo"
    print(f"Target URL: {test_url}")

    try:
        async with async_playwright() as p:
            # Connect to Browserless with CAPTCHA solving enabled
            print("\nConnecting to Browserless (stealth + CAPTCHA solving)...")
            browser = await p.chromium.connect_over_cdp(CAPTCHA_ENDPOINT)
            context = browser.contexts[0]
            page = context.pages[0]

            # Get CDP session for CAPTCHA events
            cdp = await page.context.new_cdp_session(page)

            # Set up CAPTCHA event listeners
            captcha_events = {
                'found': asyncio.Event(),
                'solving': asyncio.Event(),
                'solved': asyncio.Event(),
                'details': {}
            }

            def on_captcha_found(event):
                print(f"  🔍 CAPTCHA detected: {event}")
                captcha_events['details']['found'] = event
                captcha_events['found'].set()

            def on_captcha_auto_solved(event):
                print(f"  ✓ CAPTCHA automatically solved: {event}")
                captcha_events['details']['solved'] = event
                captcha_events['solved'].set()

            # Register CDP event listeners
            cdp.on("Browserless.captchaFound", on_captcha_found)
            cdp.on("Browserless.captchaAutoSolved", on_captcha_auto_solved)

            # Navigate to CAPTCHA page
            print("\nNavigating to reCAPTCHA demo page...")
            await page.goto(test_url, wait_until="domcontentloaded", timeout=30000)

            # Take initial screenshot
            await page.screenshot(path="test3_captcha_page.png")
            print("  Screenshot saved: test3_captcha_page.png")

            # Wait for CAPTCHA to be detected (with timeout)
            print("\nWaiting for CAPTCHA detection...")
            try:
                await asyncio.wait_for(captcha_events['found'].wait(), timeout=30.0)
                print("  ✓ CAPTCHA found")
            except asyncio.TimeoutError:
                print("  ⚠️  No CAPTCHA detected (might not be present or already bypassed)")

            # If CAPTCHA was found, wait for it to be solved
            if captcha_events['found'].is_set():
                print("\nWaiting for CAPTCHA to be solved...")
                try:
                    await asyncio.wait_for(captcha_events['solved'].wait(), timeout=60.0)
                    print("  ✓ CAPTCHA solved!")
                except asyncio.TimeoutError:
                    print("  ⚠️  CAPTCHA solving timed out")

                    # Try manual solve trigger
                    print("\nAttempting manual CAPTCHA solve...")
                    try:
                        solve_result = await cdp.send("Browserless.solveCaptcha")
                        print(f"  Manual solve result: {solve_result}")
                    except Exception as e:
                        print(f"  Manual solve failed: {e}")

            # Wait for token to be injected into the form
            print("\nWaiting for CAPTCHA token injection...")
            await page.wait_for_timeout(2000)

            # Submit the form
            print("Submitting form...")
            form_submitted = False
            try:
                # Try to find and click the submit button
                submit_button = page.locator("#recaptcha-demo-submit")
                if await submit_button.count() > 0:
                    await submit_button.click()
                    print("  ✓ Form submitted via button click")
                    form_submitted = True
                else:
                    print("  ⚠️  Submit button not found, trying alternative method")
                    # Try alternative submit method
                    await page.evaluate("document.querySelector('button[type=submit]')?.click()")
                    print("  ✓ Form submitted via JavaScript evaluation")
                    form_submitted = True
            except Exception as e:
                print(f"  ⚠️  Form submission error: {e}")

            # Wait for page to process submission
            if form_submitted:
                print("Waiting for verification result...")
                await page.wait_for_timeout(3000)

            # Take final screenshot
            await page.screenshot(path="test3_captcha_solved.png")
            print("\nFinal screenshot saved: test3_captcha_solved.png")

            # Check if we passed the CAPTCHA
            content = await page.content()
            captcha_passed = (
                "Verification Success" in content or
                "verification-success" in content.lower() or
                "recaptcha-success" in content.lower()
            )

            await browser.close()

            duration = time.time() - start_time

            print(f"\nTest completed in {duration:.2f}s")
            print(f"CAPTCHA Status: {'SOLVED' if captcha_passed else 'NOT SOLVED'}")

            return {
                'success': True,
                'captcha_solved': captcha_passed,
                'form_submitted': form_submitted,
                'duration': duration,
                'captcha_detected': captcha_events['found'].is_set(),
                'auto_solved': captcha_events['solved'].is_set(),
                'captcha_events': {
                    'found': captcha_events['found'].is_set(),
                    'solved': captcha_events['solved'].is_set()
                },
                'screenshots': ['test3_captcha_page.png', 'test3_captcha_solved.png'],
                'api_method': 'Async Playwright + CDP',
                'endpoint': 'Stealth with CAPTCHA solving',
                'features_used': [
                    'Stealth mode',
                    'CAPTCHA detection (Browserless.captchaFound event)',
                    'Automatic CAPTCHA solving',
                    'CDP events',
                    'Form submission after CAPTCHA solve',
                    'Manual solve trigger (Browserless.solveCaptcha)'
                ],
                'cost': '10 units per CAPTCHA solve (~1% of free tier monthly allowance)',
                'test_site': test_url
            }

    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ FAILED: {type(e).__name__}: {e}")

        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'duration': duration
        }

if __name__ == "__main__":
    print("=" * 60)
    print("Test 3: CAPTCHA Challenge")
    print("Platform: Browserless (Stealth + CAPTCHA Solving)")
    print("=" * 60)
    print("\n⚠️  COST WARNING:")
    print("  - CAPTCHA solving costs 10 units per attempt")
    print("  - Free tier = 1,000 units/month")
    print("  - This test uses ~1% of monthly allowance")
    print("=" * 60)

    # Check for --yes flag to skip confirmation
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    if auto_confirm:
        proceed = 'yes'
        print("\nAuto-confirmed via command line flag")
    else:
        proceed = input("\nProceed with CAPTCHA test? (yes/no): ")

    if proceed.lower() in ['yes', 'y']:
        result = asyncio.run(test_captcha_solving())

        # Save results
        output_file = "test3_results.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\nResults saved to: {output_file}")
        print(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
        print(f"Duration: {result['duration']:.2f}s")

        if result['success']:
            print(f"CAPTCHA Detected: {result['captcha_detected']}")
            print(f"CAPTCHA Solved: {result['captcha_solved']}")

            print("\n" + "=" * 60)
            print("Test demonstrates:")
            print("- CAPTCHA detection via CDP events")
            print("- Automatic CAPTCHA solving")
            print("- Stealth mode integration")
            print("- Event-driven automation")
            print("=" * 60)
    else:
        print("\nTest skipped by user")
        result = {
            'success': False,
            'skipped': True,
            'reason': 'User chose to skip due to unit cost'
        }

        output_file = "test3_results.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Skipped result saved to: {output_file}")
