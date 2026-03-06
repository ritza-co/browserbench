# ritza-browser-bench

<!-- RESULTS:START -->
## Results

_Last updated: 2026-03-06_

### 1. Session lifecycle speed

| Rank | Provider | Avg total | Median total | Avg create | Avg connect | Avg goto | Avg release | Pricing |
|------|----------|-----------|--------------|------------|-------------|----------|-------------|---------|
| 1 | STEEL | 1441ms | 1412ms | 290ms | 760ms | 209ms | 181ms | $0.10/hr |
| 2 | KERNEL | 1554ms | 1551ms | 225ms | 815ms | 271ms | 243ms | $0.0000167/sec (active only, idle free) |
| 3 | BROWSERLESS | 2090ms | 2101ms | 0ms | 1665ms | 425ms | 0ms | 1 unit/30s (1,000 units/mo free) |
| 4 | ANCHORBROWSER | 3730ms | 3636ms | 1528ms | 1015ms | 315ms | 872ms | $0.05/hr + $0.01/session |
| 5 | HYPERBROWSER | 4012ms | 3643ms | 1462ms | 1892ms | 496ms | 163ms | $0.10/hr |
| 6 | BROWSERBASE | 11933ms | 2943ms | 9401ms | 1474ms | 648ms | 410ms | $0.12/hr (Developer), 1 hr/mo free |

### 2. Idle workflow survival

| Rank | Provider | Survived idle | Step 1 | Step 2 | Reconnect | Total | Cost (1-min session) |
|------|----------|--------------|--------|--------|-----------|-------|----------------------|
| 1 | KERNEL | Yes | 1602ms | 248ms | — | 62.8s | $0.00 (idle free) |
| 2 | STEEL | Yes | 1366ms | 322ms | — | 63s | ~$0.0017 |
| 3 | HYPERBROWSER | Yes | 4047ms | 439ms | — | 65.8s | ~$0.0017 |
| 4 | BROWSERBASE | Yes | 3050ms | 373ms | — | 65.5s | ~$0.0020 |
| 5 | ANCHORBROWSER | Yes | 3179ms | 265ms | — | 65.6s | ~$0.0108 (incl. $0.01 create fee) |
| 6 | BROWSERLESS | No (reconnected) | 2439ms | 435ms | 1902ms | 65.3s | 2 units (free tier) |

### 3. Stealth / bot detection

| Provider | Mode | WebDriver | Headless UA | AreYouHeadless | reCAPTCHA score | Stealth plan |
|----------|------|-----------|-------------|----------------|-----------------|--------------|
| ANCHORBROWSER | default | Clean | Clean | Clean | 0.3 | Growth tier ($2,000/mo) |
| ANCHORBROWSER | stealth | Clean | Clean | Clean | 0.3 | Growth tier ($2,000/mo) |
| BROWSERBASE | default | Clean | Clean | Clean | 0.3 | Scale plan (custom pricing) |
| BROWSERLESS | default | Detected | Detected | Detected | 0.3 | Free (stealth endpoint) |
| BROWSERLESS | stealth | Clean | Clean | Clean | — | Free (stealth endpoint) |
| HYPERBROWSER | default | Clean | Clean | Clean | 0.3 | Paid ($10/GB proxy) |
| HYPERBROWSER | stealth | Clean | Clean | Clean | 0.1 | Paid ($10/GB proxy) |
| KERNEL | default | Clean | Clean | Clean | 0.3 | Free (managed proxy included) |
| KERNEL | stealth | Clean | Clean | Clean | 0.3 | Free (managed proxy included) |
| STEEL | default | Clean | Clean | Clean | 0.3 | Paid (proxy add-on) |
| STEEL | stealth | Clean | Clean | Clean | 0.3 | Paid (proxy add-on) |
| BROWSERBASE | stealth | — | — | — | — | 403 Advanced stealth mode is only available on the Enterprise plan |

### 4. CAPTCHA solving

| Provider | Free tier | Detected | Solved | Solve time | Cost per solve |
|----------|-----------|----------|--------|------------|----------------|
| BROWSERLESS | Yes | Yes | Yes | 17.3s | 10 units/solve (~$0.02 on paid) |
| KERNEL | Yes | Yes | Yes | 38.5s | ~$0.0006/solve (GB-seconds) |
| BROWSERBASE | No | — | — | — | Developer plan ($20/mo) required |
| STEEL | No | — | — | — | Starter plan ($29/mo) required |
| HYPERBROWSER | No | — | — | — | Paid plan required |
| ANCHORBROWSER | No | — | — | — | Starter plan ($50/mo) required |

### 5. Parallel session handling

| Rank | Provider | True parallel | Overhead ratio | Sessions succeeded | Failed batches | Free tier concurrency |
|------|----------|--------------|----------------|-------------------|----------------|----------------------|
| 1 | STEEL | Yes | 0.3729 | 3 / 3 | 0 | 3 (free tier) |
| 2 | KERNEL | Yes | 0.3792 | 3 / 3 | 0 | 5 (free tier) |
| 3 | ANCHORBROWSER | Yes | 0.3444 | 3 / 3 | 0 | 5 (free tier) |
| 4 | BROWSERLESS | No (sequential) | 1.0002 | 3 / 3 | 0 | 2 (free tier) |
| 5 | HYPERBROWSER | No (sequential) | 1.0001 | 3 / 3 | 0 | 1 (free tier) |
| 6 | BROWSERBASE | No (sequential) | 1.0001 | 3 / 3 | 0 | 1 (free tier) |

<!-- RESULTS:END -->

Benchmarks for hosted browser providers. All tests run on free tiers and produce results you can verify yourself.

Providers tested: Browserless, Browserbase, Anchor, Hyperbrowser, Kernel, Steel.

## Benchmarks

### 1. Session lifecycle speed

Measures how long it takes from "I need a browser" to "I have a page open and ready to use", split into four stages:

| Stage | What it measures |
|---|---|
| `session_creation_ms` | API call to create the session (control plane overhead) |
| `session_connect_ms` | CDP handshake to establish the browser connection |
| `page_goto_ms` | Navigate to target URL and wait for DOM content to load |
| `session_release_ms` | API call to terminate the session |

10 measured runs per provider, 3 warmup runs discarded. Target URL: `https://example.com`.

**Results:** [coming soon]

## Setup

```bash
npm install
cp .env.example .env
# Fill in your API keys in .env
```

You'll need accounts (all free tier) at:
- [Browserless](https://browserless.io)
- [Browserbase](https://browserbase.com)
- [Anchor Browser](https://anchorbrowser.io)
- [Hyperbrowser](https://hyperbrowser.ai)
- [Kernel](https://onkernel.com)
- [Steel](https://steel.dev)

## Running benchmarks

Run a single provider:

```bash
npm run bench -- --provider browserless
```

Run all providers:

```bash
npm run bench -- --provider browserless,browserbase,anchorbrowser,hyperbrowser,kernel,steel
```

Results are written to `results/<provider>.jsonl`.

## Analyzing results

Requires [DuckDB](https://duckdb.org/docs/installation/).

Quick totals (avg and median total time per provider, ranked fastest to slowest):

```bash
duckdb -c ".read queries/totals.sql"
```

Full breakdown (avg, median, p95, stddev per stage per provider):

```bash
duckdb -c ".read queries/summary.sql"
```
