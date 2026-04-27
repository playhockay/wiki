# Contributing to the Hockay Wiki

Thank you for helping build the Hockay wiki. Everything here is community-written.

## Quick edits — via GitHub's web editor

Every article has an **Edit this page** link at the bottom. Clicking it:

1. Opens the `.mdx` source in GitHub's web editor.
2. Prompts you to sign in with GitHub and fork the repo (first time only).
3. Lets you edit, then submit as a pull request against `main`.

A wiki moderator will review and either merge or leave comments. You don't need
git installed for this flow — GitHub handles everything in the browser.

## Bigger edits — clone and run locally

If you're adding a new page, reorganizing several at once, or want to preview
Starlight components as they render:

```bash
pnpm install
pnpm dev
```

Open http://127.0.0.1:4321 (or the port Astro reports). Commit your changes to
a branch and open a PR.

## Content conventions

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

## License

By contributing, you agree your contributions are licensed under the same
terms as this repository.
