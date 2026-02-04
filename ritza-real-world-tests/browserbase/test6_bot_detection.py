#!/usr/bin/env python3
"""
Test 6: Bot Detection (Stealth Mode)
Platform: Browserbase
Target: bot.sannysoft.com
Task: Test bot detection evasion
NOTE: Stealth mode NOT available on free tier (requires Developer plan $20/mo)
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 6: Bot Detection (Stealth Mode)")
print("=" * 60)
print("NOTE: Stealth mode requires Developer plan ($20/mo)")
print("Testing with basic mode only")
print("=" * 60)

# Wait 15 seconds to avoid rate limiting
print("\nWaiting 15 seconds to avoid rate limiting...")
time.sleep(15)

start_time = time.time()

# Test with basic mode (no stealth)
session = bb.sessions.create(
    project_id=os.environ["BROWSERBASE_PROJECT_ID"],
    browser_settings={
        "record_session": True,
        "log_session": True
    }
)

print(f"\nSession ID: {session.id}")
print(f"Recording URL: https://browserbase.com/sessions/{session.id}")

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate to bot detection test
        print("\nNavigating to bot detection site...")
        page.goto('https://bot.sannysoft.com/')
        page.wait_for_load_state('networkidle')

        # Take screenshot
        page.screenshot(path='test6_bot_detection.png', full_page=True)
        print("Screenshot saved: test6_bot_detection.png")

        # Check for detection indicators in page content
        page_content = page.content()

        # Look for common indicators (simplified check)
        indicators = {
            "webdriver": "webdriver" in page_content.lower(),
            "headless": "headless" in page_content.lower(),
            "automation": "automation" in page_content.lower()
        }

        # Count detected indicators
        detected_count = sum(1 for v in indicators.values() if v)

        browser.close()

    duration = time.time() - start_time

    output = {
        "test": "test6_bot_detection",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 3),
        "stealth_mode_available": False,
        "stealth_mode_used": False,
        "reason": "Stealth mode requires Developer plan ($20/mo)",
        "detection_indicators": indicators,
        "detected": any(indicators.values()),
        "detected_count": detected_count,
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test6_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Test 6 completed in {duration:.2f}s ({duration/60:.3f} minutes)")
    print(f"  Stealth mode: Not available on free tier")
    print(f"  Bot detected: {output['detected']}")
    if detected_count > 0:
        print(f"  Indicators found: {[k for k, v in indicators.items() if v]}")
    else:
        print(f"  No obvious detection indicators found")
    print(f"  Cost: {duration/60:.3f} minutes ({(duration/60)/60*100:.2f}% of monthly allowance)")
    print(f"  View recording: {output['recording_url']}")
    print("\n" + "💡 COMPARISON:")
    print("=" * 60)
    print("  Browserbase: ❌ Stealth mode requires Developer plan ($20/mo)")
    print("  Browserless: ✅ Stealth mode available on free tier")
    print("=" * 60)

except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ Test 6 failed: {e}")

    output = {
        "test": "test6_bot_detection",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "success": False,
        "error": str(e),
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test6_results.json', 'w') as f:
        json.dump(output, f, indent=2)
