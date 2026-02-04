# ritza-browser-bench

A fork of [Steel's browserbench](https://github.com/steel-dev/browserbench) adapted for testing browser automation platforms on free tiers.

## Why This Fork Exists

This fork was created for the article [Agent Experience for Browser Automation Platforms](https://ritza.co/techstackups/comparisons/browserless-vs-browserbase-vs-anchor-agent-experience/), which compares Browserless, Browserbase, and Anchor through AI coding agents.

Steel's original benchmark runs 5,000 sessions per platform to measure connection speed at scale. That's perfect for understanding production performance but impossible on free tiers that limit you to 1,000 requests per month or 1 concurrent session.

We needed benchmark results that readers could verify themselves without burning through monthly quotas in minutes. This fork adapts the original benchmark for free tier testing while maintaining the same four-stage measurement methodology.

## What Changed

**Original benchmark (Steel):**
- 5,000 measured runs per provider
- Tests: Steel, Kernel, Browserbase, Hyperbrowser, Anchor
- Run from AWS EC2 in us-east-1
- Focus: production-scale performance

**This fork (Ritza):**
- 10 measured runs + 3 warmup runs per provider
- Added: Browserless (wasn't in original)
- Tests: Browserless, Browserbase, Anchor
- Run from any machine with free tier API keys
- Focus: connection speed anyone can verify + real-world feature tests

**Additional changes:**
- Added Browserless provider implementation
- Simplified rate limiting logic for smaller test runs
- Added 6 real-world test scenarios in [ritza-real-world-tests/](ritza-real-world-tests/)
- Updated documentation for free tier constraints

## Real-World Tests

Beyond connection speed, we added six practical tests that developers actually care about:

1. **Product search** - Extract structured data from e-commerce sites
2. **Multi-page navigation** - Click through multiple pages
3. **CAPTCHA handling** - Test built-in CAPTCHA solving
4. **Error recovery** - Debugging tools when things break
5. **Parallel execution** - Running multiple browsers simultaneously
6. **Bot detection** - Stealth mode and anti-detection

See [ritza-real-world-tests/](ritza-real-world-tests/) for the test implementations.

## Credit to Original Creators

The core benchmark architecture, measurement methodology, and most of the codebase comes from [Steel's browserbench](https://github.com/steel-dev/browserbench).

**Original work by Steel:**
- All provider interface patterns (`src/providers/`)
- Benchmark runner logic (`src/benchmark.ts`)
- DuckDB analysis queries (`queries/`)
- Four-stage timing measurement
- CLI argument parsing
- Result output format (JSONL)

**Our additions (Ritza):**
- Browserless provider implementation (`src/providers/browserless.ts`)
- Reduced run counts (5,000 → 10) for free tier testing
- Real-world test scenarios (`ritza-real-world-tests/`)
- Updated documentation for free tier focus
- This README

## Quick Start (Free Tier)

1. **Requirements**
   - Node.js ≥ 18
   - Free tier API keys for the platforms you want to test

2. **Install**
   ```bash
   git clone https://github.com/ritza-co/ritza-browser-bench
   cd ritza-browser-bench
   npm install
   ```

3. **Configure** (create `.env` file)
   ```bash
   # Browserless
   BROWSERLESS_API_KEY=your_key_here

   # Browserbase
   BROWSERBASE_API_KEY=your_key_here
   BROWSERBASE_PROJECT_ID=your_project_id_here

   # Anchor
   ANCHORBROWSER_API_KEY=your_key_here
   ```

4. **Run speed benchmark** (10 runs per platform)
   ```bash
   npm run build
   npm run bench -- --provider browserless,browserbase,anchor --runs 10
   ```

5. **Run real-world tests**
   ```bash
   cd ritza-real-world-tests/browserless
   npm install
   npm test
   ```

## Results

Our free tier benchmark results:

| Platform | Total Time | Session Creation | CDP Connection | Success Rate | Variance |
|----------|------------|------------------|----------------|--------------|----------|
| **Browserless** | 4,264ms | 0ms | 3,085ms | 10/10 | 18% |
| **Browserbase** | 11,886ms | 5,838ms | 2,995ms | 10/10 | 21% |
| **Anchor** | 13,121ms | 5,801ms | 2,689ms | 10/10 | 38% |

See the [full article](https://ritza.co/techstackups/comparisons/browserless-vs-browserbase-vs-anchor-agent-experience/) for detailed analysis of these results and real-world test outcomes.

## What Gets Measured

Each iteration records four timing stages (milliseconds):

- `session_creation_ms` - API call to create browser session
- `session_connect_ms` - Playwright CDP handshake
- `page_goto_ms` - Navigate to URL (wait for `domcontentloaded`)
- `session_release_ms` - API call to terminate session

Results are written to `results/{provider}.jsonl` in JSON Lines format.

## Analyzing Results with DuckDB

Query the raw JSONL files directly:

```bash
# Quick averages per provider
duckdb -c ".read queries/simple.sql"

# Full breakdown with percentiles
duckdb -c ".read queries/full.sql"
```

## CLI Options

- `--provider` - Platform names (comma-separated): `browserless`, `browserbase`, `anchor`
- `--runs` - Number of measured iterations (default: 5, recommend: 10 for free tier)
- `--url` - First page to load (default: `https://google.com/`)
- `--out` - Output path (default: `results/{provider}.jsonl`)
- `--rate` - Maximum sessions per minute (default: unlimited)

## Free Tier Constraints

**Browserless:**
- 1,000 units/month
- 10 concurrent sessions (rate limiting observed at 3)

**Browserbase:**
- 1 browser hour/month
- 1 concurrent session

**Anchor:**
- $5 in free credits
- 5 concurrent sessions

Running 10 iterations uses minimal quota on all platforms (under 5 minutes total runtime).

## Reproducing Steel's Original Results

For production-scale testing, use [Steel's original benchmark](https://github.com/steel-dev/browserbench):

```bash
git clone https://github.com/steel-dev/browserbench
cd browserbench
npm install
npm run build
npm run bench -- --provider steel,kernel,browserbase --runs 5000
```

Their results show averages over 5,000 runs from AWS EC2:
- Kernel: 794ms
- Steel: 894ms
- Browserbase: 2,967ms
- Anchor: 8,001ms

## License

MIT (same as [original](https://github.com/steel-dev/browserbench))

## Links

- **Original benchmark**: https://github.com/steel-dev/browserbench
- **Full article**: [Agent Experience for Browser Automation Platforms](https://ritza.co/techstackups/comparisons/browserless-vs-browserbase-vs-anchor-agent-experience/)
- **Ritza**: https://ritza.co
