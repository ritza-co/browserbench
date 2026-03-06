import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";

export class BrowserlessProvider implements ProviderClient {
  readonly name = "BROWSERLESS";
  // Free tier: 2 concurrent browsers
  readonly maxConcurrency = 2;

  async create(): Promise<ProviderSession> {
    const apiKey = requireEnv("BROWSERLESS_API_KEY");
    // Browserless v2 endpoint — no explicit session creation API,
    // the CDP connection itself starts the session
    const cdpUrl = `wss://production-sfo.browserless.io?token=${apiKey}`;
    const id = `browserless-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    const apiKey = requireEnv("BROWSERLESS_API_KEY");
    const cdpUrl = `wss://production-sfo.browserless.io?token=${apiKey}&stealth=true`;
    const id = `browserless-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    return { id, cdpUrl };
  }

  async createWithCaptcha(): Promise<ProviderSession> {
    const apiKey = requireEnv("BROWSERLESS_API_KEY");
    // /stealth endpoint with solveCaptchas=true — costs 10 units per solve
    const cdpUrl = `wss://production-sfo.browserless.io/stealth?token=${apiKey}&solveCaptchas=true`;
    const id = `browserless-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    return { id, cdpUrl };
  }

  async release(_id: string): Promise<void> {
    // Session is released automatically when the CDP connection closes
  }
}
