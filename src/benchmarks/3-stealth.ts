/**
 * Benchmark 3: Stealth / bot detection bypass
 *
 * Tests each provider's ability to pass as a real user browser.
 * Runs each provider in default mode, then stealth mode (where supported).
 *
 * Checks:
 *   - bot.sannysoft.com: WebDriver detected, Headless detected, User-Agent suspicious
 *   - arh.antoinevastel.com/bots/areyouheadless: headless detection
 *   - antcpt.com/score_detector: reCAPTCHA score (0-1, >= 0.7 = human-like)
 *
 * Pass/fail criteria:
 *   - webdriver_detected: false = pass (not detected)
 *   - headless_detected: false = pass (not detected)
 *   - recaptcha_score: >= 0.7 = pass
 */

import "dotenv/config";
import fs from "node:fs";
import { chromium, type Browser } from "playwright-core";
import type { ProviderClient, ProviderName } from "../types.js";
import { isoUtcNow, nowNs, msSince } from "../utils/time.js";
import { resolveProvider } from "../providers/index.js";
import { getArg, hasFlag } from "../utils/arg.js";
import { createWithRetry, createStealthWithRetry } from "../utils/retry.js";

export type StealthMode = "default" | "stealth";

export type StealthRecord = {
  created_at: string;
  provider: ProviderName;
  mode: StealthMode;
  // bot.sannysoft.com
  sannysoft_webdriver_detected: boolean | null;
  sannysoft_headless_detected: boolean | null;
  sannysoft_user_agent_suspicious: boolean | null;
  sannysoft_raw: string | null;
  // areyouheadless
  areyouheadless_detected: boolean | null;
  areyouheadless_raw: string | null;
  // antcpt.com
  recaptcha_score: number | null;
  // overall
  total_ms: number | null;
  success: boolean;
  error_stage: string | null;
  error_message: string | null;
};

// --- Detection checks ---

/**
 * Extracts test results from bot.sannysoft.com.
 * The page renders a table where each row has a <td> with text "passed" or "failed".
 * We look for the specific test rows by their label text.
 */
async function checkSannySoft(browser: Browser): Promise<{
  webdriver_detected: boolean | null;
  headless_detected: boolean | null;
  user_agent_suspicious: boolean | null;
  raw: string;
}> {
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = await ctx.newPage();

  try {
    await page.goto("https://bot.sannysoft.com", {
      waitUntil: "networkidle",
      timeout: 30_000,
    });

    // Wait for results table to populate
    await page.waitForSelector("table", { timeout: 15_000 });
    // Give JS tests time to run
    await page.waitForTimeout(3_000);

    // Extract all table row labels and pass/fail status
    const results = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll("tr"));
      return rows.map((row) => {
        const cells = Array.from(row.querySelectorAll("td"));
        if (cells.length < 2) return null;
        const label = cells[0]?.textContent?.trim() ?? "";
        const result = cells[1]?.textContent?.trim() ?? "";
        const style = (cells[1] as HTMLElement)?.style?.backgroundColor ?? "";
        const className = cells[1]?.className ?? "";
        return { label, result, style, className };
      }).filter(Boolean);
    });

    const raw = JSON.stringify(results);

    // Helper: find a row by partial label match and check if it "failed"
    function isFailed(labelFragment: string): boolean | null {
      const row = results.find(
        (r) => r && r.label.toLowerCase().includes(labelFragment.toLowerCase())
      );
      if (!row) return null;
      // "failed" text or red background indicates detection (bad for us)
      const resultLower = row.result.toLowerCase();
      const styleLower = row.style.toLowerCase();
      const classLower = row.className.toLowerCase();
      if (resultLower.includes("failed") || styleLower.includes("red") || classLower.includes("failed")) {
        return true; // detected / failed the test
      }
      if (resultLower.includes("passed") || styleLower.includes("green") || classLower.includes("passed")) {
        return false; // not detected / passed
      }
      return null;
    }

    return {
      // "WebDriver (New)" row — present = detected
      webdriver_detected: isFailed("webdriver (new)") ?? isFailed("webdriver"),
      // "HEADCHR_UA" is the headless Chrome user-agent check
      headless_detected: isFailed("headchr_ua") ?? isFailed("headchr"),
      // "User Agent (Old)" row contains "HeadlessChrome" in UA string when suspicious
      user_agent_suspicious: isFailed("user agent"),
      raw,
    };
  } finally {
    await page.close();
  }
}

/**
 * Checks arh.antoinevastel.com/bots/areyouheadless.
 * Returns true if detected as headless.
 */
