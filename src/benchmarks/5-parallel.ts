/**
 * Benchmark 5: Parallel session handling
 *
 * Measures how each provider handles concurrent sessions.
 * Runs CONCURRENCY sessions simultaneously via Promise.all and records:
 *   - Whether all sessions completed successfully
 *   - Wall-clock time for the parallel batch (total_parallel_ms)
 *   - Sequential equivalent (sum of individual session_total_ms)
 *   - Overhead ratio: total_parallel_ms / sequential_equivalent_ms
 *     (lower = better parallelism; ideal ratio approaches 1/concurrency)
 *   - Any errors or rate-limiting per session
 *
 * Browserbase free tier allows only 1 concurrent session. For Browserbase
 * we run sequential_mode=true (sessions run one at a time) and note the
 * limitation in results.
 *
 * Each session: create → connect → navigate to TARGET_URL → release.
 * Same lifecycle as Benchmark 1 but run concurrently.
 */

import "dotenv/config";
import fs from "node:fs";
import { chromium, type Browser } from "playwright-core";
import type { ProviderClient, ProviderName } from "../types.js";
import { isoUtcNow, nowNs, msSince } from "../utils/time.js";
import { resolveProvider } from "../providers/index.js";
import { getArg, hasFlag } from "../utils/arg.js";

const TARGET_URL = "https://example.com";

export type ParallelSessionRecord = {
  created_at: string;
  provider: ProviderName;
  session_index: number;
  session_id: string | null;
  session_creation_ms: number | null;
  session_connect_ms: number | null;
  page_goto_ms: number | null;
  session_release_ms: number | null;
  session_total_ms: number | null;
  success: boolean;
  error_stage: string | null;
  error_message: string | null;
};

export type ParallelBatchRecord = {
  created_at: string;
  provider: ProviderName;
  run: number;
  concurrency: number;
  sequential_mode: boolean;
  sessions: ParallelSessionRecord[];
  sessions_succeeded: number;
  sessions_failed: number;
  total_parallel_ms: number | null;
  sequential_equivalent_ms: number | null;
  overhead_ratio: number | null;
  success: boolean;
  error_message: string | null;
};

async function runOneSession(
  provider: ProviderClient,
  index: number
): Promise<ParallelSessionRecord> {
  const sessionStart = nowNs();
  let browser: Browser | null = null;
  let sessionId: string | null = null;
  let stage = "init";

  const record: ParallelSessionRecord = {
    created_at: isoUtcNow(),
    provider: provider.name,
    session_index: index,
    session_id: null,
    session_creation_ms: null,
    session_connect_ms: null,
    page_goto_ms: null,
    session_release_ms: null,
    session_total_ms: null,
    success: false,
    error_stage: null,
    error_message: null,
  };

  try {
    // Create session
    stage = "create";
    const createStart = nowNs();
    let cdpUrl: string;

    while (true) {
      try {
        const created = await provider.create();
        sessionId = created.id;
        cdpUrl = created.cdpUrl;
        record.session_id = sessionId;
        record.session_creation_ms = msSince(createStart);
        break;
      } catch (e: any) {
        const status = e?.status ?? e?.statusCode ?? e?.response?.status;
        const message = e instanceof Error ? e.message : `${e}`;
        const isRateLimit =
          status === 429 || /rate|limit|429|too many/i.test(message ?? "");
        if (provider.name === "KERNEL" && isRateLimit) {
          console.error(`[rate_limit] KERNEL[${index}] → retry in 30s`);
          await new Promise((r) => setTimeout(r, 30_000));
          continue;
        }
        throw e;
      }
    }

    // Connect
    stage = "connect";
    const connectStart = nowNs();
    browser = await chromium.connectOverCDP(cdpUrl!);
    record.session_connect_ms = msSince(connectStart);

    // Navigate
    stage = "navigate";
    const gotoStart = nowNs();
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });
    record.page_goto_ms = msSince(gotoStart);

    record.success = true;
    console.error(
      `[s${index}] ${provider.name} ok — creation=${record.session_creation_ms}ms connect=${record.session_connect_ms}ms goto=${record.page_goto_ms}ms`
    );
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    record.error_stage = stage;
    record.error_message = message;
    console.error(`[s${index}] ${provider.name} ERROR stage=${stage}: ${message}`);
  } finally {
    if (browser) {
      try { await browser.close(); } catch {}
    }
    if (sessionId) {
      try {
        const releaseStart = nowNs();
        await provider.release(sessionId);
        record.session_release_ms = msSince(releaseStart);
      } catch (e: any) {
        console.error(`[s${index}] release error: ${e?.message ?? e}`);
      }
    }
    record.session_total_ms = msSince(sessionStart);
  }

  return record;
}

