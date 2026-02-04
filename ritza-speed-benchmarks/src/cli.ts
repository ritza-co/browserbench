import "dotenv/config";
import fs from "node:fs";
import { resolveProvider } from "./providers/index.js";
import { runLoop } from "./run.js";
import { getArg } from "./utils/arg.js";

async function main() {
  const providerArg = getArg(
    "provider",
    process.env.PROVIDER || "browserbase"
  )!;
  const runs = Number(getArg("runs", process.env.RUNS || "10")); // Default to 10 runs
  const url = getArg("url", process.env.URL || "https://google.com/")!;
  const outArg = getArg("out", process.env.OUTPUT || undefined);

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);
    const out = outArg || `results/${providerName}.jsonl`;

    // Nuke existing file before starting
    if (fs.existsSync(out)) {
      fs.unlinkSync(out);
      console.error(`[RESET] Deleted existing ${out}`);
    }

    await runLoop(provider, { runs, url, out });
  }
}

main()
  .then(() => {
    process.exit(0);
  })
  .catch((e) => {
    console.error(`[FATAL] ${e?.stack || e?.message || e}`);
    process.exit(1);
  });
