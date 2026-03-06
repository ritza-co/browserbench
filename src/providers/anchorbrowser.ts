import type { ProviderClient, ProviderSession } from "../types.js";
import Anchorbrowser from "anchorbrowser";
import { requireEnv } from "../utils/env.js";

export class AnchorBrowserProvider implements ProviderClient {
  readonly name = "ANCHORBROWSER";
  private _client: Anchorbrowser | null = null;

  private client(): Anchorbrowser {
    if (!this._client) {
      const apiKey = requireEnv("ANCHORBROWSER_API_KEY");
      this._client = new Anchorbrowser({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const session = await this.client().sessions.create();
    const id = session.data?.id;
    const cdpUrl = session.data?.cdp_url;
    if (!id || !cdpUrl) throw new Error("Invalid Anchorbrowser session response");
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    // extra_stealth requires Growth tier ($2,000/mo) — will fail on free tier
    const session = await this.client().sessions.create({
      browser: { extra_stealth: { active: true } },
      session: { proxy: { active: true } },
    } as any);
    const id = session.data?.id;
    const cdpUrl = session.data?.cdp_url;
    if (!id || !cdpUrl) throw new Error("Invalid Anchorbrowser session response");
    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    await this.client().sessions.delete(id);
  }
}
