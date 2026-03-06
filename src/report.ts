/**
 * report.ts — reads benchmark result files, queries with DuckDB, and updates
 * the Results section in README.md.
 *
 * Usage:
 *   npm run report
 *
 * Only updates the README if all providers succeeded for that benchmark.
 * Skips any benchmark whose result files are missing or contain errors.
 */

import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const README = path.resolve("README.md");
const RESULTS_DIR = path.resolve("results");

// Marker comments that wrap the auto-generated results section in the README
const START_MARKER = "<!-- RESULTS:START -->";
const END_MARKER = "<!-- RESULTS:END -->";

// ---- DuckDB helpers --------------------------------------------------------

function duckdb(sql: string): string {
  try {
    return execSync(`duckdb -c "${sql.replace(/"/g, '\\"')}"`, {
      encoding: "utf-8",
      cwd: path.resolve("."),
    }).trim();
  } catch {
    return "";
  }
}

function duckdbJson(sql: string): Record<string, unknown>[] {
  try {
    const raw = execSync(
      `duckdb -json -c "${sql.replace(/"/g, '\\"').replace(/\n/g, " ")}"`,
      { encoding: "utf-8", cwd: path.resolve(".") }
    ).trim();
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

// ---- File checks -----------------------------------------------------------

function resultsExist(pattern: string): boolean {
  try {
    const files = fs.readdirSync(RESULTS_DIR).filter((f) =>
      new RegExp(pattern).test(f)
    );
    return files.length > 0;
  } catch {
    return false;
  }
}

// ---- Benchmark 1: Session lifecycle ----------------------------------------

function bench1Table(): string | null {
  if (!resultsExist("^(?!idle-|stealth|captcha|parallel-).*\\.jsonl$")) return null;

  const rows = duckdbJson(`
    WITH data AS (
      SELECT * FROM read_json_auto('results/*.jsonl', format='newline_delimited')
      WHERE provider IS NOT NULL
        AND session_creation_ms IS NOT NULL
        AND session_connect_ms IS NOT NULL
        AND page_goto_ms IS NOT NULL
    ),
    pre AS (
      SELECT
        provider,
        success,
        try_cast(session_creation_ms AS DOUBLE) AS session_creation_ms,
        try_cast(session_connect_ms  AS DOUBLE) AS session_connect_ms,
        try_cast(page_goto_ms        AS DOUBLE) AS page_goto_ms,
        try_cast(session_release_ms  AS DOUBLE) AS session_release_ms
      FROM data WHERE success = true
    )
    SELECT
      provider,
      COUNT(*) AS runs,
      ROUND(AVG(session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms), 0) AS avg_total_ms,
      ROUND(MEDIAN(session_creation_ms + session_connect_ms + page_goto_ms + session_release_ms), 0) AS median_total_ms,
      ROUND(AVG(session_creation_ms), 0) AS avg_create_ms,
      ROUND(AVG(session_connect_ms), 0)  AS avg_connect_ms,
      ROUND(AVG(page_goto_ms), 0)        AS avg_goto_ms,
      ROUND(AVG(session_release_ms), 0)  AS avg_release_ms
    FROM pre
    GROUP BY provider
    ORDER BY avg_total_ms ASC
  `);

  if (!rows.length) return null;

  const sessionCost: Record<string, string> = {
    KERNEL:        "$0.0000167/sec (active only, idle free)",
    STEEL:         "$0.10/hr",
    HYPERBROWSER:  "$0.10/hr",
    BROWSERLESS:   "1 unit/30s (1,000 units/mo free)",
    BROWSERBASE:   "$0.12/hr (Developer), 1 hr/mo free",
    ANCHORBROWSER: "$0.05/hr + $0.01/session",
  };

  const header = `| Rank | Provider | Avg total | Median total | Avg create | Avg connect | Avg goto | Avg release | Pricing |`;
  const divider = `|------|----------|-----------|--------------|------------|-------------|----------|-------------|---------|`;
  const lines = rows.map((r, i) =>
    `| ${i + 1} | ${r.provider} | ${r.avg_total_ms}ms | ${r.median_total_ms}ms | ${r.avg_create_ms}ms | ${r.avg_connect_ms}ms | ${r.avg_goto_ms}ms | ${r.avg_release_ms}ms | ${sessionCost[String(r.provider)] ?? "—"} |`
  );

  return [header, divider, ...lines].join("\n");
}

// ---- Benchmark 2: Idle workflow --------------------------------------------

function bench2Table(): string | null {
  if (!resultsExist("^idle-.*\\.jsonl$")) return null;

  const rows = duckdbJson(`
    SELECT
      provider,
      session_survived,
      success,
      ROUND(try_cast(step1_ms AS DOUBLE), 0) AS step1_ms,
      ROUND(try_cast(reconnect_ms AS DOUBLE), 0) AS reconnect_ms,
      ROUND(try_cast(step2_ms AS DOUBLE), 0) AS step2_ms,
      ROUND(try_cast(total_ms AS DOUBLE) / 1000.0, 1) AS total_s,
      error_stage
    FROM read_json_auto('results/idle-*.jsonl', format='newline_delimited')
    ORDER BY provider
  `);

  if (!rows.length) return null;

  const hasErrors = rows.some((r) => !r.success);
  if (hasErrors) {
    console.error(`[report] benchmark 2 has errors — skipping`);
    return null;
  }

  const idleCost: Record<string, string> = {
    KERNEL:        "$0.00 (idle free)",
    STEEL:         "~$0.0017",
    HYPERBROWSER:  "~$0.0017",
    BROWSERLESS:   "2 units (free tier)",
    BROWSERBASE:   "~$0.0020",
    ANCHORBROWSER: "~$0.0108 (incl. $0.01 create fee)",
  };

  // Rank by cost: free idle first, then by step1 speed, non-survivors last
  const costRank: Record<string, number> = {
    KERNEL: 0, STEEL: 1, HYPERBROWSER: 2, BROWSERLESS: 3, BROWSERBASE: 4, ANCHORBROWSER: 5,
  };
  const sorted = [...rows].sort((a, b) => {
    const aS = a.session_survived === true ? 0 : 1;
    const bS = b.session_survived === true ? 0 : 1;
    if (aS !== bS) return aS - bS;
    const aCost = costRank[String(a.provider)] ?? 99;
    const bCost = costRank[String(b.provider)] ?? 99;
    return aCost - bCost;
  });

  const header = `| Rank | Provider | Survived idle | Step 1 | Step 2 | Reconnect | Total | Cost (1-min session) |`;
  const divider = `|------|----------|--------------|--------|--------|-----------|-------|----------------------|`;
  const lines = sorted.map((r, i) => {
    const survived = r.session_survived === true ? "Yes" : r.session_survived === false ? "No (reconnected)" : "—";
    const reconnect = r.reconnect_ms != null ? `${r.reconnect_ms}ms` : "—";
    const cost = idleCost[String(r.provider)] ?? "—";
    return `| ${i + 1} | ${r.provider} | ${survived} | ${r.step1_ms}ms | ${r.step2_ms}ms | ${reconnect} | ${r.total_s}s | ${cost} |`;
  });

  return [header, divider, ...lines].join("\n");
}

// ---- Benchmark 3: Stealth --------------------------------------------------

function bench3Table(): string | null {
  if (!resultsExist("^stealth\\.jsonl$")) return null;

  // Take the latest successful record per provider+mode
  const rows = duckdbJson(`
    WITH ranked AS (
      SELECT *,
        ROW_NUMBER() OVER (PARTITION BY provider, mode ORDER BY created_at DESC) AS rn
      FROM read_json_auto('results/stealth.jsonl', format='newline_delimited')
      WHERE success = true
    )
    SELECT
      provider,
      mode,
      success,
      sannysoft_webdriver_detected,
      sannysoft_headless_detected,
      areyouheadless_detected,
      recaptcha_score
    FROM ranked
    WHERE rn = 1
    ORDER BY provider, mode
  `);

  // Also fetch failed rows (e.g. paid-plan gates) to include in table
  const failedRows = duckdbJson(`
    WITH ranked AS (
      SELECT *,
        ROW_NUMBER() OVER (PARTITION BY provider, mode ORDER BY created_at DESC) AS rn
      FROM read_json_auto('results/stealth.jsonl', format='newline_delimited')
      WHERE success = false
    )
    SELECT provider, mode, success, error_message
    FROM ranked WHERE rn = 1
    ORDER BY provider, mode
  `);

  if (!rows.length && !failedRows.length) return null;

  function fmt(val: unknown): string {
    if (val === null || val === undefined) return "—";
    if (val === true) return "Detected";
    if (val === false) return "Clean";
    return String(val);
  }

  const stealthPlan: Record<string, string> = {
    BROWSERLESS:   "Free (stealth endpoint)",
    KERNEL:        "Free (managed proxy included)",
    STEEL:         "Paid (proxy add-on)",
    HYPERBROWSER:  "Paid ($10/GB proxy)",
    ANCHORBROWSER: "Growth tier ($2,000/mo)",
    BROWSERBASE:   "Scale plan (custom pricing)",
  };

  // Successful rows first, sorted by provider then mode; failed rows appended at end
  const allRows = [
    ...rows,
    ...failedRows.map((r) => ({ ...r, _failed: true })),
  ].sort((a: any, b: any) => {
    if (a._failed !== b._failed) return a._failed ? 1 : -1;
    if (a.provider !== b.provider) return String(a.provider).localeCompare(String(b.provider));
    return String(a.mode).localeCompare(String(b.mode));
  });

  const header = `| Provider | Mode | WebDriver | Headless UA | AreYouHeadless | reCAPTCHA score | Stealth plan |`;
  const divider = `|----------|------|-----------|-------------|----------------|-----------------|--------------|`;
  const lines = allRows.map((r: any) => {
    if (r._failed) {
      const reason = String(r.error_message ?? "").split("\n")[0].replace(/Error: /, "");
      return `| ${r.provider} | ${r.mode} | — | — | — | — | ${reason} |`;
    }
    return `| ${r.provider} | ${r.mode} | ${fmt(r.sannysoft_webdriver_detected)} | ${fmt(r.sannysoft_headless_detected)} | ${fmt(r.areyouheadless_detected)} | ${r.recaptcha_score ?? "—"} | ${stealthPlan[String(r.provider)] ?? "—"} |`;
  });

  return [header, divider, ...lines].join("\n");
}

// ---- Benchmark 4: CAPTCHA --------------------------------------------------

function bench4Table(): string | null {
  if (!resultsExist("^captcha\\.jsonl$")) return null;

  // Take the latest record per provider (handles re-runs and old not_supported records)
  const rows = duckdbJson(`
    WITH ranked AS (
      SELECT *,
        ROW_NUMBER() OVER (PARTITION BY provider ORDER BY created_at DESC) AS rn
      FROM read_json_auto('results/captcha.jsonl', format='newline_delimited')
    )
    SELECT
      provider,
      supported,
      success,
      captcha_detected,
      captcha_solved,
      ROUND(try_cast(solve_ms AS DOUBLE) / 1000.0, 1) AS solve_s,
      not_supported_reason
    FROM ranked
    WHERE rn = 1
    ORDER BY supported DESC, solve_s ASC NULLS LAST
  `);

  if (!rows.length) return null;

  const hasErrors = rows.some((r) => !r.success);
  if (hasErrors) {
    console.error(`[report] benchmark 4 has errors — skipping`);
    return null;
  }

  function fmtBool(val: unknown): string {
    if (val === true) return "Yes";
    if (val === false) return "No";
    return "—";
  }

  const captchaCost: Record<string, string> = {
    BROWSERLESS:   "10 units/solve (~$0.02 on paid)",
    KERNEL:        "~$0.0006/solve (GB-seconds)",
    ANCHORBROWSER: "Starter plan ($50/mo) required",
    BROWSERBASE:   "Developer plan ($20/mo) required",
    HYPERBROWSER:  "Paid plan required",
    STEEL:         "Starter plan ($29/mo) required",
  };

  const header = `| Provider | Free tier | Detected | Solved | Solve time | Cost per solve |`;
  const divider = `|----------|-----------|----------|--------|------------|----------------|`;
  const lines = rows.map((r) => {
    const solveTime = r.solve_s != null ? `${r.solve_s}s` : r.supported ? "timeout" : "—";
    return `| ${r.provider} | ${fmtBool(r.supported)} | ${fmtBool(r.captcha_detected)} | ${fmtBool(r.captcha_solved)} | ${solveTime} | ${captchaCost[String(r.provider)] ?? "—"} |`;
  });

  return [header, divider, ...lines].join("\n");
}

// ---- Benchmark 5: Parallel -------------------------------------------------

function bench5Table(): string | null {
  if (!resultsExist("^parallel-.*\\.jsonl$")) return null;

  const rows = duckdbJson(`
    SELECT
      provider,
      sequential_mode,
      COUNT(*) AS runs,
      ROUND(AVG(sessions_succeeded), 1) AS avg_succeeded,
      concurrency AS max_sessions,
      ROUND(AVG(total_parallel_ms)) AS avg_parallel_ms,
      ROUND(AVG(overhead_ratio), 4) AS avg_overhead_ratio,
      SUM(CASE WHEN success THEN 0 ELSE 1 END) AS failed_batches
    FROM read_ndjson_auto('results/parallel-*.jsonl')
    GROUP BY provider, sequential_mode, concurrency
    ORDER BY sequential_mode ASC, avg_parallel_ms ASC
  `);

  if (!rows.length) return null;

  const concurrencyLimit: Record<string, string> = {
    STEEL:         "3 (free tier)",
    KERNEL:        "5 (free tier)",
    ANCHORBROWSER: "5 (free tier)",
    BROWSERLESS:   "2 (free tier)",
    HYPERBROWSER:  "1 (free tier)",
    BROWSERBASE:   "1 (free tier)",
  };

  const header = `| Rank | Provider | True parallel | Overhead ratio | Sessions succeeded | Failed batches | Free tier concurrency |`;
  const divider = `|------|----------|--------------|----------------|-------------------|----------------|----------------------|`;
  const lines = rows.map((r, i) => {
    const parallel = r.sequential_mode ? "No (sequential)" : "Yes";
    const failed = Number(r.failed_batches);
    const failedStr = failed > 0 ? `**${failed}**` : "0";
    return `| ${i + 1} | ${r.provider} | ${parallel} | ${r.avg_overhead_ratio} | ${r.avg_succeeded} / ${r.max_sessions} | ${failedStr} | ${concurrencyLimit[String(r.provider)] ?? "—"} |`;
  });

  return [header, divider, ...lines].join("\n");
}

// ---- README update ---------------------------------------------------------

function buildResultsSection(date: string): string {
  const sections: string[] = [];

  const b1 = bench1Table();
  if (b1) {
    sections.push(`### 1. Session lifecycle speed\n\n${b1}`);
  } else {
    sections.push(`### 1. Session lifecycle speed\n\n_No results yet or errors present — run \`npm run bench\` first._`);
  }

  const b2 = bench2Table();
  if (b2) {
    sections.push(`### 2. Idle workflow survival\n\n${b2}`);
  } else {
    sections.push(`### 2. Idle workflow survival\n\n_No results yet or errors present — run \`npm run idle\` first._`);
  }

  const b3 = bench3Table();
  if (b3) {
    sections.push(`### 3. Stealth / bot detection\n\n${b3}`);
  } else {
    sections.push(`### 3. Stealth / bot detection\n\n_No results yet or errors present — run \`npm run stealth\` first._`);
  }

  const b4 = bench4Table();
  if (b4) {
    sections.push(`### 4. CAPTCHA solving\n\n${b4}`);
  } else {
    sections.push(`### 4. CAPTCHA solving\n\n_No results yet or errors present — run \`npm run captcha\` first._`);
  }

  const b5 = bench5Table();
  if (b5) {
    sections.push(`### 5. Parallel session handling\n\n${b5}`);
  } else {
    sections.push(`### 5. Parallel session handling\n\n_No results yet or errors present — run \`npm run parallel\` first._`);
  }

  return [
    START_MARKER,
    `## Results`,
    ``,
    `_Last updated: ${date}_`,
    ``,
    sections.join("\n\n"),
    ``,
    END_MARKER,
  ].join("\n");
}

function updateReadme(newSection: string): void {
  const readme = fs.readFileSync(README, "utf-8");

  const startIdx = readme.indexOf(START_MARKER);
  const endIdx = readme.indexOf(END_MARKER);

  let updated: string;
  if (startIdx !== -1 && endIdx !== -1) {
    // Replace existing section
    updated =
      readme.slice(0, startIdx) +
      newSection +
      readme.slice(endIdx + END_MARKER.length);
  } else {
    // Prepend before first heading
    const firstHeading = readme.indexOf("\n#");
    if (firstHeading !== -1) {
      updated = readme.slice(0, firstHeading + 1) + newSection + "\n\n" + readme.slice(firstHeading + 1);
    } else {
      updated = newSection + "\n\n" + readme;
    }
  }

  fs.writeFileSync(README, updated, "utf-8");
  console.error(`[report] README.md updated`);
}

// ---- Main ------------------------------------------------------------------

function main() {
  if (!fs.existsSync(RESULTS_DIR)) {
    console.error(`[report] No results directory found — run benchmarks first`);
    process.exit(1);
  }

  const date = new Date().toISOString().slice(0, 10);
  const section = buildResultsSection(date);
  updateReadme(section);
  console.error(`[report] Done`);
}

main();
