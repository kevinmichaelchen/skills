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
  // Flint owns chart structure. These narrow presentation fixes preserve full
  // author names and make dense monthly labels read like months and integers.
  if (name === 'contributor-scale-recency' && Array.isArray(vlSpec.hconcat)) {
    const bars = vlSpec.hconcat[0];
    if (bars?.encoding?.y?.axis) {
      bars.encoding.y.axis.labelLimit = 250;
      bars.encoding.y.axis.labelPadding = 250;
    }
    if (bars?.encoding?.color?.legend) bars.encoding.color.legend.title = 'Days since activity';
    const values = vlSpec.hconcat[1];
    if (values?.title) {
      values.width = 72;
      values.title.limit = 68;
    }
  }
  if (name === 'contributor-activity-heatmap' && Array.isArray(vlSpec.layer)) {
    for (const layer of vlSpec.layer) {
      if (layer.encoding?.x?.axis) {
        layer.encoding.x.axis.format = '%b';
        layer.encoding.x.axis.tickCount = 'month';
      }
      if (layer.encoding?.text) layer.encoding.text.format = 'd';
      if (layer.encoding?.color?.legend) layer.encoding.color.legend.title = 'Monthly commits';
    }
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
