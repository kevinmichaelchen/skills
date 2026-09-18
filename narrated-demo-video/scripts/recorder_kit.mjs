// Recorder kit for narrated demo takes. Import it from a recorder script and run that script from the root of
// an app repository that depends on `@playwright/test`; the kit resolves Playwright from the working directory.
//
//   const take = await createTake({ outDir, durations, storageState, hide });
//   const { page, mark, waitForLine, clickLike, typeHuman, smoothScroll, pause } = take;
//   ... drive the journey, calling mark("vo:<key>") where each narration line should start ...
//   mark("end"); await take.finish();
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

// The kit lives outside the app repository, so resolve Playwright from the directory the recorder is run in.
const loadChromium = async () => {
  const require = createRequire(`${process.cwd()}/`);
  const playwright = await import(pathToFileURL(require.resolve("@playwright/test")).href);
  return playwright.chromium ?? playwright.default.chromium;
};

const CURSOR_CSS = `
  #__demo_cursor { position: fixed; left: 0; top: 0; width: 22px; height: 22px; border-radius: 50%;
    background: rgba(17,24,39,.55); border: 2px solid #fff; box-shadow: 0 1px 6px rgba(0,0,0,.35);
    z-index: 2147483647; pointer-events: none; transform: translate(720px, 450px);
    transition: transform .55s cubic-bezier(.22,.8,.3,1), width .12s, height .12s, background .12s; }
  #__demo_cursor.down { width: 16px; height: 16px; background: rgba(0,122,90,.8); }`;

export const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const rand = (min, max) => min + Math.random() * (max - min);

/**
 * @param {object} options
 * @param {string} options.outDir            where the .webm and marks.json land
 * @param {string} [options.durations]       path to { "<key>": seconds } for the narration lines
 * @param {string} [options.storageState]    Playwright storage state to start signed in
 * @param {string[]} [options.hide]          CSS selectors for dev-only chrome to hide
 * @param {{width:number,height:number}} [options.viewport]
 */
export async function createTake({ outDir, durations, storageState, hide = [], viewport = { width: 1440, height: 900 } }) {
  const chromium = await loadChromium();
  mkdirSync(outDir, { recursive: true });
  const lineSeconds = durations ? JSON.parse(readFileSync(durations, "utf8")) : {};

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport,
    recordVideo: { dir: outDir, size: viewport },
    colorScheme: "light",
    ...(storageState ? { storageState } : {}),
  });

  // Runs on every document: hides dev chrome and installs a scripted pointer the viewer can follow.
  await context.addInitScript(
    ([css, selectors]) => {
      const install = () => {
        if (document.getElementById("__demo_cursor")) return;
        const style = document.createElement("style");
        style.textContent = css + (selectors.length ? `${selectors.join(",")} { display: none !important; }` : "");
        document.documentElement.appendChild(style);
        const cursor = document.createElement("div");
        cursor.id = "__demo_cursor";
        document.documentElement.appendChild(cursor);
        window.__cursorTo = (x, y) => { cursor.style.transform = `translate(${x - 11}px, ${y - 11}px)`; };
        window.__cursorDown = (on) => cursor.classList.toggle("down", on);
      };
      if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
      else install();
    },
    [CURSOR_CSS, hide],
  );

  const page = await context.newPage();
  const t0 = Date.now();
  const marks = [];

  /** Record a named moment (ms since the take began). Use "vo:<key>" where a narration line should start. */
  const mark = (name) => {
    const ms = Date.now() - t0;
    marks.push({ name, ms });
    console.log(`${(ms / 1000).toFixed(1).padStart(6)}s  ${name}`);
    return ms;
  };

  /** Hold the scene until the line that began at `startMs` has finished, plus a breath. */
  const waitForLine = async (startMs, key, breathMs = 700) => {
    const seconds = lineSeconds[key];
    if (seconds === undefined) throw new Error(`no duration for narration line "${key}"`);
    const left = startMs + seconds * 1000 + breathMs - (Date.now() - t0);
    if (left > 0) await pause(left);
  };

  const cursorTo = async (x, y, settleMs = 650) => {
    await page.evaluate(([cx, cy]) => window.__cursorTo?.(cx, cy), [x, y]);
    await pause(settleMs);
  };

  /** Glide the pointer to a locator. Works for elements inside iframes too (boxes are in page coordinates). */
  const pointAt = async (locator, settleMs) => {
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    if (!box) throw new Error("pointAt: element has no bounding box");
    await cursorTo(box.x + box.width / 2, box.y + box.height / 2, settleMs);
  };

  const clickLike = async (locator) => {
    await pointAt(locator);
    await page.evaluate(() => window.__cursorDown?.(true));
    await pause(120);
    await locator.click();
    await page.evaluate(() => window.__cursorDown?.(false)).catch(() => {});
  };

  const smoothScroll = async (top, ms = 1600) => {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: "smooth" }), top);
    await pause(ms);
  };

  /** Type one character at a time with jitter, pausing longer after every `groupSize` characters. */
  const typeHuman = async (locator, text, { groupSize = 4 } = {}) => {
    for (let i = 0; i < text.length; i++) {
      await locator.pressSequentially(text[i]);
      await pause((i + 1) % groupSize === 0 ? rand(260, 420) : rand(85, 190));
    }
  };

  const close = async () => {
    writeFileSync(`${outDir}/marks.json`, JSON.stringify({ marks }, null, 2));
    await context.close(); // finalises the video; an unclosed context leaves a .webm with no duration
    await browser.close();
  };

  const finish = async () => {
    if (!marks.some((m) => m.name === "end")) mark("end");
    await page.screenshot({ path: `${outDir}/final.png` }).catch(() => {});
    await close();
    console.log("take finished:", outDir);
  };

  const fail = async (error) => {
    console.error("STEP FAILED:", String(error).split("\n").slice(0, 3).join(" | "));
    await page.screenshot({ path: `${outDir}/error.png` }).catch(() => {});
    const text = await page.locator("body").innerText().catch(() => "");
    console.log("url:", page.url(), "| page:", text.replace(/\s+/g, " ").slice(0, 300));
    await close();
    process.exit(1);
  };

  return { browser, context, page, durations: lineSeconds, mark, waitForLine, cursorTo, pointAt, clickLike, smoothScroll, typeHuman, pause, finish, fail };
}
