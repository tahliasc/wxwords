// Local development servers. Port 8080 is the documented convention.
const LOCAL_ORIGINS = ["http://localhost:8080", "http://127.0.0.1:8080"];

/**
 * Parse the configured site origins.
 *
 * ALLOWED_ORIGINS is a comma-separated list (e.g. the Cloudflare Pages site and,
 * during migration, the old GitHub Pages site). ALLOWED_ORIGIN is the legacy
 * single-value form, still honoured.
 */
export function configuredOrigins(env) {
  const raw = [env.ALLOWED_ORIGINS, env.ALLOWED_ORIGIN].filter(Boolean).join(",");
  return raw.split(",").map((o) => o.trim()).filter(Boolean);
}

/**
 * Whether a browser Origin may call this Worker with credentials.
 *
 * Allowed: configured site origins, local dev, and Cloudflare Pages preview
 * deployments of THIS project — https://<anything>.<PAGES_PREVIEW_HOST>.
 * The leading "." in the suffix check matters: it stops a lookalike such as
 * "https://evilwxwords.pages.dev" from matching.
 */
export function isAllowedOrigin(origin, env) {
  if (!origin) return false;
  if (configuredOrigins(env).includes(origin)) return true;
  if (LOCAL_ORIGINS.includes(origin)) return true;
  const previewHost = env.PAGES_PREVIEW_HOST;
  if (previewHost) {
    let url;
    try { url = new URL(origin); } catch { return false; }
    if (url.protocol === "https:" && url.hostname.endsWith("." + previewHost)) return true;
  }
  return false;
}
