import fs from "node:fs";
import { chromium, type Browser } from "playwright-core";
import type { MetricRecord, ProviderClient } from "./types.js";
import { isoUtcNow, nowNs, msSince } from "./utils/time.js";

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
    const created = await provider.create();
    const { id, cdpUrl } = created;
    result.id = id;
    session = { id };
    result.session_creation_ms = msSince(t0);
    console.error(
      `[Session created] provider=${provider.name} id=${id} ${result.session_creation_ms}ms`
    );

    stage = "connect_over_cdp";
    const t1 = nowNs();
    browser = await chromium.connectOverCDP(cdpUrl);
    result.session_connect_ms = msSince(t1);
    console.error(`[Browser connected] ${result.session_connect_ms}ms`);

    stage = "page_goto";
    const t2 = nowNs();
    const context = browser.contexts()[0] || (await browser.newContext());
    const page = context.pages()[0] || (await context.newPage());
    await page.goto(url, { waitUntil: "domcontentloaded" });
    result.page_goto_ms = msSince(t2);
    console.error(`[Page visited] ${result.page_goto_ms}ms`);

    result.success = true;
  } catch (e: any) {
    const message = e instanceof Error ? e.stack || e.message : `${e}`;
    result.error_stage = stage;
    result.error_message = message;
    console.error(`[ERROR] stage=${stage} id=${result.id} ${message}`);
  } finally {
    if (browser) {
      try {
        await browser.close();
      } catch (e) {
        console.error(`[BROWSER_CLOSE_ERROR] ${e}`);
      }
    }

    if (session?.id) {
      try {
        stage = "session_release";
        const t3 = nowNs();
        await provider.release(session.id);
        result.session_release_ms = msSince(t3);
        console.error(`[Session released] ${result.session_release_ms}ms`);
      } catch (e: any) {
        console.error(
          `[SESSION_RELEASE_ERROR] id=${session.id} ${e?.message || e}`
        );
      }
    }
  }

  return result;
}

const WARMUP_RUNS = 3; // Reduced from 10 for smaller tests

export async function runLoop(
  provider: ProviderClient,
  { runs, url, out }: { runs: number; url: string; out: string }
) {
  console.error(`\n=== Starting benchmark for ${provider.name} ===`);
  console.error(`Warmup runs: ${WARMUP_RUNS}, Measured runs: ${runs}\n`);

  for (let i = 1; i <= WARMUP_RUNS; i++) {
    console.error(`[WARMUP] ${i}/${WARMUP_RUNS}`);
    await runSingleSession(provider, url);
  }

  let success = 0;
  let failure = 0;

  for (let i = 1; i <= runs; i++) {
    console.error(`[RUN] ${i}/${runs}`);
    const record = await runSingleSession(provider, url);
    fs.appendFileSync(out, JSON.stringify(record) + "\n", {
      encoding: "utf-8",
    });
    if (record.success) success++;
    else failure++;
  }

  console.error(`\n=== ${provider.name} Complete ===`);
  console.error(`Success: ${success}, Failure: ${failure}`);
  console.error(`Results written to: ${out}\n`);
}
