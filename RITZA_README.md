# Ritza's Browser Automation Platform Tests

This directory contains Ritza's extensions to Steel's browserbench, testing three browser automation platforms: Browserbase, Browserless, and Anchor.

## What's Added

```
browserbench/
├── ritza-speed-benchmarks/     # Modified speed benchmarks
├── ritza-real-world-tests/     # Real-world feature tests
└── ritza-results/              # All test results
```

The original Steel benchmark files (`src/`, `queries/`, `results/`) remain unchanged.

## Ritza Speed Benchmarks

Modified version of Steel's benchmark to include Browserless and Anchor platforms.

**Location:** `ritza-speed-benchmarks/`

**Changes from original:**
- Added Browserless provider
- Added Anchor provider (aliased as "anchorbrowser")
- Reduced from 5,000 to 10 measured runs (+ 3 warmup)
- Simplified rate limiting logic

**Running:**
```bash
cd ritza-speed-benchmarks
npm install
npm run bench
```

Results saved to `ritza-results/speed-benchmarks/`:
- `browserbase.jsonl`
- `browserless.jsonl`
- `anchorbrowser.jsonl`

## Ritza Real-World Tests

Six practical tests implemented for each platform (18 tests total).

**Location:** `ritza-real-world-tests/{platform}/`

**Tests:**
1. **Product Search** - Search Amazon for "mechanical keyboard"
2. **Multi-Page Navigation** - Navigate Wikipedia pages
3. **CAPTCHA Handling** - Detect and respond to CAPTCHAs
4. **Debugging/Error Recovery** - Handle selector failures
5. **Parallel Execution** - Run multiple browsers concurrently
6. **Bot Detection Avoidance** - Test stealth capabilities

**Running:**
```bash
cd ritza-real-world-tests/browserbase
pip install -r requirements.txt
python test1_product_search.py
python test2_navigation.py
# ... etc
```

Results saved to `ritza-results/real-world-tests/`:
- `{platform}_test1_results.json`
- `{platform}_test2_results.json`
- ... etc (18 files total)

## Requirements

**Speed Benchmarks:**
- Node.js 18+
- API keys for all three platforms

**Real-World Tests:**
- Python 3.8+
- playwright (Browserbase, Anchor)
- requests (Browserless)

**API Keys (set as environment variables):**
- `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID`
- `BROWSERLESS_API_KEY`
- `ANCHOR_API_KEY`

## Related Article

These tests accompany the article **"Browser Automation Platforms: An Agent Experience Comparison"**.

GitHub: https://github.com/ritza-co/browserbench

## License

MIT
