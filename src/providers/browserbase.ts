import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import { Browserbase } from "@browserbasehq/sdk";

export class BrowserbaseProvider implements ProviderClient {
  readonly name = "BROWSERBASE";
  // Free tier: 1 concurrent session
  readonly maxConcurrency = 1;
  private _client: Browserbase | null = null;

  private client(): Browserbase {
    if (!this._client) {
      const apiKey = requireEnv("BROWSERBASE_API_KEY");
      this._client = new Browserbase({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const projectId = requireEnv("BROWSERBASE_PROJECT_ID");
    const session = await this.client().sessions.create({ projectId });
    const id = session?.id;
    const cdpUrl = session?.connectUrl;
    if (!id || !cdpUrl) throw new Error("Invalid Browserbase session response");
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    // advancedStealth is Scale plan only — basic stealth is always on by default
    const projectId = requireEnv("BROWSERBASE_PROJECT_ID");
    const session = await this.client().sessions.create({
      projectId,
      browserSettings: { advancedStealth: true },
    });
    const id = session?.id;
    const cdpUrl = session?.connectUrl;
    if (!id || !cdpUrl) throw new Error("Invalid Browserbase session response");
    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    const projectId = requireEnv("BROWSERBASE_PROJECT_ID");
    await this.client().sessions.update(id, {
      status: "REQUEST_RELEASE",
      projectId,
    });
  }
}
