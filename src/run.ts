import fs from "node:fs";
import { chromium, type Browser } from "playwright-core";
import type { MetricRecord, ProviderClient } from "./types.js";
import { isoUtcNow, nowNs, msSince } from "./utils/time.js";
import { createWithRetry } from "./utils/retry.js";

export async function runSingleSession(
  provider: ProviderClient,
  url: string
): Promise<MetricRecord> {
  let browser: Browser | null = null;
  let session: { id: string } | null = null;
  let stage = "init";

  const result: MetricRecord = {
    created_at: isoUtcNow(),
    id: null,
    session_creation_ms: null,
    session_connect_ms: null,
    page_goto_ms: null,
    session_release_ms: null,
    provider: provider.name,
    success: false,
    error_stage: null,
    error_message: null,
  };

  try {
    stage = "session_create";
    const t0 = nowNs();
    const created = await createWithRetry(provider);
    const { id, cdpUrl } = created;
    result.id = id;
    session = { id };
    result.session_creation_ms = msSince(t0);
    console.error(`[session_create] ${provider.name} id=${id} ${result.session_creation_ms}ms`);

    stage = "session_connect";
    const t1 = nowNs();
    browser = await chromium.connectOverCDP(cdpUrl);
    result.session_connect_ms = msSince(t1);
    console.error(`[session_connect] ${result.session_connect_ms}ms`);

    stage = "page_goto";
    const t2 = nowNs();
    const context = browser.contexts()[0] ?? (await browser.newContext());
    const page = context.pages()[0] ?? (await context.newPage());
    await page.goto(url, { waitUntil: "domcontentloaded" });
    result.page_goto_ms = msSince(t2);
    console.error(`[page_goto] ${result.page_goto_ms}ms`);

    result.success = true;
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    result.error_stage = stage;
    result.error_message = message;
    console.error(`[error] stage=${stage} id=${result.id} ${message}`);
  } finally {
    if (browser) {
      try {
        await browser.close();
      } catch {}
    }

    if (session?.id) {
      try {
        stage = "session_release";
        const t3 = nowNs();
        await provider.release(session.id);
        result.session_release_ms = msSince(t3);
        console.error(`[session_release] ${result.session_release_ms}ms`);
      } catch (e: any) {
        console.error(`[session_release_error] id=${session.id} ${e?.message ?? e}`);
      }
    }

    // Browserbase rate limit: sessions created faster than ~3s get throttled
    if (provider.name === "BROWSERBASE") {
      const total =
        (result.session_creation_ms ?? 0) +
        (result.session_connect_ms ?? 0) +
        (result.page_goto_ms ?? 0) +
        (result.session_release_ms ?? 0);
      const wait = Math.max(0, 3000 - total);
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    }
  }

  return result;
}

const WARMUP_RUNS = 3;

export async function runBenchmark(
  provider: ProviderClient,
  { runs, url, out, warmup = true }: { runs: number; url: string; out: string; warmup?: boolean }
) {
  console.error(`\n=== ${provider.name} ===`);
  if (warmup) {
    console.error(`Warmup: ${WARMUP_RUNS} runs`);
    for (let i = 1; i <= WARMUP_RUNS; i++) {
      console.error(`[warmup ${i}/${WARMUP_RUNS}]`);
      await runSingleSession(provider, url);
    }
  }

  console.error(`Measured: ${runs} runs → ${out}`);
  let success = 0;
  let failure = 0;

  for (let i = 1; i <= runs; i++) {
    console.error(`[run ${i}/${runs}]`);
    const record = await runSingleSession(provider, url);
    fs.appendFileSync(out, JSON.stringify(record) + "\n", { encoding: "utf-8" });
    if (record.success) success++;
    else failure++;
  }

  console.error(`Done: ${success} ok, ${failure} failed`);
}