async function runParallelBatch(
  provider: ProviderClient,
  concurrency: number,
  sequential: boolean,
  run: number
): Promise<ParallelBatchRecord> {
  const batchRecord: ParallelBatchRecord = {
    created_at: isoUtcNow(),
    provider: provider.name,
    run,
    concurrency,
    sequential_mode: sequential,
    sessions: [],
    sessions_succeeded: 0,
    sessions_failed: 0,
    total_parallel_ms: null,
    sequential_equivalent_ms: null,
    overhead_ratio: null,
    success: false,
    error_message: null,
  };

  const batchStart = nowNs();

  try {
    if (sequential) {
      // Run sessions one-by-one (for providers with concurrency=1 free-tier limit)
      console.error(`[batch] ${provider.name} sequential mode (free-tier limit: 1 concurrent)`);
      for (let i = 0; i < concurrency; i++) {
        const result = await runOneSession(provider, i);
        batchRecord.sessions.push(result);
      }
    } else {
      // Run all sessions simultaneously
      console.error(`[batch] ${provider.name} parallel (concurrency=${concurrency})`);
      const promises = Array.from({ length: concurrency }, (_, i) =>
        runOneSession(provider, i)
      );
      batchRecord.sessions = await Promise.all(promises);
    }

    batchRecord.total_parallel_ms = msSince(batchStart);
    batchRecord.sessions_succeeded = batchRecord.sessions.filter((s) => s.success).length;
    batchRecord.sessions_failed = batchRecord.sessions.filter((s) => !s.success).length;

    const seqEquiv = batchRecord.sessions.reduce(
      (sum, s) => sum + (s.session_total_ms ?? 0),
      0
    );
    batchRecord.sequential_equivalent_ms = seqEquiv;

    if (seqEquiv > 0 && batchRecord.total_parallel_ms !== null) {
      batchRecord.overhead_ratio = parseFloat(
        (batchRecord.total_parallel_ms / seqEquiv).toFixed(4)
      );
    }

    batchRecord.success = batchRecord.sessions_failed === 0;
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    batchRecord.error_message = message;
    batchRecord.total_parallel_ms = msSince(batchStart);
    console.error(`[batch_error] ${provider.name}: ${message}`);
  }

  return batchRecord;
}

// --- CLI ---

async function main() {
  const providerArg = getArg("provider", process.env.PROVIDER ?? "browserless")!;
  const concurrency = Number(getArg("concurrency", "3"));
  const runs = Number(getArg("runs", "3"));
  const warmup = !hasFlag("no-warmup");

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);

    // Run sequentially if the provider's free-tier concurrency limit is 1
    const isSequential = (provider.maxConcurrency ?? Infinity) < concurrency;

    const out = `results/parallel-${providerName}.jsonl`;
    fs.mkdirSync("results", { recursive: true });
    if (fs.existsSync(out)) {
      fs.unlinkSync(out);
      console.error(`[reset] deleted existing ${out}`);
    }

    console.error(
      `\n=== ${provider.name} (concurrency=${concurrency}, sequential_mode=${isSequential}) ===`
    );

    if (warmup) {
      console.error(`[warmup] 1 batch, concurrency=1`);
      const wr = await runParallelBatch(provider, 1, true, 0);
      if (!wr.success) console.error(`[warmup_failed] ${wr.error_message}`);
    }

    for (let i = 1; i <= runs; i++) {
      console.error(`\n[run ${i}/${runs}]`);
      const record = await runParallelBatch(provider, concurrency, isSequential, i);
      fs.appendFileSync(out, JSON.stringify(record) + "\n", { encoding: "utf-8" });
      console.error(
        `[run ${i}] parallel=${record.total_parallel_ms}ms seq_equiv=${record.sequential_equivalent_ms}ms ratio=${record.overhead_ratio} ok=${record.sessions_succeeded}/${concurrency}`
      );
    }

    console.error(`[done] results written to ${out}`);
  }
}

main().catch((e) => {
  console.error(`[fatal] ${e?.stack ?? e?.message ?? e}`);
  process.exit(1);
});
