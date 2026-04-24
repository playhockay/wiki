# Contributing to the Hockay Wiki

Thank you for helping build the Hockay wiki. Everything here is community-written.
There are two ways to contribute—pick whichever is easier for you. Both open
pull requests against this repo, so the review flow is the same.

## Lane 1—Browser editor (no git required)

1. Go to [hockay.wiki/editor](https://hockay.wiki/editor).
2. Sign in with your GitHub account. (The editor asks for permission to open
   pull requests on your behalf—nothing else.)
3. Pick a collection (Guides, Lore, or Glossary), create or edit a page, and
   save. A pull request will be opened automatically.
4. Wait for review—a wiki moderator will either merge it or leave comments.

You don't need to know Markdown, git, or anything else. The editor handles it.

## Lane 2—Direct pull requests (for power users)

1. On any wiki page, click **Edit this page** to open the `.mdx` source in
   GitHub's web editor, or fork the repo locally.
2. Edit the file and open a pull request against `main`.
3. A wiki moderator will review and merge.

All content lives under `src/content/docs/` as `.mdx` files. Frontmatter fields:

```yaml
---
title: Page title
description: Short summary (shown in search results and meta tags)
tags: [optional, list]
lastUpdated: 2026-04-24
---
```

Use `<Infobox variant="ice" title="...">...</Infobox>` for callouts (variants:
`ice`, `jambono`, `sixth`, `positive`, `negative`, `neutral`).

## What gets reviewed for

- Factual accuracy—we'll ask for sources if something looks off.
- Tone—neutral, descriptive, community-friendly.
- No promotional / off-topic content.
- Images: reasonable size, relevant, attributed if required.

## Who reviews

Members of the `wiki-mods` team. If you'd like to become a moderator after a
few accepted contributions, open an issue and ask.

## Running the site locally (optional)

```bash
pnpm install
pnpm dev
```

Open http://127.0.0.1:4321 (or the port Astro reports).

The `/editor` route uses **local** storage in dev—edits write straight to
your filesystem, no GitHub round-trip. Set up a GitHub OAuth App and the env
vars in `.env.example` only if you want to test the production flow locally.

## License

By contributing, you agree your contributions are licensed under the same
terms as this repository.
