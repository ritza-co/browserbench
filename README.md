# ritza-browser-bench

<!-- RESULTS:START -->
## Results

_Last updated: 2026-03-06_

### 1. Session lifecycle speed

| Rank | Provider | Avg total | Median total | Avg create | Avg connect | Avg goto | Avg release |
|------|----------|-----------|--------------|------------|-------------|----------|-------------|
| 1 | STEEL | 1441ms | 1412ms | 290ms | 760ms | 209ms | 181ms |
| 2 | KERNEL | 1554ms | 1551ms | 225ms | 815ms | 271ms | 243ms |
| 3 | BROWSERLESS | 2090ms | 2101ms | 0ms | 1665ms | 425ms | 0ms |
| 4 | ANCHORBROWSER | 3730ms | 3636ms | 1528ms | 1015ms | 315ms | 872ms |
| 5 | HYPERBROWSER | 4012ms | 3643ms | 1462ms | 1892ms | 496ms | 163ms |
| 6 | BROWSERBASE | 11933ms | 2943ms | 9401ms | 1474ms | 648ms | 410ms |

### 2. Idle workflow survival

| Provider | Session survived | Step 1 | Step 2 | Reconnect | Total |
|----------|-----------------|--------|--------|-----------|-------|
| ANCHORBROWSER | Yes | 3179ms | 265ms | — | 65.6s |
| BROWSERBASE | Yes | 3050ms | 373ms | — | 65.5s |
| BROWSERLESS | No | 2439ms | 435ms | 1902ms | 65.3s |
| HYPERBROWSER | Yes | 4047ms | 439ms | — | 65.8s |
| KERNEL | Yes | 1602ms | 248ms | — | 62.8s |
| STEEL | Yes | 1366ms | 322ms | — | 63s |

### 3. Stealth / bot detection

| Provider | Mode | WebDriver | Headless UA | AreYouHeadless | reCAPTCHA score |
|----------|------|-----------|-------------|----------------|-----------------|
| ANCHORBROWSER | default | Clean | Clean | Clean | 0.3 |
| ANCHORBROWSER | stealth | Clean | Clean | Clean | 0.3 |
| BROWSERBASE | default | Clean | Clean | Clean | 0.3 |
| BROWSERLESS | default | Detected | Detected | Detected | 0.3 |
| BROWSERLESS | stealth | Clean | Clean | Clean | — |
| HYPERBROWSER | default | Clean | Clean | Clean | 0.3 |
| HYPERBROWSER | stealth | Clean | Clean | Clean | 0.1 |
| KERNEL | default | Clean | Clean | Clean | 0.3 |
| KERNEL | stealth | Clean | Clean | Clean | 0.3 |
| STEEL | default | Clean | Clean | Clean | 0.3 |
| STEEL | stealth | Clean | Clean | Clean | 0.3 |

### 4. CAPTCHA solving

| Provider | Free tier support | Detected | Solved | Solve time |
|----------|-------------------|----------|--------|------------|
| BROWSERLESS | Yes | Yes | Yes | 17.3s |
| KERNEL | Yes | Yes | Yes | 38.5s |
| HYPERBROWSER | No | — | — | — |
| ANCHORBROWSER | No | — | — | — |
| BROWSERBASE | No | — | — | — |
| STEEL | No | — | — | — |

### 5. Parallel session handling

| Rank | Provider | Avg parallel time | Overhead ratio | Avg sessions succeeded | Failed batches | Sequential mode |
|------|----------|-------------------|----------------|------------------------|----------------|-----------------|
| 1 | STEEL | 1736ms | 0.3729 | 3 / 3 | 0 | No |
| 2 | KERNEL | 2097ms | 0.3792 | 3 / 3 | 0 | No |
| 3 | ANCHORBROWSER | 4401ms | 0.3444 | 3 / 3 | 0 | No |
| 4 | BROWSERLESS | 6729ms | 1.0002 | 3 / 3 | 0 | Yes (free tier limit) |
| 5 | HYPERBROWSER | 12394ms | 1.0001 | 3 / 3 | 0 | Yes (free tier limit) |
| 6 | BROWSERBASE | 24889ms | 1.0001 | 3 / 3 | 0 | Yes (free tier limit) |

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
