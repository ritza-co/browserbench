import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import Kernel from "@onkernel/sdk";

export class KernelProvider implements ProviderClient {
  readonly name = "KERNEL";
  private _client: Kernel | null = null;

  private async client(): Promise<Kernel> {
    if (!this._client) {
      const apiKey = requireEnv("KERNEL_API_KEY");
      this._client = new Kernel({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const created = await (await this.client()).browsers.create();
    const id = created.session_id;
    const cdpUrl = created.cdp_ws_url;
    if (!id || !cdpUrl) throw new Error("Invalid Kernel session response");
    return { id, cdpUrl };
  }

  async release(id: string): Promise<void> {
    await (await this.client()).browsers.deleteByID(id);
  }
}
