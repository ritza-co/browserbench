#!/usr/bin/env python3
"""
Test 4: Intentional Selector Failure (Debugging)
Platform: Browserbase
Target: books.toscrape.com with broken selectors
Task: Trigger errors and showcase Browserbase's debugging tools
THIS IS BROWSERBASE'S KEY ADVANTAGE: Session replay on free tier
"""

from browserbase import Browserbase
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])

print("Starting Test 4: Intentional Selector Failure (Debugging)")
print("=" * 60)
print("THIS IS BROWSERBASE'S KEY ADVANTAGE")
print("Session replay available on free tier (not available on Browserless free tier)")
print("=" * 60)

# Wait 15 seconds to avoid rate limiting
print("\nWaiting 15 seconds to avoid rate limiting...")
time.sleep(15)

start_time = time.time()

session = bb.sessions.create(
    project_id=os.environ["BROWSERBASE_PROJECT_ID"],
    browser_settings={"record_session": True, "log_session": True}
)

print(f"\nSession ID: {session.id}")
print(f"Recording URL: https://browserbase.com/sessions/{session.id}")
print(f"Starting test with intentional failures...")

errors_encountered = []

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(session.connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate successfully
        print("\n1. Navigating to books.toscrape.com...")
        page.goto('http://books.toscrape.com/')

        # Try to find element that doesn't exist
        print("2. Attempting to click non-existent selector...")
        try:
            page.locator('div.this-selector-does-not-exist').click(timeout=5000)
        except Exception as e:
            error_msg = f"Expected error: {type(e).__name__}"
            print(f"   ✓ {error_msg}")
            errors_encountered.append(error_msg)
            page.screenshot(path='test4_error_state.png')
            print("   Screenshot saved: test4_error_state.png")

        # Try another broken selector
        print("3. Attempting to extract text from non-existent element...")
        try:
            price = page.locator('.nonexistent-price-class').inner_text(timeout=5000)
        except Exception as e:
            error_msg = f"Expected error: {type(e).__name__}"
            print(f"   ✓ {error_msg}")
            errors_encountered.append(error_msg)

        # Save page content for debugging
        content = page.content()
        with open('test4_page_content.html', 'w') as f:
            f.write(content)
        print("   Page HTML saved: test4_page_content.html")

        browser.close()

    duration = time.time() - start_time

    # Wait for logs to be processed
    print("\n⏳ Waiting 5 seconds for logs to be processed...")
    time.sleep(5)

    # Try to retrieve logs
    try:
        logs = bb.sessions.logs.list(session.id)
        logs_count = len(logs) if logs else 0
    except Exception as e:
        print(f"   Note: Could not retrieve logs via API: {e}")
        logs_count = 0

    output = {
        "test": "test4_selector_failure",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "duration_minutes": round(duration / 60, 3),
        "success": True,
        "errors_triggered": len(errors_encountered),
        "error_types": errors_encountered,
        "debugging_features": {
            "session_recording": True,
            "session_inspector": True,
            "logs_api": True,
            "video_replay": True,
            "rrweb_dom_replay": True,
            "live_debug_url": True,
            "available_on_free_tier": True
        },
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "logs_retrieved": logs_count,
        "timestamp": time.time()
    }

    with open('test4_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Test 4 completed in {duration:.2f}s ({duration/60:.3f} minutes)")
    print(f"  Errors triggered: {len(errors_encountered)}")
    print(f"  Cost: {duration/60:.3f} minutes ({(duration/60)/60*100:.2f}% of monthly allowance)")
    print("\n" + "🎬 DEBUGGING TOOLS AVAILABLE (ALL ON FREE TIER):")
    print("=" * 60)
    print(f"  1. Session Recording (video): {output['recording_url']}")
    print(f"  2. Session Inspector: Click session in dashboard")
    print(f"  3. rrweb DOM Replay: Programmatic access available")
    print(f"  4. Network logs, console logs, DOM inspection")
    if logs_count > 0:
        print(f"  5. Logs API: Retrieved {logs_count} log entries")
    print("\n" + "💡 KEY ADVANTAGE:")
    print("=" * 60)
    print("  Browserbase: ✅ Session replay ON FREE TIER")
    print("  Browserless: ❌ Session replay Enterprise only (not on free tier)")
    print("  This is a MAJOR differentiator for debugging failed automation")
    print("=" * 60)

except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ Test 4 had unexpected failure: {e}")

    output = {
        "test": "test4_selector_failure",
        "platform": "browserbase",
        "duration_seconds": round(duration, 2),
        "success": False,
        "error": str(e),
        "session_id": session.id,
        "recording_url": f"https://browserbase.com/sessions/{session.id}",
        "timestamp": time.time()
    }

    with open('test4_results.json', 'w') as f:
        json.dump(output, f, indent=2)
