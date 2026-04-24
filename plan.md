# Hockay Wiki—continuation plan

Picks up where the initial scaffold left off. Read this, then start with the
first unchecked item under "What's next."

## Current state

Scaffolded at `/Users/jpvalery/wiki`. `pnpm dev` + `pnpm build` both pass.

- **Framework**: Astro 6 + Starlight 0.38, React islands, MDX, Tailwind v4
- **Editor**: Keystatic 0.5, mounted at `/keystatic`, `/editor` redirects there
- **Hosting target**: Cloudflare Pages (not yet connected)
- **Repo target**: `playhockay/wiki` on GitHub (not yet pushed)
- **Domain target**: `hockay.wiki` (not yet configured)

Routes that work in `pnpm dev`:

| Route | What it is |
|---|---|
| `/` | Landing page (splash layout) |
| `/guides/getting-started` | Seed Guide page |
| `/lore/world` | Seed Lore page |
| `/glossary` | Seed Glossary page |
| `/editor` → `/keystatic` | Browser editor (uses local filesystem storage in dev) |

## Non-obvious constraints (read before changing architecture)

1. **Cloudflare adapter is gated to build only.** `astro.config.mjs` only
   applies `cloudflare()` when `process.argv.includes('build')`. Without this,
   dev fails because postcss (via astro-expressive-code) uses Node's `path`,
   which the adapter's Workers-like dev env can't resolve. If you ever need
   SSR-in-dev to behave exactly like CF, run `pnpm build && pnpm preview`.
2. **Keystatic base path is hardcoded.** `@keystatic/core` has
   `basePath = "/keystatic"` at `node_modules/@keystatic/core/dist/keystatic-core-ui.js:8235`
   and all API calls hit `/api/keystatic/*`. We can't move it. We redirect
   `/editor` → `/keystatic` to keep `/editor` as the marketed URL.
3. **Keystatic peer-dep warns on Astro 6.** `@keystatic/astro@5.0.6` declares
   `astro: "2 || 3 || 4 || 5"`—still works, but upgrade when a
   `@keystatic/astro@>=5.1` lands that adds Astro 6 to its peer range.
4. **`nodejs_compat` flag required on Cloudflare Pages**—postcss + others
   import Node built-ins. Build warns about this; the flag fixes it at runtime.
5. **All deps are pinned exactly** (`.npmrc` has `save-exact=true`). Keep this
   when adding new deps—it's a security policy.
6. **MDX components are auto-imported via a remark plugin.** Infobox is
   registered in both Keystatic's schema (`keystatic.config.ts` → `block()`)
   and an Astro remark plugin at `src/lib/remark-inject-mdx-components.mjs`.
   MDX files should **not** hand-write `import Infobox from '...'`—the
   plugin injects it at build time. To add a new component (e.g. PlayerCard),
   register it in both places (see step 7).

## What's next (in order)

### 1. Initialize git and push to GitHub

```bash
git init -b main
git add .
git commit -m "Initial Hockay wiki scaffold"
gh repo create playhockay/wiki --public --source=. --push
```

(User asked to skip git during scaffold—confirm before running.)

### 2. Create the `wiki-mods` team and branch protection

- GitHub org `playhockay` → Teams → New team `wiki-mods`. Add yourself + any
  trusted contributors with write access.
- Repo → Settings → Branches → add rule for `main`:
  - Require a pull request before merging
  - Require 1 approval from `wiki-mods`
  - Require branches to be up to date
  - Disallow force-push, disallow deletion

`CODEOWNERS` already routes all reviews to `@playhockay/wiki-mods`.

### 3. Create the GitHub OAuth App for Keystatic

Under `playhockay` org → Settings → Developer settings → OAuth Apps → New:

- **Application name**: `Hockay Wiki editor`
- **Homepage URL**: `https://hockay.wiki`
- **Authorization callback URL**: `https://hockay.wiki/api/keystatic/github/oauth/callback`

Save the client ID + secret. Generate a random 32-byte hex string for
`KEYSTATIC_SECRET` (e.g. `openssl rand -hex 32`).

### 4. Deploy to Cloudflare Pages

- Cloudflare dashboard → Workers & Pages → Create → Pages → Connect to Git.
- Select `playhockay/wiki`. Framework preset: **Astro**.
- Build command: `pnpm build`. Output directory: `dist`.
- Environment variables (Production):
  - `KEYSTATIC_GITHUB_CLIENT_ID`
  - `KEYSTATIC_GITHUB_CLIENT_SECRET`
  - `KEYSTATIC_SECRET`
  - `PUBLIC_KEYSTATIC_GITHUB_APP_SLUG` (the repo part of the OAuth app URL slug)
- Settings → Functions → Compatibility flags → add `nodejs_compat` for both
  Production and Preview.
- Settings → Custom domains → add `hockay.wiki`.

### 5. Verify end-to-end

