#!/usr/bin/env python3
"""
Test 3: CAPTCHA Challenge

Target: Google reCAPTCHA demo
Task: Navigate and attempt to solve CAPTCHA
Tests: Built-in CAPTCHA solving (platform-specific feature)
Platform Feature Focus: Anchor's vision-based CAPTCHA solver with proxy
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
    print("Test 3: CAPTCHA Challenge")
    print("=" * 60)
    print("\n⚠️  WARNING: This test uses proxy ($8/GB) and may consume credits")

    # Ask for confirmation
    response = input("\nProceed with CAPTCHA test? (yes/no): ").strip().lower()
    if response not in ["yes", "y"]:
        print("Test cancelled by user.")
        return

    # Initialize Anchor client
    client = Anchorbrowser(api_key=os.getenv("ANCHOR_API_KEY"))

    # Enable CAPTCHA solver (requires proxy to be active)
    session_config = {
        "browser": {
            "captcha_solver": {
                "active": True  # Enable vision-based CAPTCHA solving
            }
        },
        "session": {
            "proxy": {
                "active": True,  # Required for CAPTCHA solver
                "type": "anchor_residential",
                "country_code": "us"
            },
            "max_duration": 5,
            "idle_timeout": 2
        }
    }

    session = client.sessions.create(browser=session_config)
    session_id = session.data.id
    cdp_url = session.data.cdp_url
    live_view_url = session.data.live_view_url

    print(f"\n✓ Session created with CAPTCHA solver enabled: {session_id}")
    print(f"  Proxy: Enabled (anchor_residential, us)")

    captcha_detected = False
    captcha_solved = False
    solve_duration = 0

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            print(f"\n→ Navigating to Google reCAPTCHA demo...")
            await page.goto("https://www.google.com/recaptcha/api2/demo", timeout=30000)

            # Wait for CAPTCHA iframe to load
            await page.wait_for_selector("iframe[src*='recaptcha']", timeout=10000)
            print(f"✓ CAPTCHA page loaded")

            # Take screenshot before solve attempt
            await page.screenshot(path="test3_captcha_page.png")
            print(f"✓ Screenshot saved: test3_captcha_page.png")

            captcha_detected = True
            print(f"\n→ CAPTCHA detected, waiting for Anchor to solve...")
            print(f"  (This may take 15-30 seconds...)")

            solve_start = time.time()

            # Wait for CAPTCHA to be solved
            # Anchor should automatically detect and solve it
            await asyncio.sleep(20)  # Give CAPTCHA solver time to work

            solve_duration = time.time() - solve_start

            # Try to submit the form
            print(f"\n→ Attempting to submit form...")
            try:
                await page.click("#recaptcha-demo-submit", timeout=5000)
                await asyncio.sleep(3)  # Wait for response
            except Exception as e:
                print(f"  Note: Submit click failed or timed out: {e}")

            # Check if CAPTCHA was solved by looking for success indicators
            page_content = await page.content()
            captcha_solved = "Verification Success" in page_content or "verification was successful" in page_content.lower()

            # Take screenshot after solve attempt
            await page.screenshot(path="test3_captcha_solved.png" if captcha_solved else "test3_captcha_unsolved.png")
            screenshot_name = "test3_captcha_solved.png" if captcha_solved else "test3_captcha_unsolved.png"
            print(f"✓ Screenshot saved: {screenshot_name}")

            if captcha_solved:
                print(f"\n✓ CAPTCHA SOLVED in {solve_duration:.2f}s")
                print(f"  Verification successful!")
            else:
                print(f"\n⚠️  CAPTCHA NOT SOLVED after {solve_duration:.2f}s")
                print(f"  Either solver didn't trigger or solve failed")

            await browser.close()

    except Exception as e:
        print(f"\n✗ Error during test: {e}")

    finally:
        # Clean up session
        print(f"\n→ Cleaning up session...")
        client.sessions.delete(session_id)
        print(f"✓ Session deleted: {session_id}")

    # Calculate metrics
    duration = time.time() - start_time
    success = captcha_detected and captcha_solved

    # Save results
    result_data = {
        "test": "Test 3: CAPTCHA Challenge",
        "platform": "Anchor",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": round(duration, 2),
        "success": success,
        "captcha_detected": captcha_detected,
        "captcha_solved": captcha_solved,
        "solve_duration_seconds": round(solve_duration, 2) if captcha_detected else 0,
        "session_id": session_id,
        "live_view_url": live_view_url,
        "approach": "SDK + Playwright CDP with vision-based CAPTCHA solver + proxy",
        "estimated_cost": "$0.01 (creation) + ~$0.0008 (time) + proxy data transfer",
        "notes": "Uses proxy ($8/GB) and CAPTCHA solver. Auto-detection and solving expected."
    }

    with open("test3_results.json", "w") as f:
        json.dump(result_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Status: {'✓ PASSED' if success else '⚠️  PARTIAL' if captcha_detected else '✗ FAILED'}")
    print(f"Duration: {duration:.2f}s")
    print(f"CAPTCHA Detected: {'✓' if captcha_detected else '✗'}")
    print(f"CAPTCHA Solved: {'✓' if captcha_solved else '✗'}")
    if captcha_detected:
        print(f"Solve Duration: {solve_duration:.2f}s")
    print(f"Session ID: {session_id}")
    print(f"Results saved: test3_results.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
