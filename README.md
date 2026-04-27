# Hockay Wiki

Community-maintained wiki for [Hockay](https://hockay.com). Live at
**[hockay.wiki](https://hockay.wiki)**.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Click **Edit this page** at the
bottom of any article to open the `.mdx` source in GitHub's web editor—no
git required locally. For larger edits, clone the repo and run it locally.

## Stack

- [Astro](https://astro.build) + [Starlight](https://starlight.astro.build) (docs theme)
- [Tailwind v4](https://tailwindcss.com) via `@astrojs/starlight-tailwind`
- Deployed on [Cloudflare Workers](https://workers.cloudflare.com) via `@astrojs/cloudflare`

Content lives as `.mdx` files under `src/content/docs/` across five
collections: `guides`, `lore`, `teams`, `modifiers`, `glossary`.

## Local development

```bash
pnpm install
pnpm dev       # http://127.0.0.1:4321
pnpm build     # production build (uses Cloudflare adapter)
pnpm preview   # serve the build locally
```

## Deployment (Cloudflare Workers)

1. Build the project: `pnpm build`.
2. Deploy: `pnpm run deploy` (runs `wrangler deploy --config dist/server/wrangler.json`).
3. Set the `nodejs_compat` compatibility flag on the Worker if not already set.

## License

Content: community contributions licensed per the repository's LICENSE.
Code: MIT.
