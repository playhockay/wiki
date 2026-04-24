// @ts-check

import { readFile, rename, writeFile } from "node:fs/promises";
import cloudflare from "@astrojs/cloudflare";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import starlight from "@astrojs/starlight";
import keystatic from "@keystatic/astro";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "astro/config";
import remarkInjectMdxComponents from "./src/lib/remark-inject-mdx-components.mjs";

// @astrojs/sitemap emits `sitemap-index.xml`; rename to `sitemap.xml` so the
// canonical URL matches what robots.txt advertises.
/** @returns {import('astro').AstroIntegration} */
const renameSitemapIndex = () => ({
	name: "rename-sitemap-index",
	hooks: {
		"astro:build:done": async ({ dir }) => {
			const from = new URL("sitemap-index.xml", dir);
			const to = new URL("sitemap.xml", dir);
			try {
				await rename(from, to);
			} catch (err) {
				if (/** @type {NodeJS.ErrnoException} */ (err).code !== "ENOENT") throw err;
			}
		},
	},
});

// The Cloudflare adapter auto-wires a `SESSION` KV binding for Astro's
// built-in sessions API, but nothing in the wiki calls `Astro.session`. Without
// a pre-existing namespace id wrangler tries to provision one on deploy and
// collides with any prior namespace of the same name. Strip the binding.
/** @returns {import('astro').AstroIntegration} */
const stripSessionKvBinding = () => ({
	name: "strip-session-kv-binding",
	hooks: {
		"astro:build:done": async () => {
			const path = new URL("./dist/server/wrangler.json", import.meta.url);
			let raw;
			try {
				raw = await readFile(path, "utf8");
			} catch (err) {
				if (/** @type {NodeJS.ErrnoException} */ (err).code === "ENOENT") return;
				throw err;
			}
			const config = JSON.parse(raw);
			if (!Array.isArray(config.kv_namespaces)) return;
			const filtered = config.kv_namespaces.filter(
				(/** @type {{ binding?: string }} */ ns) => ns.binding !== "SESSION",
			);
			if (filtered.length === config.kv_namespaces.length) return;
			config.kv_namespaces = filtered;
			if (config.previews?.kv_namespaces) {
				config.previews.kv_namespaces = config.previews.kv_namespaces.filter(
					(/** @type {{ binding?: string }} */ ns) => ns.binding !== "SESSION",
				);
			}
			await writeFile(path, JSON.stringify(config));
		},
	},
});

// The Cloudflare adapter emits `/editor/*  /keystatic/*/index.html  301`, which
// Cloudflare's `_redirects` validator rejects because `/index.html` is stripped
// automatically and could theoretically loop. Rewrite the splat rule to use
// `:splat` and drop the `/index.html` suffix.
/** @returns {import('astro').AstroIntegration} */
const fixCloudflareRedirects = () => ({
	name: "fix-cloudflare-redirects",
	hooks: {
		"astro:build:done": async ({ dir }) => {
			const path = new URL("_redirects", dir);
			let contents;
			try {
				contents = await readFile(path, "utf8");
			} catch (err) {
				if (/** @type {NodeJS.ErrnoException} */ (err).code === "ENOENT") return;
				throw err;
			}
			const patched = contents.replace(
				/\/keystatic\/\*\/index\.html/g,
				"/keystatic/:splat",
			);
			if (patched !== contents) await writeFile(path, patched);
		},
	},
});

// Cloudflare adapter treats SSR deps as Workers-compatible, which breaks
// Node-only deps (e.g. astro-expressive-code → postcss) during Vite's SSR
// dep optimization in dev. Only apply the adapter for production builds.
const isBuild = process.argv.includes("build");

export default defineConfig({
	site: "https://hockay.wiki",
	output: "server",
	...(isBuild ? { adapter: cloudflare({ prerenderEnvironment: "node" }) } : {}),
	// /editor is the public-facing URL; Keystatic's client-side router
	// hardcodes /keystatic as its base path, so we redirect to the real mount.
	redirects: {
		"/editor": "/keystatic",
		"/editor/[...params]": "/keystatic/[...params]",
	},
	vite: {
		plugins: [tailwindcss()],
	},
	markdown: {
		remarkPlugins: [remarkInjectMdxComponents],
	},
	integrations: [
		react(),
		starlight({
			title: "Hockay Wiki",
			customCss: ["./src/styles/hockay.css"],
			head: [
				{
					tag: "link",
					attrs: { rel: "preconnect", href: "https://fonts.googleapis.com" },
				},
				{
					tag: "link",
					attrs: {
						rel: "preconnect",
						href: "https://fonts.gstatic.com",
						crossorigin: "",
					},
				},
				{
					tag: "link",
					attrs: {
						rel: "stylesheet",
						href:
							"https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&family=Young+Serif&display=swap",
					},
				},
			],
			social: [
				{
					icon: "github",
					label: "GitHub",
					href: "https://github.com/playhockay/wiki",
				},
				{
					icon: "discord",
					label: "Discord",
					href: "https://discord.gg/DdzbFY6vzp",
				},
			],
			editLink: {
				baseUrl: "https://github.com/playhockay/wiki/edit/main/",
			},
			components: {
				SiteTitle: "./src/components/overrides/SiteTitle.astro",
				Footer: "./src/components/overrides/Footer.astro",
			},
			sidebar: [
				{ label: "Guides", autogenerate: { directory: "guides" } },
				{ label: "Lore", autogenerate: { directory: "lore" } },
				{
					label: "Teams",
					autogenerate: { directory: "teams" },
					collapsed: true,
				},
				{ label: "Modifiers", autogenerate: { directory: "modifiers" } },
				{ label: "Glossary", autogenerate: { directory: "glossary" } },
			],
		}),
		mdx(),
		sitemap(),
		renameSitemapIndex(),
		keystatic(),
		fixCloudflareRedirects(),
		stripSessionKvBinding(),
	],
});
