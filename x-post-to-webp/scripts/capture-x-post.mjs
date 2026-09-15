#!/usr/bin/env node

import { spawn } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

const CHROME_CANDIDATES = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
];

const CWEBP_CANDIDATES = [
  "/opt/homebrew/bin/cwebp",
  "/usr/local/bin/cwebp",
  "/usr/bin/cwebp",
];

function usage() {
  console.error(`Usage: capture-x-post.mjs [options] <x-status-url>...

Options:
  --output-dir DIR   Destination directory (default: current directory)
  --theme THEME      light or dark (default: light)
  --scale NUMBER     Output scale from 1 to 3 (default: 3)
  --chrome PATH      Chrome/Chromium executable
  --cwebp PATH       cwebp executable for lossless encoding
  --timeout MS       Per-post render timeout (default: 20000)
  -h, --help         Show this help`);
}

function parseArgs(argv) {
  const options = {
    outputDir: process.cwd(),
    theme: "light",
    scale: 3,
    timeout: 20_000,
    chrome: process.env.CHROME_PATH,
    cwebp: process.env.CWEBP_PATH,
    urls: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") return { ...options, help: true };
    if (["--output-dir", "--theme", "--scale", "--chrome", "--cwebp", "--timeout"].includes(arg)) {
      const value = argv[++index];
      if (!value) throw new Error(`${arg} requires a value`);
      if (arg === "--output-dir") options.outputDir = path.resolve(value);
      if (arg === "--theme") options.theme = value;
      if (arg === "--scale") options.scale = Number(value);
      if (arg === "--chrome") options.chrome = value;
      if (arg === "--cwebp") options.cwebp = value;
      if (arg === "--timeout") options.timeout = Number(value);
    } else if (arg.startsWith("-")) {
      throw new Error(`Unknown option: ${arg}`);
    } else {
      options.urls.push(arg);
    }
  }
  if (!options.urls.length) throw new Error("Provide at least one X status URL");
  if (!["light", "dark"].includes(options.theme)) throw new Error("--theme must be light or dark");
  if (!Number.isFinite(options.scale) || options.scale < 1 || options.scale > 3) {
    throw new Error("--scale must be between 1 and 3");
  }
  if (!Number.isInteger(options.timeout) || options.timeout < 1_000) {
    throw new Error("--timeout must be an integer of at least 1000 ms");
  }
  return options;
}

function parsePostUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`Invalid URL: ${value}`);
  }
  const host = url.hostname.toLowerCase().replace(/^www\./, "");
  if (!["x.com", "twitter.com"].includes(host)) throw new Error(`Not an X/Twitter URL: ${value}`);
  const match = url.pathname.match(/^\/([^/]+)\/status\/(\d+)/);
  if (!match) throw new Error(`Not an X/Twitter status URL: ${value}`);
  return {
    canonicalUrl: `https://x.com/${match[1]}/status/${match[2]}`,
    handle: match[1],
    id: match[2],
  };
}

async function findChrome(explicitPath) {
  const { access } = await import("node:fs/promises");
  const candidates = explicitPath ? [path.resolve(explicitPath)] : CHROME_CANDIDATES;
  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {}
  }
  throw new Error("Chrome/Chromium not found; pass --chrome PATH or set CHROME_PATH");
}

async function findCwebp(explicitPath) {
  const { access } = await import("node:fs/promises");
  const candidates = explicitPath ? [path.resolve(explicitPath)] : CWEBP_CANDIDATES;
  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {}
  }
  throw new Error("cwebp not found; install the WebP tools, pass --cwebp PATH, or set CWEBP_PATH");
}

async function encodeLosslessWebp(cwebpPath, pngData) {
  const workDir = await mkdtemp(path.join(tmpdir(), "x-post-encode-"));
  const inputPath = path.join(workDir, "capture.png");
  const outputPath = path.join(workDir, "capture.webp");
  try {
    await writeFile(inputPath, pngData);
    const child = spawn(cwebpPath, ["-quiet", "-lossless", "-z", "9", inputPath, "-o", outputPath], {
      stdio: ["ignore", "ignore", "pipe"],
    });
    const stderr = [];
    child.stderr.on("data", (chunk) => stderr.push(chunk));
    const code = await new Promise((resolve, reject) => {
      child.once("error", reject);
      child.once("close", resolve);
    });
    if (code !== 0) {
      throw new Error(`cwebp failed (code ${code}): ${Buffer.concat(stderr).toString("utf8").trim()}`);
    }
    return await readFile(outputPath);
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }
}

async function fetchEmbed(post, theme) {
  const endpoint = new URL("https://publish.twitter.com/oembed");
  endpoint.searchParams.set("url", post.canonicalUrl);
  endpoint.searchParams.set("dnt", "true");
  endpoint.searchParams.set("omit_script", "true");
  endpoint.searchParams.set("theme", theme);
  endpoint.searchParams.set("align", "center");
  const response = await fetch(endpoint, { signal: AbortSignal.timeout(15_000) });
  if (!response.ok) throw new Error(`X oEmbed returned HTTP ${response.status}`);
  const embed = await response.json();
  if (!embed.html?.includes("twitter-tweet")) throw new Error("X oEmbed did not return a post embed");
  return embed.html;
}

