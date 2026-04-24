import { defineMiddleware } from "astro:middleware";

// @keystatic/astro 5.0.6 still reads `Astro.locals.runtime.env`, which Astro 6
// removed in favor of `import { env } from "cloudflare:workers"`. The adapter
// now defines `env` on `locals.runtime` as a getter that throws — so a simple
// `"env" in runtime` check passes through and Keystatic hits the throwing
// getter. Force-redefine it as a data property so Keystatic gets the real env.
// Dynamic import keeps Node-side prerender happy (it can't resolve
// `cloudflare:workers`).
export const onRequest = defineMiddleware(async (context, next) => {
	const locals = context.locals as unknown as { runtime?: object };
	if (locals.runtime) {
		try {
			const { env } = await import("cloudflare:workers");
			Object.defineProperty(locals.runtime, "env", {
				value: env,
				writable: true,
				configurable: true,
				enumerable: true,
			});
		} catch {
			// Not running on Workers (e.g. Node prerender) — nothing to shim.
		}
	}
	return next();
});
