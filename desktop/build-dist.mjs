#!/usr/bin/env node
// Stelt de web-assets samen die in de desktop-app (Tauri) gebundeld worden.
// Cross-platform (Linux + Windows CI): gebruikt alleen node:fs.
// Sluit bewust uit: extern gepubliceerde audio, git/venvs/scripts/docs en build-mappen.
import { cpSync, rmSync, mkdirSync, existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const out = join(here, "dist");

// Mappen die compleet meegaan (alle bijbeldata, frontend, assets).
const DIRS = ["css", "js", "data", "icons", "images", "fonts"];
// Losse bestanden in de repo-root die de app nodig heeft.
const FILE_GLOB = (name) => name.endsWith(".html") && name !== "mockup-leesversie.html";
const FILES = ["favicon.svg", "manifest.json", "sw.js", "embed.js"];

console.log("[build-dist] volledige naslagteksten bouwen");
const built = spawnSync(
  process.env.PYTHON || "python",
  [join(root, "scripts", "build_naslag_teksten.py")],
  { cwd: root, stdio: "inherit" },
);
if (built.error || built.status !== 0) {
  throw new Error("bouwen naslagteksten mislukt", { cause: built.error });
}

console.log("[build-dist] schoonmaken:", out);
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

for (const d of DIRS) {
  const src = join(root, d);
  if (!existsSync(src)) { console.warn("[build-dist] overslaan (ontbreekt):", d); continue; }
  cpSync(src, join(out, d), { recursive: true });
  console.log("[build-dist] map:", d);
}

const htmls = readdirSync(root).filter(FILE_GLOB);
for (const name of [...htmls, ...FILES]) {
  const src = join(root, name);
  if (!existsSync(src)) { console.warn("[build-dist] overslaan (ontbreekt):", name); continue; }
  cpSync(src, join(out, name));
}
console.log("[build-dist] klaar — bestanden:", readdirSync(out).length, "items in", out);
