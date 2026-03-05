import type { ProviderClient, ProviderSession } from "../types.js";
import { requireEnv } from "../utils/env.js";
import Kernel from "@onkernel/sdk";

export class KernelProvider implements ProviderClient {
  readonly name = "KERNEL";
  private _client: Kernel | null = null;


  private client(): Kernel {
    if (!this._client) {
      const apiKey = requireEnv("KERNEL_API_KEY");
      this._client = new Kernel({ apiKey });
    }
    return this._client;
  }

  async create(): Promise<ProviderSession> {
    const created = await this.client().browsers.create();
    const id = created.session_id;
    const cdpUrl = created.cdp_ws_url;
    if (!id || !cdpUrl) throw new Error("Invalid Kernel session response");
    return { id, cdpUrl };
  }

  async createStealth(): Promise<ProviderSession> {
    const created = await this.client().browsers.create({ stealth: true });
    const id = created.session_id;
    const cdpUrl = created.cdp_ws_url;
    if (!id || !cdpUrl) throw new Error("Invalid Kernel session response");
    return { id, cdpUrl };
  }

  // Kernel CAPTCHA solving is part of stealth: true — same session type
  createWithCaptcha = this.createStealth;

  async release(id: string): Promise<void> {
    await this.client().browsers.deleteByID(id);
  }
}
