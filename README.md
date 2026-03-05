# ritza-browser-bench

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