function htmlDocument(embedHtml, theme) {
  const background = theme === "dark" ? "#000" : "#fff";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    html,body{margin:0;padding:0;background:${background};overflow:hidden}
    body{width:650px;min-height:2200px}
    .twitter-tweet{margin:16px auto!important}
  </style></head><body>${embedHtml}
  <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
  </body></html>`;
}

class Cdp {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message));
      else pending.resolve(message.result);
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }
}

async function connectTarget(debugPort) {
  const response = await fetch(`http://127.0.0.1:${debugPort}/json/new?about:blank`, { method: "PUT" });
  if (!response.ok) throw new Error(`Could not create Chrome target: HTTP ${response.status}`);
  const target = await response.json();
  const socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", () => reject(new Error("Could not connect to Chrome")), { once: true });
  });
  return { cdp: new Cdp(socket), socket, targetId: target.id };
}

async function waitForEmbed(cdp, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let previousHeight = 0;
  let stableReads = 0;
  while (Date.now() < deadline) {
    const result = await cdp.send("Runtime.evaluate", {
      expression: `(() => {
        const frame = document.querySelector(
          'iframe.twitter-tweet-rendered, iframe[id^="twitter-widget"], twitter-widget.twitter-tweet-rendered'
        );
        if (!frame) return null;
        const rect = frame.getBoundingClientRect();
        return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
      })()`,
      returnByValue: true,
    });
    const rect = result.result?.value;
    if (rect?.width > 300 && rect?.height > 100) {
      stableReads = Math.abs(rect.height - previousHeight) < 0.5 ? stableReads + 1 : 0;
      previousHeight = rect.height;
      if (stableReads >= 3) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return rect;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 350));
  }
  throw new Error(`Timed out after ${timeoutMs} ms waiting for the rendered X embed`);
}

async function renderPost(debugPort, post, options) {
  const embedHtml = await fetchEmbed(post, options.theme);
  const document = htmlDocument(embedHtml, options.theme);
  const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(document)}`;
  const { cdp, socket, targetId } = await connectTarget(debugPort);
  try {
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    await cdp.send("Emulation.setDeviceMetricsOverride", {
      width: 650,
      height: 2200,
      deviceScaleFactor: 0,
      mobile: false,
    });
    await cdp.send("Page.navigate", { url: dataUrl });
    const rect = await waitForEmbed(cdp, options.timeout);
    const clip = {
      x: Math.max(0, Math.floor(rect.x)),
      y: Math.max(0, Math.floor(rect.y)),
      width: Math.ceil(rect.width),
      height: Math.ceil(rect.height),
      scale: 1,
    };
    const screenshot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: true,
      clip,
    });
    const filename = `${post.handle}-${post.id}.webp`;
    const outputPath = path.join(options.outputDir, filename);
    const pngData = Buffer.from(screenshot.data, "base64");
    const webpData = await encodeLosslessWebp(options.cwebp, pngData);
    await writeFile(outputPath, webpData);
    return {
      outputPath,
      width: Math.round(clip.width * options.scale),
      height: Math.round(clip.height * options.scale),
    };
  } finally {
    socket.close();
    await fetch(`http://127.0.0.1:${debugPort}/json/close/${targetId}`).catch(() => {});
  }
}

async function launchChrome(chromePath, deviceScaleFactor) {
  const profileDir = await mkdtemp(path.join(tmpdir(), "x-post-to-webp-"));
  const child = spawn(chromePath, [
    "--headless=new",
    "--remote-debugging-port=0",
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
    "--hide-scrollbars",
    `--force-device-scale-factor=${deviceScaleFactor}`,
    "about:blank",
  ], { stdio: ["ignore", "ignore", "pipe"] });

  const debugPort = await new Promise((resolve, reject) => {
    let stderr = "";
    const timer = setTimeout(() => reject(new Error("Timed out launching Chrome")), 10_000);
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
      const match = stderr.match(/DevTools listening on ws:\/\/127\.0\.0\.1:(\d+)/);
      if (match) {
        clearTimeout(timer);
        resolve(Number(match[1]));
      }
    });
    child.once("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Chrome exited before startup (code ${code})`));
    });
  });
  return { child, debugPort, profileDir };
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    usage();
    return;
  }
  const posts = options.urls.map(parsePostUrl);
  options.chrome = await findChrome(options.chrome);
  options.cwebp = await findCwebp(options.cwebp);
  await mkdir(options.outputDir, { recursive: true });
  const { child, debugPort, profileDir } = await launchChrome(options.chrome, options.scale);
  let failed = false;
  try {
    for (const post of posts) {
      try {
        const result = await renderPost(debugPort, post, options);
        console.log(JSON.stringify({
          url: post.canonicalUrl,
          output: result.outputPath,
          width: result.width,
          height: result.height,
          theme: options.theme,
        }));
      } catch (error) {
        failed = true;
        console.error(JSON.stringify({ url: post.canonicalUrl, error: error.message }));
      }
    }
  } finally {
    child.kill("SIGTERM");
    await new Promise((resolve) => child.once("exit", resolve));
    await rm(profileDir, { recursive: true, force: true });
  }
  if (failed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
});
