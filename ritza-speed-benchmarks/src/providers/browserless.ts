import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";

export class BrowserlessProvider implements ProviderClient {
  readonly name = "BROWSERLESS";
  private apiKey: string | null = null;
  private baseUrl: string = "https://chrome.browserless.io";

  private getApiKey(): string {
    if (!this.apiKey) {
      this.apiKey = requireEnv("BROWSERLESS_API_KEY");
    }
    return this.apiKey;
  }

  async create(): Promise<ProviderSession> {
    // Browserless uses a simple CDP endpoint with API key in query string
    // No explicit session creation API - CDP endpoint handles it
    const apiKey = this.getApiKey();
    const cdpUrl = `wss://${apiKey}@chrome.browserless.io`;

    // Generate a pseudo-ID since Browserless doesn't return one
    const id = `browserless-${Date.now()}-${Math.random().toString(36).substring(7)}`;

    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    // Browserless automatically closes sessions when CDP connection is dropped
    // No explicit release API call needed
    return Promise.resolve();
  }
}
