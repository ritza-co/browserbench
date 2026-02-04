#!/usr/bin/env python3
"""
Test 6: Bot Detection (Stealth Mode)

Target: bot.sannysoft.com
Task: Navigate to bot detection site and check if blocked
Tests: Stealth mode / anti-detection
Platform Feature Focus: Cloudflare Web Bot Auth (Verified Bot status)
"""

import asyncio
import json
import os
import time
from anchorbrowser import Anchorbrowser
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

async def test_bot_detection(client, enable_web_bot_auth=False):
    """Test bot detection with/without Cloudflare Web Bot Auth"""

    mode = "Web Bot Auth" if enable_web_bot_auth else "Standard"
    session_start = time.time()

    # Configure session with optional web bot auth
    session_config = {
        "browser": {
            "web_bot_auth": {
                "active": enable_web_bot_auth  # Cloudflare Verified Bot
            }
        },
        "session": {
            "max_duration": 5,
            "idle_timeout": 2
        }
    }

    session = client.sessions.create(browser=session_config)
    session_id = session.data.id
    cdp_url = session.data.cdp_url
    live_view_url = session.data.live_view_url

    print(f"\n→ Testing {mode} mode...")
    print(f"  Session: {session_id[:20]}...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to bot detection test site
            await page.goto("https://bot.sannysoft.com/", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)

            # Take screenshot
            screenshot_name = f"test6_{'web_bot_auth' if enable_web_bot_auth else 'standard'}.png"
            await page.screenshot(path=screenshot_name, full_page=True)
            print(f"  ✓ Screenshot: {screenshot_name}")

            # Check for bot detection indicators
            page_content = await page.content()

            # Look for common bot detection indicators
            indicators = {
                "webdriver": "webdriver" in page_content.lower() and ("present" in page_content.lower() or "true" in page_content.lower()),
                "headless": "headless" in page_content.lower() and "true" in page_content.lower(),
                "automation": "automation" in page_content.lower() and ("detected" in page_content.lower() or "true" in page_content.lower())
            }

            detected = any(indicators.values())
            duration = time.time() - session_start

            print(f"  Result: {'✗ DETECTED' if detected else '✓ NOT DETECTED'}")
            if detected:
                print(f"    Indicators: {[k for k, v in indicators.items() if v]}")

            await browser.close()

            return {
                "mode": mode,
                "web_bot_auth_enabled": enable_web_bot_auth,
                "session_id": session_id,
        "live_view_url": live_view_url,
                "duration": duration,
                "detected": detected,
                "indicators": indicators,
                "screenshot": screenshot_name,
                "success": True
            }

    except Exception as e:
        duration = time.time() - session_start
        print(f"  ✗ Error: {str(e)[:50]}")

        return {
            "mode": mode,
            "web_bot_auth_enabled": enable_web_bot_auth,
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
    print("Test 6: Bot Detection (Stealth Mode)")
    print("=" * 60)

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    print(f"\n→ Testing bot detection in two modes:")
    print(f"  1. Standard mode (no special anti-detection)")
    print(f"  2. Web Bot Auth mode (Cloudflare Verified Bot)")

    # Test both modes
    standard_result = await test_bot_detection(client, enable_web_bot_auth=False)
    await asyncio.sleep(2)  # Brief delay between tests
    web_bot_auth_result = await test_bot_detection(client, enable_web_bot_auth=True)

    # Calculate metrics
    duration = time.time() - start_time
    both_passed = standard_result.get("success") and web_bot_auth_result.get("success")

    # Determine overall success
    # Ideally: standard mode may be detected, but web bot auth should NOT be detected
    standard_detected = standard_result.get("detected", True)
    web_bot_detected = web_bot_auth_result.get("detected", True)

    success = both_passed and not web_bot_detected

    # Save results
    result_data = {
        "test": "Test 6: Bot Detection (Stealth Mode)",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "success": success,
        "standard_mode": standard_result,
        "web_bot_auth_mode": web_bot_auth_result,
        "approach": "SDK + Playwright CDP with Cloudflare Web Bot Auth",
        "estimated_cost": "$0.02 (creation) + ~$0.00083 (time)",
        "platform_feature": "Cloudflare Verified Bot status (partnership)",
        "comparison": {
            "standard_detected": standard_detected,
            "web_bot_auth_detected": web_bot_detected,
            "web_bot_auth_advantage": standard_detected and not web_bot_detected
        }
    }

    with open("test6_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if success else '⚠️  PARTIAL' if both_passed else '✗ FAILED'}")
    print(f"Duration: {duration:.2f}s")

    print(f"\nStandard Mode:")
    print(f"  Detected: {'✗ YES' if standard_detected else '✓ NO'}")
    if standard_result.get("indicators"):
        detected_indicators = [k for k, v in standard_result["indicators"].items() if v]
        if detected_indicators:
            print(f"  Indicators: {', '.join(detected_indicators)}")

    print(f"\nWeb Bot Auth Mode (Cloudflare Verified):")
    print(f"  Detected: {'✗ YES' if web_bot_detected else '✓ NO'}")
    if web_bot_auth_result.get("indicators"):
        detected_indicators = [k for k, v in web_bot_auth_result["indicators"].items() if v]
        if detected_indicators:
            print(f"  Indicators: {', '.join(detected_indicators)}")

    if standard_detected and not web_bot_detected:
        print(f"\n✓ Web Bot Auth provides protection against bot detection!")
    elif not standard_detected and not web_bot_detected:
        print(f"\n✓ Both modes passed (no bot detection)")
    elif standard_detected and web_bot_detected:
        print(f"\n⚠️  Both modes detected as bots")

    print(f"\nScreenshots:")
    print(f"  Standard: {standard_result.get('screenshot', 'N/A')}")
    print(f"  Web Bot Auth: {web_bot_auth_result.get('screenshot', 'N/A')}")

    print(f"\nResults saved: test6_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
