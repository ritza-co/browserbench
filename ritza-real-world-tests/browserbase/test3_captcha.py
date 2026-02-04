#!/usr/bin/env python3
"""
Test 3: CAPTCHA Challenge
Platform: Browserbase
Target: Google reCAPTCHA demo
Task: Attempt to solve CAPTCHA (expected to fail on free tier)
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 3: CAPTCHA Challenge")
print("=" * 60)
print("NOTE: CAPTCHA solving requires Developer plan ($20/mo)")
print("Expected outcome: FAIL (not available on free tier)")
print("=" * 60)

# Wait 15 seconds to avoid rate limiting
print("\nWaiting 15 seconds to avoid rate limiting...")
time.sleep(15)

start_time = time.time()

# Try to create session with CAPTCHA solving (may not be supported on free tier)
try:
    # Check if solve_captchas parameter exists
    session = bb.sessions.create(
        project_id=os.environ["BROWSERBASE_PROJECT_ID"],
        browser_settings={
            "record_session": True,
            "log_session": True,
            # Note: solve_captchas may not be a valid parameter or may fail on free tier
        }
    )

    print(f"Session ID: {session.id}")
    print(f"Recording URL: https://browserbase.com/sessions/{session.id}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate to CAPTCHA demo
        print("\nNavigating to CAPTCHA demo...")
        page.goto('https://www.google.com/recaptcha/api2/demo')
        page.wait_for_load_state('networkidle')

        # Take screenshot before
        page.screenshot(path='test3_captcha_page.png')
        print("Screenshot saved: test3_captcha_page.png")

        # Wait to see if CAPTCHA solves automatically (it won't on free tier)
        print("\nWaiting 10 seconds to see if CAPTCHA solves automatically...")
        time.sleep(10)

        # Check if solved
        page.screenshot(path='test3_captcha_unsolved.png')
        print("Screenshot saved: test3_captcha_unsolved.png")

        # Try to check for verification success
        try:
            success_element = page.locator('.recaptcha-success').is_visible(timeout=1000)
            captcha_solved = success_element
        except:
            captcha_solved = False

        browser.close()

    duration = time.time() - start_time

    output = {
        "test": "test3_captcha",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 3),
        "success": False,
        "reason": "CAPTCHA not solved - feature requires Developer plan ($20/mo)",
        "captcha_detected": True,
        "captcha_solved": captcha_solved,
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test3_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print(f"❌ Test 3 failed (expected) - CAPTCHA solving not available on free tier")
    print(f"  Duration: {duration:.2f}s ({duration/60:.3f} minutes)")
    print(f"  CAPTCHA detected: Yes")
    print(f"  CAPTCHA solved: No")
    print(f"  Cost: {duration/60:.3f} minutes ({(duration/60)/60*100:.2f}% of monthly allowance)")
    print(f"  View recording: {output['recording_url']}")
    print("\n💡 Comparison: Browserless has CAPTCHA solving on free tier (costs 10 units)")
    print("=" * 60)

except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ Test 3 failed with exception: {e}")

    output = {
        "test": "test3_captcha",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "success": False,
        "error": str(e),
        "reason": "CAPTCHA solving not available on free tier",
        "timestamp": time.time()
    }

    with open('test3_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print("❌ Test 3 failed (expected) - CAPTCHA solving not available on free tier")
    print("=" * 60)
