import type { ProviderClient } from "../types.js";
import { BrowserlessProvider } from "./browserless.js";
import { BrowserbaseProvider } from "./browserbase.js";
import { AnchorBrowserProvider } from "./anchorbrowser.js";
import { HyperbrowserProvider } from "./hyperbrowser.js";
import { KernelProvider } from "./kernel.js";
import { SteelProvider } from "./steel.js";

export function resolveProvider(name: string): ProviderClient {
  const key = name.trim().toLowerCase();

  if (key === "browserless") return new BrowserlessProvider();
  if (key === "browserbase" || key === "bb") return new BrowserbaseProvider();
  if (key === "anchorbrowser" || key === "anchor") return new AnchorBrowserProvider();
  if (key === "hyperbrowser" || key === "hyper") return new HyperbrowserProvider();
  if (key === "kernel") return new KernelProvider();
  if (key === "steel") return new SteelProvider();

  throw new Error(`Unknown provider: ${name}. Valid options: browserless, browserbase, anchorbrowser, hyperbrowser, kernel, steel`);
}
