import { defineMiddleware } from "astro:middleware";

// @keystatic/astro 5.0.6 still reads `Astro.locals.runtime.env`, which Astro 6
// removed. Until Keystatic ships an Astro-6-compatible release, repopulate
// `locals.runtime.env` from the `cloudflare:workers` module so Keystatic's
// built handler can pick up KEYSTATIC_GITHUB_CLIENT_ID / CLIENT_SECRET /
// SECRET on each request. Dynamic import so Node-side prerendering (which
// can't resolve `cloudflare:workers`) doesn't blow up.
export const onRequest = defineMiddleware(async (context, next) => {
	const locals = context.locals as unknown as {
		runtime?: { env?: unknown };
	};
	if (locals.runtime && !("env" in locals.runtime)) {
		try {
			const { env } = await import("cloudflare:workers");
			locals.runtime.env = env;
		} catch {
			// Not running on Workers (e.g. Node prerender) — nothing to shim.
		}
	}
	return next();
});
