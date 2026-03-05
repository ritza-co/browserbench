import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import Steel from "steel-sdk";

export class SteelProvider implements ProviderClient {
  readonly name = "STEEL";
  private _client: Steel | null = null;


  private client(): Steel {
    if (!this._client) {
      const apiKey = requireEnv("STEEL_API_KEY");
      this._client = new Steel({ steelAPIKey: apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const apiKey = requireEnv("STEEL_API_KEY");
    const session = await this.client().sessions.create();
    const id = session?.id;
    const websocketUrl = session?.websocketUrl;
    const cdpUrl = `${websocketUrl}&apiKey=${apiKey}`;
    if (!id || !cdpUrl) throw new Error("Invalid Steel session response");
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    const apiKey = requireEnv("STEEL_API_KEY");
    const session = await this.client().sessions.create({
      stealthConfig: { humanizeInteractions: true },
    });
    const id = session?.id;
    const websocketUrl = session?.websocketUrl;
    if (!id || !websocketUrl) throw new Error("Invalid Steel session response");
    return { id, cdpUrl: `${websocketUrl}&apiKey=${apiKey}` };
  }

  async release(id: string): Promise<void> {
    await this.client().sessions.release(id);
  }
}
