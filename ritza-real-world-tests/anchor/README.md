# Anchor Phase 2 Feature Tests

**Test Date:** 2026-02-02
**Platform:** Anchor Browser (anchorbrowser.io)
**Free Tier:** $5 credits/month, 5 concurrent sessions

## Test Suite Overview

This directory contains 6 feature-focused tests designed to evaluate Anchor's capabilities for real-world browser automation scenarios.

### The 6 Tests

1. **Test 1: Product Search & Extract** (`test1_product_search.py`)
   - **Target:** books.toscrape.com
   - **Task:** Extract first 10 book titles and prices
   - **Tests:** Basic navigation + data extraction
   - **Anchor Feature:** Standard Playwright scraping (baseline)

2. **Test 2: Multi-Page Navigation** (`test2_navigation.py`)
   - **Target:** books.toscrape.com (catalog → detail page)
   - **Task:** Navigate from listing to product detail, extract data
   - **Tests:** Multi-step navigation stability
   - **Anchor Feature:** Session stability across page transitions

3. **Test 3: CAPTCHA Challenge** (`test3_captcha.py`)
   - **Target:** Google reCAPTCHA demo
   - **Task:** Navigate and solve CAPTCHA
   - **Tests:** Built-in CAPTCHA solving
   - **Anchor Feature:** Vision-based CAPTCHA solver with proxy
   - **⚠️ Cost:** Uses proxy ($8/GB) - asks for confirmation before running

4. **Test 4: Selector Failure (Debugging)** (`test4_selector_failure.py`)
   - **Target:** books.toscrape.com with broken selectors
   - **Task:** Trigger errors and test debugging tools
   - **Tests:** Debugging tools when automation breaks
   - **Anchor Feature:** Live View URL (real-time iframe)

5. **Test 5: Parallel Product Lookups** (`test5_parallel.py`)
   - **Target:** books.toscrape.com (3 categories simultaneously)
   - **Task:** Scrape 3 categories in parallel
   - **Tests:** Concurrent session handling
   - **Anchor Feature:** 5 concurrent sessions (vs 10 for Browserless, 1 for Browserbase)

6. **Test 6: Bot Detection (Stealth Mode)** (`test6_bot_detection.py`)
   - **Target:** bot.sannysoft.com
   - **Task:** Test standard vs Web Bot Auth modes
   - **Tests:** Anti-detection capabilities
   - **Anchor Feature:** Cloudflare Web Bot Auth (Verified Bot status)

## Setup

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### Environment Variables
Create a `.env` file with your Anchor API key:
```
ANCHOR_API_KEY=sk-your-api-key-here
```

## Running Tests

### Run Individual Test
```bash
cd code/phase2-tests/anchor/
python test1_product_search.py
```

### Run All Tests (Recommended Order)
```bash
# Cheapest/safest tests first, expensive test (CAPTCHA) last
python test1_product_search.py  # $0.01
python test4_selector_failure.py  # $0.01
python test2_navigation.py  # $0.01
python test6_bot_detection.py  # $0.02
python test5_parallel.py  # $0.04
python test3_captcha.py  # $0.02+ (asks for confirmation, uses proxy)
```

### Expected Total Cost
- **Without CAPTCHA test:** ~$0.09 (1.8% of $5 allowance)
- **With CAPTCHA test:** ~$0.11-0.15 (2.2-3% of allowance)

## Expected Results

Based on Phase 1 benchmark and research:

| Test | Expected Result | Key Insight |
|------|----------------|-------------|
| Test 1 | ✅ Pass (slower than Browserless) | Baseline performance check |
| Test 2 | ✅ Pass | Multi-step workflows should work |
| Test 3 | ✅ Pass (with proxy) | CAPTCHA solver on free tier |
| Test 4 | ✅ Pass | Live View URL available for debugging |
| Test 5 | ✅ Pass (~2-3x speedup) | 5 concurrent sessions (middle ground) |
| Test 6 | ✅ Pass with Web Bot Auth | Cloudflare partnership advantage |

## Anchor-Specific Features Tested

### 1. Natural Language Extraction (NOT TESTED)
- AI-powered data extraction with $0.01/step cost
- Planned for future testing if time/credits permit
- Would simplify Test 1 implementation

### 2. CAPTCHA Solving (Test 3)
- Vision-based solver with extension fallbacks
- Requires proxy to be enabled
- Free tier includes CAPTCHA solving (unlike Browserbase)

### 3. Cloudflare Web Bot Auth (Test 6)
- Partnership for Verified Bot status
- Should bypass Cloudflare protection
- Unique to Anchor platform

### 4. Live View URL (Test 4)
- Real-time iframe embedding
- Available on free tier
- Useful for debugging and monitoring

### 5. 5 Concurrent Sessions (Test 5)
- Middle ground: Better than Browserbase (1), less than Browserless (10)
- Should show ~2-3x speedup for parallel workloads

## Cost Tracking

Anchor uses credit-based pricing:
- **Browser creation:** $0.01 per instance
- **Browser usage:** $0.05 per hour
- **Proxy data:** $8 per GB (only if proxy enabled)
- **AI steps:** $0.01 per step (natural language features)

**Free tier:** $5/month = ~500 short sessions

## Output Files

Each test produces:
- `test{N}_results.json` - Test results and metrics
- `test{N}_*.png` - Screenshots
- `test{N}_*.html` - HTML dumps (Test 4)

## Comparison Notes

### vs Browserless
- ❌ Slower base performance (13.1s vs 4.2s in Phase 1)
- ❌ Fewer concurrent sessions (5 vs 10)
- ✅ Cloudflare Web Bot Auth (unique to Anchor)
- ✅ Natural language extraction (unique to Anchor)
- ✅ Live View URL available

### vs Browserbase
- ❌ Slower base performance (13.1s vs 11.9s in Phase 1)
- ✅ More concurrent sessions (5 vs 1)
- ✅ CAPTCHA solving on free tier (Browserbase requires $20/mo)
- ✅ Cloudflare Web Bot Auth (unique to Anchor)
- ❌ No session replay like Browserbase (unclear if available)

### Cost Model
- **Anchor:** Credit-based ($5 = ~500 sessions)
- **Browserless:** Time-based (1,000 units = ~30 min)
- **Browserbase:** Time-based (60 min total)

## Known Limitations

1. **Low Discoverability:** Only 8% in discovery phase (vs 75% for Browserless)
2. **Slowest Performance:** 13.1s average in Phase 1 (vs 4.2s for Browserless)
3. **High Variance:** 38% variance in Phase 1 benchmark
4. **Credit Model Complexity:** More complex than simple time-based billing

## Platform Strengths

1. **AI-First Design:** Natural language extraction (not tested in Phase 2)
2. **Legitimate Bot Access:** Cloudflare partnership = fewer blocks
3. **Authentication Focus:** Browser profiles, SSO, MFA support (not tested)
4. **Hybrid Approach:** Deterministic code + runtime AI adaptation

## Next Steps

After completing tests:
1. Compare results to Browserless and Browserbase
2. Document credit consumption
3. Create Phase 2 comparison summary
4. Analyze where Anchor excels/struggles
5. Make platform recommendations

## Research Documents

- `/research/phase2-anchor-implementation-notes.md` - Full implementation research
- `/research/anchor-features.md` - Complete feature list
- `/research/phase1-benchmark-results.md` - Speed benchmark results

---

**Status:** Ready for testing
**Estimated Runtime:** ~5-7 minutes for all tests
**Estimated Cost:** $0.11-0.15 (2.2-3% of monthly allowance)
