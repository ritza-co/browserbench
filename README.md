# ritza-browser-bench

<!-- RESULTS:START -->
## Results

_Last updated: 2026-03-05_

### 1. Session lifecycle speed

| Rank | Provider | Avg total | Median total | Avg create | Avg connect | Avg goto | Avg release |
|------|----------|-----------|--------------|------------|-------------|----------|-------------|
| 1 | STEEL | 3298ms | 3125ms | 632ms | 1682ms | 479ms | 505ms |
| 2 | BROWSERLESS | 4200ms | 4246ms | 0ms | 3580ms | 620ms | 0ms |
| 3 | KERNEL | 4393ms | 4159ms | 566ms | 2693ms | 528ms | 605ms |
| 4 | HYPERBROWSER | 5163ms | 5004ms | 1780ms | 2378ms | 608ms | 397ms |
| 5 | ANCHORBROWSER | 10396ms | 10380ms | 3538ms | 3287ms | 539ms | 3033ms |
| 6 | BROWSERBASE | 12119ms | 7536ms | 5419ms | 3353ms | 1012ms | 2336ms |

### 2. Idle workflow survival

| Provider | Session survived | Step 1 | Step 2 | Reconnect | Total |
|----------|-----------------|--------|--------|-----------|-------|
| ANCHORBROWSER | Yes | 8598ms | 621ms | — | 75s |
| BROWSERBASE | Yes | 5902ms | 639ms | — | 71.3s |
| BROWSERLESS | No | 4364ms | 656ms | 2810ms | 69.2s |
| HYPERBROWSER | Yes | 5612ms | 601ms | — | 68.9s |
| KERNEL | Yes | 3991ms | 553ms | — | 67s |
| STEEL | No | 4493ms | 399ms | 2976ms | 69.6s |

### 3. Stealth / bot detection

| Provider | Mode | WebDriver | Headless UA | AreYouHeadless | reCAPTCHA score |
|----------|------|-----------|-------------|----------------|-----------------|
| ANCHORBROWSER | default | Clean | Clean | Clean | 0.1 |
| BROWSERBASE | default | Clean | Clean | Clean | 0.3 |
| BROWSERLESS | default | Detected | Detected | Detected | 0.3 |
| BROWSERLESS | stealth | Clean | Clean | Clean | 0.3 |
| HYPERBROWSER | default | Clean | Clean | Clean | 0.1 |
| HYPERBROWSER | stealth | Clean | Clean | Clean | 0.1 |
| KERNEL | default | Clean | Clean | Clean | 0.1 |
| KERNEL | stealth | Clean | Clean | Clean | 0.3 |
| STEEL | default | Clean | Clean | Clean | 0.3 |
| STEEL | stealth | Clean | Clean | Clean | 0.3 |

### 4. CAPTCHA solving

| Provider | Free tier support | Detected | Solved | Solve time |
|----------|-------------------|----------|--------|------------|
| BROWSERLESS | Yes | Yes | Yes | 38.6s |
| KERNEL | Yes | Yes | Yes | 40.7s |
| BROWSERBASE | No | — | — | — |
| STEEL | No | — | — | — |
| ANCHORBROWSER | No | — | — | — |
| HYPERBROWSER | No | — | — | — |

### 5. Parallel session handling

| Rank | Provider | Avg parallel time | Overhead ratio | Avg sessions succeeded | Failed batches | Sequential mode |
|------|----------|-------------------|----------------|------------------------|----------------|-----------------|
| 1 | STEEL | 3955ms | 0.3394 | 3 / 3 | 0 | No |
| 2 | KERNEL | 4280ms | 0.3553 | 3 / 3 | 0 | No |
| 3 | ANCHORBROWSER | 9957ms | 0.3822 | 3 / 3 | 0 | No |
| 4 | BROWSERLESS | 13707ms | 1.0001 | 3 / 3 | 0 | Yes (free tier limit) |
| 5 | HYPERBROWSER | 21382ms | 1.0001 | 3 / 3 | 0 | Yes (free tier limit) |
| 6 | BROWSERBASE | 21903ms | 1.0006 | 0 / 3 | **3** | Yes (free tier limit) |

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
