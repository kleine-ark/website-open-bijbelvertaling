#!/usr/bin/env node
// Stelt de web-assets samen die in de desktop-app (Tauri) gebundeld worden.
// Cross-platform (Linux + Windows CI): gebruikt alleen node:fs.
// Sluit bewust uit: audio/ (11 GB), git/venvs/scripts/docs en alle build-mappen.
import { cpSync, rmSync, mkdirSync, existsSync, readdirSync } from "node:fs";
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
