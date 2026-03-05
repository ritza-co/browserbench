/**
 * Benchmark 2: Cost efficiency for idle workflows
 *
 * Simulates a multi-step workflow with a 5-minute idle gap:
 *   1. Create session, navigate to URL 1, extract page title (active work)
 *   2. Wait IDLE_MS (default 5 minutes)
 *   3. Navigate to URL 2, extract page title (active work)
 *   4. Release session
 *
 * Measures:
 *   - step1_ms: creation + connect + first navigation
 *   - idle_ms: actual time spent waiting
 *   - session_survived: was the browser connection still alive after the wait?
 *   - reconnect_ms: if session died, time for a full cold-start reconnect (null if survived)
 *   - step2_ms: second navigation time
 *   - step2_title: page title from second navigation (sanity check)
 *   - session_release_ms: time to release
 *   - total_ms: wall-clock time for the entire workflow
 */

import "dotenv/config";
import fs from "node:fs";
import { chromium, type Browser, type Page } from "playwright-core";
import type { ProviderClient, ProviderName } from "../types.js";
import { isoUtcNow, nowNs, msSince } from "../utils/time.js";
import { resolveProvider } from "../providers/index.js";
import { getArg, hasFlag } from "../utils/arg.js";
import { createWithRetry } from "../utils/retry.js";

const STEP1_URL = "https://example.com";
const STEP2_URL = "https://example.org";

export type IdleRecord = {
  created_at: string;
  provider: ProviderName;
  session_id: string | null;
  step1_ms: number | null;
  idle_ms: number | null;
  session_survived: boolean | null;
  reconnect_ms: number | null;
  step2_ms: number | null;
  step2_title: string | null;
  session_release_ms: number | null;
  total_ms: number | null;
  success: boolean;
  error_stage: string | null;
  error_message: string | null;
};

