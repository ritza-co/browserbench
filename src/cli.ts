import "dotenv/config";
import fs from "node:fs";
import { resolveProvider } from "./providers/index.js";
import { runBenchmark } from "./run.js";
import { getArg, hasFlag } from "./utils/arg.js";

async function main() {
  const providerArg = getArg("provider", process.env.PROVIDER ?? "browserless")!;
  const runs = Number(getArg("runs", process.env.RUNS ?? "10"));
  const url = getArg("url", process.env.URL ?? "https://example.com")!;
  const warmup = !hasFlag("no-warmup");

  const providerNames = providerArg
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);

  for (const providerName of providerNames) {
    const provider = resolveProvider(providerName);
    const out = `results/${providerName}.jsonl`;

    fs.mkdirSync("results", { recursive: true });
    if (fs.existsSync(out)) {
      fs.unlinkSync(out);
      console.error(`[reset] deleted existing ${out}`);
    }

    await runBenchmark(provider, { runs, url, out, warmup });
  }
}

main().catch((e) => {
  console.error(`[fatal] ${e?.stack ?? e?.message ?? e}`);
  process.exit(1);
});
