export type ProviderName =
  | "BROWSERLESS"
  | "BROWSERBASE"
  | "ANCHORBROWSER"
  | "HYPERBROWSER"
  | "KERNEL"
  | "STEEL";

export type MetricRecord = {
  created_at: string;
  id: string | null;
  session_creation_ms: number | null;
  session_connect_ms: number | null;
  page_goto_ms: number | null;
  session_release_ms: number | null;
  provider: ProviderName;
  success: boolean;
  error_stage: string | null;
  error_message: string | null;
};

export type ProviderSession = {
  id: string;
  cdpUrl: string;
};

export interface ProviderClient {
  readonly name: ProviderName;
  create(): Promise<ProviderSession>;
  release(id: string): Promise<void>;

  // Optional per-benchmark variants. If absent, the benchmark falls back to create().
  createStealth?(): Promise<ProviderSession>;
  createWithCaptcha?(): Promise<ProviderSession>;

  // Free-tier concurrency limit. Undefined = no known limit.
  readonly maxConcurrency?: number;
}
