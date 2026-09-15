#!/usr/bin/env node
/** Compile Flint ChartAssemblyInput JSON and render verified WEBP files. */

import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((pairs, value, index, values) => {
    if (value.startsWith('--')) pairs.push([value.slice(2), values[index + 1]]);
    return pairs;
  }, []),
);

if (!args.runtime || !args.specs || !args.out) {
  console.error('usage: render_flint.mjs --runtime <npm-prefix> --specs <dir> --out <dir>');
  process.exit(2);
}

const runtime = path.resolve(args.runtime, 'node_modules');
const importFrom = async (packageName, file) => import(pathToFileURL(path.join(runtime, packageName, file)));
const [{ assembleVegaLite }, vegaLite, vega, sharpModule] = await Promise.all([
  importFrom('flint-chart', 'dist/index.js'),
  importFrom('vega-lite', 'build/index.js'),
  importFrom('vega', 'build/vega.module.js'),
  importFrom('sharp', 'lib/index.js'),
]);
const sharp = sharpModule.default;

await fs.mkdir(args.out, { recursive: true });
const files = (await fs.readdir(args.specs)).filter((name) => name.endsWith('.json')).sort();
for (const file of files) {
  const name = path.basename(file, '.json');
  const input = JSON.parse(await fs.readFile(path.join(args.specs, file), 'utf8'));
  const vlSpec = assembleVegaLite(input);
  // Flint owns chart structure. This narrow post-compile presentation tweak
  // prevents Vega's default temporal formatter from reducing every tick to
  // the unhelpful repeated label ":30" in short CI timelines. The UTC scale
  // keeps the static image faithful to GitHub's ISO timestamps regardless of
  // the machine that renders it.
  if (name.endsWith('timeline') && vlSpec.encoding?.x?.axis) {
    vlSpec.encoding.x.axis.format = '%H:%M';
    vlSpec.encoding.x.scale = { type: 'utc' };
  }
  const compiled = vegaLite.compile(vlSpec).spec;
  const view = new vega.View(vega.parse(compiled), { renderer: 'none' });
  const svg = await view.toSVG();
  const webpPath = path.join(args.out, `${name}.webp`);
  await sharp(Buffer.from(svg)).webp({ quality: 92, effort: 6 }).toFile(webpPath);
  await fs.writeFile(path.join(args.out, `${name}.vega-lite.json`), JSON.stringify(vlSpec, null, 2) + '\n');
  const metadata = await sharp(webpPath).metadata();
  console.log(`${name}: ${metadata.width}x${metadata.height} ${metadata.format}`);
}
