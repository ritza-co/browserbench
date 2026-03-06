import type { ProviderClient, ProviderSession } from "../types.js";

/**
 * Calls provider.create() with automatic retry on Kernel 429 rate-limit errors.
 * Other providers fail immediately on any error.
 */
export async function createWithRetry(provider: ProviderClient): Promise<ProviderSession> {
  return _retryCreate(() => provider.create(), provider.name);
}

export async function createStealthWithRetry(provider: ProviderClient): Promise<ProviderSession> {
  if (!provider.createStealth) throw new Error(`${provider.name} does not support stealth mode`);
  return _retryCreate(() => provider.createStealth!(), provider.name);
}

export async function createWithCaptchaRetry(provider: ProviderClient): Promise<ProviderSession> {
  if (!provider.createWithCaptcha) throw new Error(`${provider.name} does not support CAPTCHA solving`);
  return _retryCreate(() => provider.createWithCaptcha!(), provider.name);
}

async function _retryCreate(
  fn: () => Promise<ProviderSession>,
  providerName: string
): Promise<ProviderSession> {
  while (true) {
    try {
      return await fn();
    } catch (e: any) {
      const status = e?.status ?? e?.statusCode ?? e?.response?.status;
      const message = e instanceof Error ? e.message : `${e}`;
      const isRateLimit = status === 429 || /rate|limit|429|too many/i.test(message ?? "");
      if (providerName === "KERNEL" && isRateLimit) {
        console.error(`[rate_limit] KERNEL → retry in 30s`);
        await new Promise((r) => setTimeout(r, 30_000));
        continue;
      }
      throw e;
    }
  }
}