async function checkAreYouHeadless(browser: Browser): Promise<{
  detected: boolean | null;
  raw: string;
}> {
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = await ctx.newPage();

  try {
    await page.goto("https://arh.antoinevastel.com/bots/areyouheadless", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    await page.waitForTimeout(2_000);

    const text = await page.evaluate(() => {
      return document.body?.innerText ?? "";
    });

    const raw = text.slice(0, 500);
    const textLower = text.toLowerCase();

    // The page says "You are Chrome headless" or "You are not Chrome headless"
    if (textLower.includes("you are not chrome headless")) return { detected: false, raw };
    if (textLower.includes("you are chrome headless")) return { detected: true, raw };
    // Fallback for shorter variants
    if (textLower.includes("you are not headless")) return { detected: false, raw };
    if (textLower.includes("you are headless")) return { detected: true, raw };

    return { detected: null, raw };
  } finally {
    await page.close();
  }
}

/**
 * Gets reCAPTCHA score from antcpt.com/score_detector.
 * Score >= 0.7 is considered human-like.
 */
async function checkRecaptchaScore(browser: Browser): Promise<number | null> {
  const ctx = browser.contexts()[0] ?? (await browser.newContext());
  const page = await ctx.newPage();

  try {
    await page.goto("https://antcpt.com/score_detector", {
      waitUntil: "domcontentloaded",
      timeout: 45_000,
    });

    // The page loads the score via reCAPTCHA — wait up to 20s for it to appear
    let score: number | null = null;
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(3_000);

      score = await page.evaluate(() => {
        const text = document.body?.innerText ?? "";
        const match = text.match(/score[:\s]+([\d.]+)/i) ?? text.match(/([\d.]+)\s*\//);
        if (match) return parseFloat(match[1]);

        // Try looking for the score element directly
        const divs = Array.from(document.querySelectorAll("div, span, p"));
        for (const el of divs) {
          const content = (el as HTMLElement).innerText ?? "";
          const m = content.match(/^(0\.\d+)$/);
          if (m) return parseFloat(m[1]);
        }
        return null;
      });

      if (score !== null) break;
    }

    return score;
  } finally {
    await page.close();
  }
}

// --- Main benchmark runner ---

async function runStealthCheck(
  provider: ProviderClient,
  mode: StealthMode
): Promise<StealthRecord> {
  const wallStart = nowNs();
  let browser: Browser | null = null;
  let sessionId: string | null = null;
  let stage = "init";

  const record: StealthRecord = {
    created_at: isoUtcNow(),
    provider: provider.name,
    mode,
    sannysoft_webdriver_detected: null,
    sannysoft_headless_detected: null,
    sannysoft_user_agent_suspicious: null,
    sannysoft_raw: null,
    areyouheadless_detected: null,
    areyouheadless_raw: null,
    recaptcha_score: null,
    total_ms: null,
    success: false,
    error_stage: null,
    error_message: null,
  };

  try {
    stage = "session_create";
    console.error(`[create] ${provider.name} mode=${mode}`);

    const session = mode === "stealth"
      ? await createStealthWithRetry(provider)
      : await createWithRetry(provider);

    sessionId = session.id;

    stage = "session_connect";
    console.error(`[connect] ${provider.name}`);
    browser = await chromium.connectOverCDP(session.cdpUrl);

    // --- bot.sannysoft.com ---
    stage = "sannysoft";
    console.error(`[sannysoft] ${provider.name} mode=${mode}`);
    const sanny = await checkSannySoft(browser);
    record.sannysoft_webdriver_detected = sanny.webdriver_detected;
    record.sannysoft_headless_detected = sanny.headless_detected;
    record.sannysoft_user_agent_suspicious = sanny.user_agent_suspicious;
    record.sannysoft_raw = sanny.raw;
    console.error(
      `[sannysoft] webdriver=${sanny.webdriver_detected} headless=${sanny.headless_detected} ua=${sanny.user_agent_suspicious}`
    );

    // --- areyouheadless ---
    stage = "areyouheadless";
    console.error(`[areyouheadless] ${provider.name} mode=${mode}`);
    const ayh = await checkAreYouHeadless(browser);
    record.areyouheadless_detected = ayh.detected;
    record.areyouheadless_raw = ayh.raw;
    console.error(`[areyouheadless] detected=${ayh.detected}`);

    // --- antcpt.com reCAPTCHA score ---
    stage = "recaptcha";
    console.error(`[recaptcha] ${provider.name} mode=${mode}`);
    try {
      record.recaptcha_score = await checkRecaptchaScore(browser);
    } catch (e: any) {
      console.error(`[recaptcha_error] ${e?.message?.split("\n")[0] ?? e} — recording null`);
      record.recaptcha_score = null;
    }
    console.error(`[recaptcha] score=${record.recaptcha_score}`);

    record.success = true;
  } catch (e: any) {
    const message = e instanceof Error ? (e.stack ?? e.message) : `${e}`;
    record.error_stage = stage;
    record.error_message = message;
    console.error(`[error] stage=${stage} ${message}`);
  } finally {
    if (browser) {
      try {
        await browser.close();
      } catch {}
    }

    if (sessionId) {
      try {
        await provider.release(sessionId);
        console.error(`[released] ${provider.name} ${sessionId}`);
      } catch (e: any) {
        console.error(`[release_error] ${e?.message ?? e}`);
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
  const modesArg = getArg("modes", "default,stealth") ?? "default,stealth";
  const skipStealth = hasFlag("no-stealth");

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  const requestedModes: StealthMode[] = skipStealth
    ? ["default"]
    : (modesArg.split(",").map((m) => m.trim()) as StealthMode[]);

  const out = `results/stealth.jsonl`;
  fs.mkdirSync("results", { recursive: true });

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);

    const modes: StealthMode[] = requestedModes.filter((m) => {
      if (m === "stealth" && !provider.createStealth) {
        console.error(`[skip] ${provider.name} does not support stealth mode — skipping stealth run`);
        return false;
      }
      return true;
    });

    for (const mode of modes) {
      console.error(`\n=== ${provider.name} [${mode}] ===`);
      const record = await runStealthCheck(provider, mode);
      fs.appendFileSync(out, JSON.stringify(record) + "\n", { encoding: "utf-8" });
      console.error(`[written] ${out}`);

      // Brief pause between runs to avoid hammering providers
      await new Promise((r) => setTimeout(r, 2_000));
    }
  }

  console.error(`\n[done] results written to ${out}`);
}

main().catch((e) => {
  console.error(`[fatal] ${e?.stack ?? e?.message ?? e}`);
  process.exit(1);
});
