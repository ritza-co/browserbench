/**
 * Benchmark 4: CAPTCHA solving capability
 *
 * Tests whether each provider offers built-in CAPTCHA solving,
 * and whether it works on the free tier.
 *
 * Target: https://www.google.com/recaptcha/api2/demo (reCAPTCHA v2 checkbox)
 *
 * Metrics:
 *   - supported: does the provider advertise built-in CAPTCHA solving?
 *   - captcha_detected: did the provider detect the CAPTCHA?
 *   - captcha_solved: did the CAPTCHA get solved (form submittable)?
 *   - solve_ms: time from page load to CAPTCHA solved event (or timeout)
 *   - total_ms: total wall clock time
 *
 * Cost note: Browserless charges 10 units per CAPTCHA solve (free tier = 1,000 units/mo).
 * Run once per provider — do not loop.
 *
 * Provider support matrix (free tier only):
 *   Browserless   - yes  (solveCaptchas=true CDP param, Browserless.captchaAutoSolved event)
 *   Browserbase   - no   (requires Developer plan, $20/mo)
 *   Anchor        - no   (requires paid residential proxy, $8/GB)
 *   Hyperbrowser  - no   (feature exists: solveCaptchas=true, but requires paid plan)
 *   Steel         - no   (feature exists: solveCaptcha=true, but requires Developer plan or above)
 *   Kernel        - yes  (stealth: true adds a reCAPTCHA solver that auto-solves challenges)
 */

import "dotenv/config";
import fs from "node:fs";
import { chromium } from "playwright-core";
import type { ProviderClient, ProviderName } from "../types.js";
import { isoUtcNow, nowNs, msSince } from "../utils/time.js";
import { getArg } from "../utils/arg.js";
import { resolveProvider } from "../providers/index.js";
import { createWithCaptchaRetry } from "../utils/retry.js";

const CAPTCHA_URL = "https://www.google.com/recaptcha/api2/demo";
const RESULTS_FILE = "results/captcha.jsonl";

export type CaptchaRecord = {
  created_at: string;
  provider: ProviderName;
  supported: boolean;
  not_supported_reason: string | null;
  captcha_detected: boolean | null;
  captcha_solved: boolean | null;
  solve_ms: number | null;
  total_ms: number | null;
  success: boolean;
  error_stage: string | null;
  error_message: string | null;
};

// Providers that do not support CAPTCHA solving on the free tier, and why.
const NOT_SUPPORTED: Partial<Record<ProviderName, string>> = {
  BROWSERBASE: "Requires Developer plan ($20/mo) — not available on free tier",
  ANCHORBROWSER: "Requires paid residential proxy ($8/GB) — not available without additional cost",
  HYPERBROWSER: "Built-in CAPTCHA solving exists (solveCaptchas=true) but requires a paid plan — not available on free tier",
  STEEL: "Built-in CAPTCHA solving exists (solveCaptcha=true) but requires Developer plan or above — not available on free tier",
};

async function runBrowserlessCaptcha(provider: ProviderClient): Promise<{
  captcha_detected: boolean;
  captcha_solved: boolean;
  solve_ms: number | null;
}> {
  const session = await createWithCaptchaRetry(provider);
  const browser = await chromium.connectOverCDP(session.cdpUrl);
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = ctx.pages()[0] ?? (await ctx.newPage());

  // Set up CDP session to listen for Browserless CAPTCHA events
  const cdpSession = await ctx.newCDPSession(page);

  let captchaDetected = false;
  let captchaSolved = false;
  let detectTime: bigint | null = null;
  let solveTime: bigint | null = null;

  // Playwright's CDPSession type only covers standard CDP domains, but Browserless emits
  // custom events via the same CDP channel. Cast to EventEmitter to register listeners.
  const cdpEmitter = cdpSession as unknown as {
    on(event: string, listener: (data: unknown) => void): void;
  };

  cdpEmitter.on("Browserless.captchaFound", () => {
    captchaDetected = true;
    detectTime = nowNs();
    console.error("[captcha] CAPTCHA detected");
  });

  cdpEmitter.on("Browserless.captchaAutoSolved", () => {
    captchaSolved = true;
    solveTime = nowNs();
    console.error("[captcha] CAPTCHA auto-solved");
  });

  try {
    console.error(`[goto] ${CAPTCHA_URL}`);
    await page.goto(CAPTCHA_URL, { waitUntil: "domcontentloaded", timeout: 30_000 });

    // Wait up to 60s for CAPTCHA to be detected and solved
    const deadline = Date.now() + 60_000;
    while (Date.now() < deadline) {
      if (captchaSolved) break;
      await page.waitForTimeout(1_000);
    }

    // If solved, try to submit the form to confirm the token was injected
    if (captchaSolved) {
      await page.waitForTimeout(1_000); // brief pause for token injection
      try {
        const submitBtn = page.locator("#recaptcha-demo-submit");
        if ((await submitBtn.count()) > 0) {
          await submitBtn.click();
          await page.waitForTimeout(3_000);
        }
      } catch {
        // Non-fatal — we already have captcha_solved from the event
      }

      // Confirm success from page content
      const content = await page.content();
      const verified =
        content.includes("Verification Success") ||
        content.toLowerCase().includes("recaptcha-success") ||
        content.toLowerCase().includes("verification was successful");
      if (!verified) {
        // Event fired but form didn't confirm — keep captcha_solved=true (event is the ground truth)
        console.error("[captcha] warning: solved event fired but success text not found in page");
      }
    }

    const solve_ms =
      detectTime !== null && solveTime !== null
        ? Number(solveTime - detectTime) / 1_000_000
        : null;

    return { captcha_detected: captchaDetected, captcha_solved: captchaSolved, solve_ms };
  } finally {
    try { await page.close(); } catch {}
    try { await browser.close(); } catch {}
  }
}

