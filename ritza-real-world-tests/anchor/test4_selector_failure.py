#!/usr/bin/env python3
"""
Test 4: Selector Failure (Debugging)

Target: books.toscrape.com with broken selectors
Task: Build workflow with selectors that don't exist, let it fail, debug
Tests: Debugging tools when automation breaks
Platform Feature Focus: Live View URL, Playwright tools
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
    print("Test 4: Selector Failure (Debugging)")
    print("=" * 60)

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    # Enable recording for debugging
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
    live_view_url = session.data.live_view_url

    print(f"\n✓ Session created: {session_id}")
    print(f"\n🔴 LIVE VIEW URL (open in browser to watch):")
    print(f"   {live_view_url}")

    console_messages = []
    errors_captured = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Enable console message capture
            page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

            print(f"\n→ Navigating to books.toscrape.com...")
            await page.goto("https://books.toscrape.com/")
            await page.wait_for_selector(".product_pod", timeout=10000)
            print(f"✓ Page loaded successfully")

            # Intentional error #1: Broken selector (timeout)
            print(f"\n--- Test 1: Broken selector (wait timeout) ---")
            try:
                await page.wait_for_selector("div.this-selector-does-not-exist", timeout=3000)
                print("✗ ERROR: Selector should have timed out!")
            except Exception as e:
                print(f"✓ Expected timeout caught: {type(e).__name__}")
                errors_captured.append({
                    "test": "Broken selector timeout",
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:100]
                })
                await page.screenshot(path="test4_error1_screenshot.png")
                print(f"  Screenshot saved: test4_error1_screenshot.png")

            # Intentional error #2: Missing element (returns None)
            print(f"\n--- Test 2: Missing element query ---")
            try:
                missing_elem = await page.query_selector("button#fake-button-id")
                if missing_elem is None:
                    print(f"✓ Element correctly returned None")
                    errors_captured.append({
                        "test": "Missing element query",
                        "error_type": "None",
                        "error_message": "Element not found (returned None)"
                    })
                else:
                    print(f"✗ ERROR: Element should be None!")
            except Exception as e:
                print(f"✗ Unexpected error: {e}")

            # Intentional error #3: Navigation timeout
            print(f"\n--- Test 3: Navigation timeout ---")
            try:
                await page.goto("https://httpstat.us/504", timeout=3000)
            except Exception as e:
                print(f"✓ Expected navigation timeout: {type(e).__name__}")
                errors_captured.append({
                    "test": "Navigation timeout",
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:100]
                })

            # Return to working page
            await page.goto("https://books.toscrape.com/")
            await page.wait_for_selector(".product_pod", timeout=10000)

            # Capture debugging artifacts
            print(f"\n→ Capturing debugging artifacts...")
            await page.screenshot(path="test4_final_state.png")
            print(f"✓ Final screenshot: test4_final_state.png")

            html_content = await page.content()
            with open("test4_page_content.html", "w") as f:
                f.write(html_content)
            print(f"✓ HTML dump: test4_page_content.html ({len(html_content)} bytes)")

            print(f"\n--- Console Messages ({len(console_messages)}) ---")
            if console_messages:
                for msg in console_messages[-10:]:  # Last 10 messages
                    print(f"  {msg}")
            else:
                print("  (No console messages captured)")

            await browser.close()

    except Exception as e:
        print(f"\n✗ Unexpected error during test: {e}")
        errors_captured.append({
            "test": "Test execution",
            "error_type": type(e).__name__,
            "error_message": str(e)
        })

    finally:
        # Clean up session
        print(f"\n→ Cleaning up session...")
        client.sessions.delete(session_id)
        print(f"✓ Session deleted: {session_id}")

    # Calculate metrics
    duration = time.time() - start_time
    success = len(errors_captured) >= 2  # We expect at least 2 intentional errors

    # Save results
    result_data = {
        "test": "Test 4: Selector Failure (Debugging)",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "success": success,
        "errors_captured": len(errors_captured),
        "console_messages": len(console_messages),
        "session_id": session_id,
        "live_view_url": live_view_url,
        "live_view_url": live_view_url,
        "errors": errors_captured,
        "debugging_artifacts": [
            "test4_error1_screenshot.png",
            "test4_final_state.png",
            "test4_page_content.html"
        ],
        "approach": "SDK + Playwright CDP with error handling and Live View URL",
        "estimated_cost": "$0.01 (creation) + ~$0.0004 (time)",
        "debugging_tools_used": [
            "Live View URL (real-time iframe)",
            "Playwright console capture",
            "Screenshots on error",
            "HTML content dumps"
        ]
    }

    with open("test4_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if success else '✗ FAILED'}")
    print(f"Duration: {duration:.2f}s")
    print(f"Errors Captured: {len(errors_captured)}")
    print(f"Console Messages: {len(console_messages)}")
    print(f"\nDebugging Resources:")
    print(f"  Live View: {live_view_url}")
    print(f"  Screenshots: test4_error1_screenshot.png, test4_final_state.png")
    print(f"  HTML Dump: test4_page_content.html")
    print(f"\nSession ID: {session_id}")
    print(f"Results saved: test4_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
