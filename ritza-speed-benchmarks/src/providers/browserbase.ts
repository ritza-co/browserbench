import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import { Browserbase } from "@browserbasehq/sdk";

export class BrowserbaseProvider implements ProviderClient {
  readonly name = "BROWSERBASE";
  private _client: Browserbase | null = null;

  private async client(): Promise<Browserbase | null> {
    if (!this._client) {
      const apiKey = requireEnv("BROWSERBASE_API_KEY");
      this._client = new Browserbase({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const projectId = requireEnv("BROWSERBASE_PROJECT_ID");
    const session = await (await this.client())?.sessions.create({ projectId });
    const id = session?.id;
    const cdpUrl = session?.connectUrl;
    if (!id || !cdpUrl) throw new Error("Invalid Browserbase session response");
    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    const projectId = requireEnv("BROWSERBASE_PROJECT_ID");
    await (
      await this.client()
    )?.sessions.update(id, { status: "REQUEST_RELEASE", projectId });
  }
}