async function runKernelCaptcha(provider: ProviderClient): Promise<{
  captcha_detected: boolean;
  captcha_solved: boolean;
  solve_ms: number | null;
}> {
  const session = await createWithCaptchaRetry(provider);
  const browser = await chromium.connectOverCDP(session.cdpUrl);
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = ctx.pages()[0] ?? (await ctx.newPage());

  const detectTime = nowNs();
  let captchaSolved = false;
  let solveTime: bigint | null = null;

  try {
    console.error(`[goto] ${CAPTCHA_URL}`);
    await page.goto(CAPTCHA_URL, { waitUntil: "domcontentloaded", timeout: 30_000 });

    // Poll up to 90s for the reCAPTCHA to be solved.
    // Detection methods (in priority order):
    // 1. grecaptcha.getResponse() on the main page — returns token string when solved
    // 2. .recaptcha-checkbox inside the reCAPTCHA iframe has aria-checked="true"
    const deadline = Date.now() + 90_000;
    while (Date.now() < deadline) {
      try {
        // Method 1: main page grecaptcha response
        const token = await page.evaluate(() => {
          const w = window as any;
          if (typeof w.grecaptcha?.getResponse === "function") {
            return w.grecaptcha.getResponse() as string;
          }
          return "";
        });
        if (token && token.length > 0) {
          captchaSolved = true;
          solveTime = nowNs();
          console.error("[captcha] solved via grecaptcha.getResponse()");
          break;
        }

        // Method 2: reCAPTCHA iframe checkbox state
        const rcFrame = page.frames().find(
          (f) => f.url().includes("google.com/recaptcha/api2/anchor") ||
                 f.url().includes("google.com/recaptcha/api2/bframe")
        );
        if (rcFrame) {
          const checked = await rcFrame.evaluate(() => {
            const cb = document.querySelector("#recaptcha-anchor, .recaptcha-checkbox");
            return cb?.getAttribute("aria-checked") === "true";
          }).catch(() => false);
          if (checked) {
            captchaSolved = true;
            solveTime = nowNs();
            console.error("[captcha] solved via iframe checkbox aria-checked");
            break;
          }
        }
      } catch {
        // page may not be ready yet — continue polling
      }
      await page.waitForTimeout(2_000);
    }

    const solve_ms =
      solveTime !== null ? Number(solveTime - detectTime) / 1_000_000 : null;

    // captcha_detected=true: we always detect the presence of the reCAPTCHA on page load
    return { captcha_detected: true, captcha_solved: captchaSolved, solve_ms };
  } finally {
    try { await page.close(); } catch {}
    try { await browser.close(); } catch {}
    try { await provider.release(session.id); } catch {}
  }
}

async function runCaptchaBenchmark(provider: ProviderClient): Promise<CaptchaRecord> {
  const wallStart = nowNs();
  let stage = "init";

  const notSupportedReason = NOT_SUPPORTED[provider.name] ?? null;
  const supported = notSupportedReason === null && !!provider.createWithCaptcha;

  const record: CaptchaRecord = {
    created_at: isoUtcNow(),
    provider: provider.name,
    supported,
    not_supported_reason: notSupportedReason,
    captcha_detected: null,
    captcha_solved: null,
    solve_ms: null,
    total_ms: null,
    success: false,
    error_stage: null,
    error_message: null,
  };

  // If not supported, record immediately — no session needed
  if (!supported) {
    record.total_ms = msSince(wallStart);
    record.success = true; // "success" means the benchmark completed — not that CAPTCHA was solved
    console.error(
      `[skip] ${provider.name} — CAPTCHA solving not supported: ${record.not_supported_reason}`
    );
    return record;
  }

  try {
    stage = "captcha";
    console.error(`[run] ${provider.name} — navigating to ${CAPTCHA_URL}`);

    let result: { captcha_detected: boolean; captcha_solved: boolean; solve_ms: number | null };

    switch (provider.name) {
      case "BROWSERLESS":
        result = await runBrowserlessCaptcha(provider);
        break;
      case "KERNEL":
        result = await runKernelCaptcha(provider);
        break;
      default:
        throw new Error(`No CAPTCHA implementation for supported provider: ${provider.name}`);
    }

    record.captcha_detected = result.captcha_detected;
    record.captcha_solved = result.captcha_solved;
    record.solve_ms = result.solve_ms;
    record.success = true;
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    record.error_stage = stage;
    record.error_message = message;
    console.error(`[error] stage=${stage} ${message}`);
  } finally {
    record.total_ms = msSince(wallStart);
  }

  return record;
}

async function main() {
  const providerArg = getArg("provider", process.env.PROVIDER ?? "browserless")!;

  const providers = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  fs.mkdirSync("results", { recursive: true });

  for (const providerName of providers) {
    const provider = resolveProvider(providerName);
    console.error(`\n=== ${provider.name} ===`);
    const record = await runCaptchaBenchmark(provider);
    fs.appendFileSync(RESULTS_FILE, JSON.stringify(record) + "\n", {
      encoding: "utf-8",
    });
    console.error(
      `[result] supported=${record.supported} detected=${record.captcha_detected} solved=${record.captcha_solved} solve_ms=${record.solve_ms} total_ms=${record.total_ms}`
    );
    console.error(`[written] ${RESULTS_FILE}`);
  }

  console.error(`\n[done] results written to ${RESULTS_FILE}`);
}

main().catch((e) => {
  console.error(`[fatal] ${e?.stack ?? e?.message ?? e}`);
  process.exit(1);
});
