// Renders a title banner as a transparent PNG for `overlay.py --image`, for FFmpeg builds without `drawtext`.
// Run from the root of a repository that depends on `@playwright/test` (resolved from the working directory):
//   node <skill-dir>/scripts/make_title.mjs "Declined card" out/title.png [width]
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

// The kit lives outside the app repository, so resolve Playwright from the directory the recorder is run in.
const loadChromium = async () => {
  const require = createRequire(`${process.cwd()}/`);
  const playwright = await import(pathToFileURL(require.resolve("@playwright/test")).href);
  return playwright.chromium ?? playwright.default.chromium;
};
const chromium = await loadChromium();

const [text, out, width = "1440"] = process.argv.slice(2);
if (!text || !out) {
  console.error('usage: make_title.mjs "<text>" <out.png> [width]');
  process.exit(2);
}

const escaped = text.replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[ch]);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: Number(width), height: 110 }, deviceScaleFactor: 1 });
await page.setContent(`<html><body style="margin:0;background:transparent;display:flex;justify-content:center;padding-top:18px;font-family:-apple-system,Helvetica,Arial,sans-serif">
<div style="background:rgba(17,24,39,.86);color:#fff;font-size:34px;font-weight:600;padding:14px 30px;border-radius:12px">${escaped}</div></body></html>`);
await page.screenshot({ path: out, omitBackground: true });
await browser.close();
console.log("wrote", out);
