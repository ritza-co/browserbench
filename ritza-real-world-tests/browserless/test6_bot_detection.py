#!/usr/bin:env python3
"""
Test 6: Bot Detection (Stealth Mode)
Goal: Test with and without stealth mode to see anti-detection capabilities
Platform: Browserless (Playwright + CDP with Stealth)
Target: bot.sannysoft.com (comprehensive bot detection test site)
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

NORMAL_ENDPOINT = f"wss://production-sfo.browserless.io?token={TOKEN}"
STEALTH_ENDPOINT = f"wss://production-sfo.browserless.io/stealth?token={TOKEN}"

def test_bot_detection(endpoint_name, endpoint_url):
    """
    Test bot detection on a given endpoint

    Args:
        endpoint_name: Name of the endpoint (normal/stealth)
        endpoint_url: WebSocket URL to connect to

    Returns:
        dict: Detection results
    """

    start_time = time.time()

    print(f"\nTesting {endpoint_name} mode...")

    try:
        with sync_playwright() as p:
            # Connect to Browserless
            browser = p.chromium.connect_over_cdp(endpoint_url)

            # Handle context/page differences between normal and stealth
            if "stealth" in endpoint_url:
                context = browser.contexts[0]
                page = context.pages[0]
            else:
                context = browser.new_context()
                page = context.new_page()

            # Navigate to bot detection test site
            page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=30000)

            # Wait for page to load completely
            page.wait_for_timeout(2000)

            # Take screenshot
            screenshot_path = f"test6_{endpoint_name}_detection.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  Screenshot saved: {screenshot_path}")

            # Analyze detection indicators
            content = page.content()

            # Check for common bot detection indicators
            detections = {}

            # WebDriver detection
            if "WebDriver: present" in content or "WebDriver</b>: present" in content:
                detections['webdriver'] = 'DETECTED'
            elif "WebDriver: not detected" in content or "WebDriver</b>: not detected" in content:
                detections['webdriver'] = 'PASSED'
            else:
                detections['webdriver'] = 'UNKNOWN'

            # Headless detection
            if "Chrome: Headless" in content or "Headless</b>: Headless" in content:
                detections['headless'] = 'DETECTED'
            elif "Chrome: not headless" in content or "Headless</b>: not headless" in content:
                detections['headless'] = 'PASSED'
            else:
                detections['headless'] = 'UNKNOWN'

            # Check for "User-Agent" presence
            if "User-Agent" in content:
                detections['user_agent'] = 'PRESENT'

            browser.close()

            duration = time.time() - start_time

            # Determine overall status
            is_detected = (detections.get('webdriver') == 'DETECTED' or
                          detections.get('headless') == 'DETECTED')

            status = "DETECTED" if is_detected else "PASSED"
            print(f"  Status: {status}")
            print(f"  Detections: {detections}")
            print(f"  Duration: {duration:.2f}s")

            return {
                'endpoint': endpoint_name,
                'success': True,
                'detected': is_detected,
                'detections': detections,
                'duration': duration,
                'screenshot': screenshot_path
            }

    except Exception as e:
        duration = time.time() - start_time
        print(f"  FAILED: {type(e).__name__}: {e}")

        return {
            'endpoint': endpoint_name,
            'success': False,
            'error': str(e),
            'duration': duration
        }

def run_test():
    """Run bot detection tests on both normal and stealth endpoints"""

    print("Testing bot detection capabilities...")

    results = []

    # Test normal mode
    normal_result = test_bot_detection("normal", NORMAL_ENDPOINT)
    results.append(normal_result)

    # Wait between tests to avoid rate limiting
    print("\nWaiting 5 seconds before next test...")
    time.sleep(5)

    # Test stealth mode
    stealth_result = test_bot_detection("stealth", STEALTH_ENDPOINT)
    results.append(stealth_result)

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON:")
    print("=" * 60)

    for result in results:
        if result['success']:
            status = "DETECTED" if result['detected'] else "PASSED"
            print(f"{result['endpoint'].capitalize()} Mode: {status}")
            for key, value in result['detections'].items():
                print(f"  {key}: {value}")
        else:
            print(f"{result['endpoint'].capitalize()} Mode: FAILED - {result.get('error')}")

    # Overall assessment
    normal_detected = results[0].get('detected', True) if results[0].get('success') else None
    stealth_detected = results[1].get('detected', True) if results[1].get('success') else None

    overall_success = False
    if normal_detected is not None and stealth_detected is not None:
        if normal_detected and not stealth_detected:
            print("\n✓ SUCCESS: Stealth mode successfully bypassed bot detection")
            overall_success = True
        elif not normal_detected and not stealth_detected:
            print("\n✓ PARTIAL SUCCESS: Both modes passed (bot detection not triggered)")
            overall_success = True
        else:
            print("\n✗ FAILED: Stealth mode did not bypass bot detection")

    return {
        'success': overall_success,
        'results': results,
        'api_method': 'Playwright + CDP',
        'endpoints_tested': ['normal', 'stealth'],
        'features_used': [
            'Normal CDP endpoint',
            'Stealth CDP endpoint',
            'Bot detection bypass',
            'Anti-fingerprinting'
        ],
        'test_site': 'bot.sannysoft.com'
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Test 6: Bot Detection (Stealth Mode)")
    print("Platform: Browserless (Playwright + CDP)")
    print("=" * 60)

    result = run_test()

    # Save results
    output_file = "test6_results.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    print(f"Overall Status: {'PASSED' if result['success'] else 'FAILED'}")

    print("\n" + "=" * 60)
    print("Test demonstrates:")
    print("- Normal vs stealth mode comparison")
    print("- Bot detection bypass capabilities")
    print("- Anti-fingerprinting features")
    print("- Real-world stealth effectiveness")
    print("=" * 60)