async function runIdleWorkflow(
  provider: ProviderClient,
  idleMs: number
): Promise<IdleRecord> {
  const wallStart = nowNs();
  let browser: Browser | null = null;
  let sessionId: string | null = null;
  let cdpUrl: string | null = null;
  let stage = "init";

  const record: IdleRecord = {
    created_at: isoUtcNow(),
    provider: provider.name,
    session_id: null,
    step1_ms: null,
    idle_ms: null,
    session_survived: null,
    reconnect_ms: null,
    step2_ms: null,
    step2_title: null,
    session_release_ms: null,
    total_ms: null,
    success: false,
    error_stage: null,
    error_message: null,
  };

  try {
    // --- Step 1: Create session, connect, navigate ---
    stage = "step1_create";
    console.error(`[step1_create] ${provider.name}`);
    const step1Start = nowNs();

    const created = await createWithRetry(provider);
    sessionId = created.id;
    cdpUrl = created.cdpUrl;
    record.session_id = sessionId;

    stage = "step1_connect";
    console.error(`[step1_connect] ${provider.name}`);
    browser = await chromium.connectOverCDP(cdpUrl);

    stage = "step1_navigate";
    console.error(`[step1_navigate] ${STEP1_URL}`);
    const ctx = browser.contexts()[0] ?? (await browser.newContext());
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    await page.goto(STEP1_URL, { waitUntil: "domcontentloaded" });
    const step1Title = await page.title();
    console.error(`[step1_done] title="${step1Title}"`);

    record.step1_ms = msSince(step1Start);
    console.error(`[step1_ms] ${record.step1_ms}ms`);

    // --- Wait (idle) ---
    stage = "idle";
    console.error(`[idle] waiting ${idleMs / 1000}s…`);
    const idleStart = nowNs();
    await new Promise((r) => setTimeout(r, idleMs));
    record.idle_ms = msSince(idleStart);
    console.error(`[idle_done] actual=${record.idle_ms}ms`);

    // --- Step 2: Check if session survived, navigate ---
    stage = "step2";
    console.error(`[step2] checking session health…`);

    let step2Page: Page;
    let survived = false;
    let reconnectMs: number | null = null;

    try {
      // Probe the connection: if browser is disconnected this throws
      if (!browser.isConnected()) throw new Error("Browser disconnected");
      // Also try a quick evaluate to confirm the page is still alive
      await page.evaluate(() => document.title);
      survived = true;
      step2Page = page;
      console.error(`[step2] session survived idle period`);
    } catch (_e) {
      // Session died during idle — need a full cold start
      console.error(`[step2] session died — cold-starting new session`);
      const reconnectStart = nowNs();

      stage = "step2_reconnect_create";
      if (browser) {
        try { await browser.close(); } catch {}
        browser = null;
      }

      const reconnected = await createWithRetry(provider);
      sessionId = reconnected.id;
      cdpUrl = reconnected.cdpUrl;
      record.session_id = sessionId;

      stage = "step2_reconnect_connect";
      browser = await chromium.connectOverCDP(cdpUrl);
      const ctx2 = browser.contexts()[0] ?? (await browser.newContext());
      step2Page = ctx2.pages()[0] ?? (await ctx2.newPage());
      reconnectMs = msSince(reconnectStart);
      console.error(`[step2_reconnect_done] reconnect_ms=${reconnectMs}`);
    }

    record.session_survived = survived;
    record.reconnect_ms = reconnectMs;

    stage = "step2_navigate";
    console.error(`[step2_navigate] ${STEP2_URL}`);
    const step2Start = nowNs();
    await step2Page.goto(STEP2_URL, { waitUntil: "domcontentloaded" });
    record.step2_ms = msSince(step2Start);
    record.step2_title = await step2Page.title();
    console.error(
      `[step2_done] step2_ms=${record.step2_ms}ms title="${record.step2_title}"`
    );

    record.success = true;
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    record.error_stage = stage;
    record.error_message = message;
    console.error(`[error] stage=${stage} ${message}`);
  } finally {
    if (browser) {
      try { await browser.close(); } catch {}
    }

    if (sessionId) {
      stage = "session_release";
      try {
        const t = nowNs();
        await provider.release(sessionId);
        record.session_release_ms = msSince(t);
        console.error(`[session_release] ${record.session_release_ms}ms`);
      } catch (e: any) {
        console.error(`[session_release_error] ${e?.message ?? e}`);
      }
    }

    record.total_ms = msSince(wallStart);
    console.error(`[total] ${record.total_ms}ms success=${record.success}`);
  }

  return record;
}

// --- CLI ---

async function main() {
  const providerArg = getArg("provider", process.env.PROVIDER ?? "browserless")!;
  const idleMins = Number(getArg("idle-mins", "5"));
  const idleMs = idleMins * 60 * 1000;
  const runs = Number(getArg("runs", "1"));
  const warmup = !hasFlag("no-warmup");

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);
    const out = `results/idle-${providerName}.jsonl`;

    fs.mkdirSync("results", { recursive: true });
    if (fs.existsSync(out)) {
      fs.unlinkSync(out);
      console.error(`[reset] deleted existing ${out}`);
    }

    console.error(`\n=== ${provider.name} (idle=${idleMins}min) ===`);

    if (warmup) {
      // One warmup run with 0s idle to wake up the provider
      console.error(`[warmup] 1 run, no idle`);
      const warmupRecord = await runIdleWorkflow(provider, 0);
      if (!warmupRecord.success) {
        console.error(`[warmup_failed] ${warmupRecord.error_message}`);
      }
    }

    for (let i = 1; i <= runs; i++) {
      console.error(`[run ${i}/${runs}]`);
      const record = await runIdleWorkflow(provider, idleMs);
      fs.appendFileSync(out, JSON.stringify(record) + "\n", { encoding: "utf-8" });
    }

    console.error(`[done] results written to ${out}`);
  }
}

main().catch((e) => {
  console.error(`[fatal] ${e?.stack ?? e?.message ?? e}`);
  process.exit(1);
});
