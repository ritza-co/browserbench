import "dotenv/config";
import { resolveProvider } from "./providers/index.js";
import { runLoop } from "./run.js";
import { getArg } from "./utils/arg.js";

async function main() {
  const providerArg = getArg(
    "provider",
    process.env.PROVIDER || "browserbase"
  )!;
  const runs = Number(getArg("runs", process.env.RUNS || "5"));
  const url = getArg("url", process.env.URL || "https://google.com/")!;
  const outArg = getArg("out", process.env.OUTPUT || undefined);

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);
    const out = outArg || `results/${providerName}.jsonl`;
    await runLoop(provider, { runs, url, out });
  }
}

main().catch((e) => {
  console.error(`[FATAL] ${e?.stack || e?.message || e}`);
  process.exit(1);
});
