/**
 * all.ts — runs all 5 benchmarks sequentially for all providers.
 *
 * Usage:
 *   npm run all                        # run all benchmarks
 *   npm run all -- --update-readme     # run all benchmarks then update README
 *   npm run all -- --provider browserless,kernel   # specific providers only
 *   npm run all -- --no-warmup         # skip warmup runs
 */

import "dotenv/config";
import { spawnSync } from "node:child_process";
import { hasFlag, getArg } from "./utils/arg.js";

const ALL_PROVIDERS = "browserless,browserbase,anchorbrowser,hyperbrowser,kernel,steel";

function run(script: string, extraArgs: string[] = []): boolean {
  console.error(`\n${"=".repeat(60)}`);
  console.error(`Running: tsx ${script} ${extraArgs.join(" ")}`);
  console.error("=".repeat(60));

  const result = spawnSync(
    "npx",
    ["tsx", script, ...extraArgs],
    { stdio: "inherit", encoding: "utf-8" }
  );

  if (result.status !== 0) {
    console.error(`[all] FAILED: ${script} exited with code ${result.status}`);
    return false;
  }
  return true;
}

function main() {
  const providers = getArg("provider", ALL_PROVIDERS)!;
  const updateReadme = hasFlag("update-readme");
  const noWarmup = hasFlag("no-warmup");
  const idleMins = getArg("idle-mins", "1")!;

  const baseArgs = [
    `--provider`, providers,
    ...(noWarmup ? ["--no-warmup"] : []),
  ];

  const benchmarks: Array<{ script: string; args?: string[] }> = [
    { script: "src/cli.ts", args: baseArgs },
    { script: "src/benchmarks/2-idle-workflow.ts", args: [...baseArgs, "--idle-mins", idleMins] },
    { script: "src/benchmarks/3-stealth.ts", args: baseArgs },
    { script: "src/benchmarks/4-captcha.ts", args: [`--provider`, providers] },
    { script: "src/benchmarks/5-parallel.ts", args: baseArgs },
  ];

  let allPassed = true;
  for (const { script, args = [] } of benchmarks) {
    const ok = run(script, args);
    if (!ok) allPassed = false;
  }

  console.error(`\n${"=".repeat(60)}`);
  console.error(allPassed ? "[all] All benchmarks completed" : "[all] Some benchmarks failed");
  console.error("=".repeat(60));

  if (updateReadme) {
    console.error("\n[all] Updating README...");
    run("src/report.ts");
  }
}

main();
