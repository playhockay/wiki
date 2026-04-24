# Hockay Wiki

Community-maintained wiki for [Hockay](https://hockay.com). Live at
**[hockay.wiki](https://hockay.wiki)**.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Two ways:

1. **Browser editor**—sign in at [hockay.wiki/editor](https://hockay.wiki/editor) with GitHub. No git knowledge needed.
2. **Direct PRs**—click "Edit this page" on any article, or fork and open a PR.

## Stack

- [Astro](https://astro.build) + [Starlight](https://starlight.astro.build) (docs theme)
- [Keystatic](https://keystatic.com) for the in-browser editor (mounted at `/editor`)
- [Tailwind v4](https://tailwindcss.com) via `@astrojs/starlight-tailwind`
- Deployed on [Cloudflare Pages](https://pages.cloudflare.com)—free, unlimited collaborators

Content lives as `.mdx` files under `src/content/docs/` in three collections:
`guides`, `lore`, `glossary`.

## Local development

```bash
pnpm install
pnpm dev       # http://127.0.0.1:4321
pnpm build     # production build (uses Cloudflare adapter)
pnpm preview   # serve the build locally
```

The `/editor` route uses local filesystem storage in dev. For production
(GitHub storage), see [`.env.example`](./.env.example).

## Deployment (Cloudflare Pages)

1. Create a Pages project connected to this repo.
2. Framework preset: **Astro**. Build command: `pnpm build`. Output: `dist`.
3. Under **Settings → Functions**, enable the `nodejs_compat` compatibility flag.
4. Add the env vars from [`.env.example`](./.env.example) (GitHub OAuth App credentials + Keystatic secret).

## License

Content: community contributions licensed per the repository's LICENSE.
Code: MIT.
