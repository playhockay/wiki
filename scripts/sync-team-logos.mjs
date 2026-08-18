// Sync the 48 team logos from the Hockay app into `public/team-logos/`.
//
// The source SVGs are traced exports: ~2.2 MB across the set, carrying 3-6
// decimal places on viewBoxes of 783 units and up. Rounding coordinates to
// integers is ~0.02 css px of error at the 32 px the grid renders them at,
// and takes the set to ~390 KB.
//
// Only the *_color.svg variants are copied. The *_monochrome.svg files are the
// same geometry with fills swapped to #1C1C1C/#FEFEFE; the grid gets that look
// from `filter: grayscale(1)` instead of a second download.
//
// Geometry-touching SVGO plugins are disabled — mergePaths and removeHiddenElems
// silently dropped a <path> from vla_color. Verified after every run below.
//
// Usage: node scripts/sync-team-logos.mjs [path-to-hockay-repo]

import { execFileSync } from "node:child_process";
import {
	mkdirSync,
	mkdtempSync,
	readdirSync,
	readFileSync,
	rmSync,
	writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const HOCKAY = process.argv[2] ?? join(process.env.HOME, "hockay");
const SRC = join(HOCKAY, "apps/web/public/team_logos");
const OUT = fileURLToPath(new URL("../public/team-logos/", import.meta.url));

// Not teams — the two All-Star squads. They have logos but never appear in the grid.
const EXCLUDE = new Set(["asv", "asg"]);

const SVGO_CONFIG = `export default {
  multipass: true,
  plugins: [
    { name: "preset-default", params: { overrides: {
      removeViewBox: false,
      mergePaths: false,
      removeHiddenElems: false,
      removeUselessStrokeAndFill: false,
      convertShapeToPath: false,
      cleanupNumericValues: { floatPrecision: 0 },
      convertPathData: { floatPrecision: 0, transformPrecision: 1 },
    } } },
    "removeDimensions",
  ],
};
`;

const countPaths = (s) => s.split("<path").length - 1;
const countSubpaths = (s) =>
	[...s.matchAll(/\sd="([^"]*)"/g)].reduce(
		(n, m) => n + (m[1].match(/[Mm]/g)?.length ?? 0),
		0,
	);

const work = mkdtempSync(join(tmpdir(), "hockay-logos-"));
const configPath = join(work, "svgo.config.mjs");
writeFileSync(configPath, SVGO_CONFIG);

const ids = readdirSync(SRC)
	.filter((f) => f.endsWith("_color.svg"))
	.map((f) => f.replace("_color.svg", ""))
	.filter((id) => !EXCLUDE.has(id))
	.sort();

const originals = new Map();
for (const id of ids) {
	const svg = readFileSync(join(SRC, `${id}_color.svg`), "utf8");
	originals.set(id, svg);
	writeFileSync(join(work, `${id}.svg`), svg);
}

execFileSync(
	"npx",
	["--yes", "svgo@3", "-f", work, "-q", "--config", configPath],
	{
		stdio: "inherit",
	},
);

mkdirSync(OUT, { recursive: true });
let before = 0;
let after = 0;
const broken = [];

for (const id of ids) {
	const src = originals.get(id);
	const out = readFileSync(join(work, `${id}.svg`), "utf8");

	// A dropped path is invisible in a byte count and obvious on the page.
	if (
		countPaths(src) !== countPaths(out) ||
		countSubpaths(src) !== countSubpaths(out)
	) {
		broken.push(id);
		continue;
	}
	before += Buffer.byteLength(src);
	after += Buffer.byteLength(out);
	writeFileSync(join(OUT, `${id}.svg`), out);
}

rmSync(work, { recursive: true, force: true });

if (broken.length) {
	console.error(`geometry changed, not written: ${broken.join(", ")}`);
	process.exit(1);
}

const kb = (n) => `${(n / 1024).toFixed(0)} KB`;
console.log(
	`${ids.length} logos · ${kb(before)} → ${kb(after)} (${((1 - after / before) * 100).toFixed(0)}% smaller)`,
);
