import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import { Hyperbrowser } from "@hyperbrowser/sdk";

export class HyperbrowserProvider implements ProviderClient {
  readonly name = "HYPERBROWSER";
  // Free tier: 1 concurrent session
  readonly maxConcurrency = 1;
  private _client: Hyperbrowser | null = null;

  private client(): Hyperbrowser {
    if (!this._client) {
      const apiKey = requireEnv("HYPERBROWSER_API_KEY");
      this._client = new Hyperbrowser({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const session = await this.client().sessions.create();
    const id = session.id;
    const cdpUrl = session.wsEndpoint;
    if (!id || !cdpUrl) throw new Error("Invalid Hyperbrowser session response");
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    const session = await this.client().sessions.create({ useStealth: true });
    const id = session.id;
    const cdpUrl = session.wsEndpoint;
    if (!id || !cdpUrl) throw new Error("Invalid Hyperbrowser session response");
    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    await this.client().sessions.stop(id);
  }
}
