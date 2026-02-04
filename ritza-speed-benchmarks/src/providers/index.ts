import type { ProviderClient } from "../types.js";
import { BrowserbaseProvider } from "./browserbase.js";
import { AnchorBrowserProvider } from "./anchorbrowser.js";
import { BrowserlessProvider } from "./browserless.js";

const ALIAS_MAP: Record<string, string> = {
  bb: "browserbase",
  anchor: "anchorbrowser",
  browserless: "browserless",
};

export function resolveProvider(name: string): ProviderClient {
  const normalized = (ALIAS_MAP[name.toLowerCase()] || name).toUpperCase();

  switch (normalized) {
    case "BROWSERBASE":
      return new BrowserbaseProvider();
    case "ANCHORBROWSER":
      return new AnchorBrowserProvider();
    case "BROWSERLESS":
      return new BrowserlessProvider();
    default:
      throw new Error(`Unknown provider: ${name}`);
  }
}