1. Visit `https://hockay.wiki` → wiki renders.
2. Visit `https://hockay.wiki/editor` → redirects to `/keystatic` → Keystatic
   UI loads. Sign in with GitHub.
3. Edit a page, save → confirm a PR appears on `playhockay/wiki`.
4. Merge PR → CF Pages redeploys → edit is live.
5. Have a non-`wiki-mods` user try to merge directly → blocked by branch protection.
6. Have a mod (not you) merge a PR → confirm CF deploy still runs (this is the
   whole reason we're not on Vercel).

### 6. Backfill content—done for initial launch

Initial content migrated from `~/hockay/design/lore.md`, `~/hockay/design/lore/*.json`,
and `~/hockay/apps/web/src/app/(resources)/faq/page.tsx`. Structure:

- **Homepage**—richer landing: hero + Start Here + mythology cards + mock H.O.R.N. advisories + featured teams + modifier cards + contribute.
- **guides/**—getting-started, faq (41 items, auto-generated from faq/page.tsx), season-cycle, simulation, economy, community.
- **lore/**—index, almighty-ice, the-puck, the-jambono, the-sixth, glacified, lpchuip, organizations, commentators.
- **teams/**—index + 20 team pages auto-generated from `teams.json` + `arenas.json` via `/tmp/gen-teams.mjs`.
- **modifiers/**—index, player (18 modifiers), match (10), arena (table of all 20), advisories.
- **glossary/**—A–Z reference cross-linked to every full page.

Future content additions happen via Keystatic at `/editor` or direct PRs. The scripts at
`/tmp/gen-teams.mjs` and `/tmp/gen-faq.mjs` can be rerun if the source JSON/TSX change.

### 7. Add more MDX components (when needed)

The plumbing for custom MDX components is wired:

- **Astro render side**: `src/lib/remark-inject-mdx-components.mjs` auto-injects
  `import Foo from '...'` at the top of any MDX file that uses `<Foo>`. Add a
  new entry to its `COMPONENTS` map.
- **Keystatic editor side**: `keystatic.config.ts` declares components under
  `fields.mdx({ components: { Foo: block({ schema: {...} }) } })`. Add a new
  `block()` and reference it in the `components` map.

Checklist to add a new component (e.g. PlayerCard):

1. Create `src/components/mdx/PlayerCard.astro` with the component's markup.
2. Add an entry to `COMPONENTS` in `src/lib/remark-inject-mdx-components.mjs`:
   `PlayerCard: "import PlayerCard from '../../../components/mdx/PlayerCard.astro';"`
3. Add a `block()` definition in `keystatic.config.ts` and register it under
   the `components` map of `fields.mdx`.
4. Test by editing a page in `/editor` → insert the new component → save →
   confirm the generated MDX renders the Astro component.

Keep the component variants aligned with Hockay's lore accent names
(ice/jambono/sixth/positive/negative) for visual consistency with the main app.

### 8. Polish the theme

The Hockay tokens are wired, but the header is still Starlight's default.
Consider:

- Add `src/components/overrides/Header.astro` to embed Hockay's real top nav
  (logo + link to `hockay.com`, `play.hockay.com`, etc.). Register under
  `starlight.components.Header` in `astro.config.mjs`.
- Load Geist Sans / Geist Mono / Young Serif (currently referenced in CSS but
  not actually loaded—add `<link>` tags to Starlight's `head` config or via
  a component override).
- Double-check the dark-mode palette in `src/styles/hockay.css`—it's
  derived by hand, not from a real Hockay dark theme.

## Handy commands

```bash
pnpm dev                           # dev server (Node, no CF adapter)
pnpm build                         # production build (CF adapter + prerender)
pnpm preview                       # serve the build locally
pnpm astro check                   # type-check content collections
pnpm add <pkg>                     # respects save-exact=true (.npmrc)
```

## Critical files

- `astro.config.mjs`—Astro + Starlight + React + MDX + Keystatic + CF adapter (build-only) + redirects
- `keystatic.config.ts`—Keystatic schema, GitHub storage for production
- `src/content.config.ts`—Astro content collections (Starlight's `docs` loader)
- `src/content/docs/**/*.mdx`—wiki pages (what contributors edit)
- `src/styles/hockay.css`—Tailwind v4 + Starlight-Tailwind + Hockay tokens + Starlight var overrides
- `src/components/overrides/{SiteTitle,Footer}.astro`—brand chrome
- `src/components/mdx/Infobox.astro`—first reusable wiki component
- `.env.example`—GitHub OAuth env vars for production
- `.npmrc`—`save-exact=true` (pins all new deps)
- `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/pull_request_template.md`

## Related docs

- Approved implementation plan: `~/.claude/plans/i-d-like-to-build-sunny-peacock.md`
- Project memory: `~/.claude/projects/-Users-jpvalery-wiki/memory/project_hockay_wiki_setup.md`
