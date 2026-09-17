// Local development servers. Port 8080 is the documented convention.
const LOCAL_ORIGINS = ["http://localhost:8080", "http://127.0.0.1:8080"];

function splitList(value) {
  return (value || "").split(",").map((v) => v.trim()).filter(Boolean);
}

/**
 * Parse the configured site origins.
 *
 * ALLOWED_ORIGINS is a comma-separated list (the live site and, during
 * migration, the old GitHub Pages site). ALLOWED_ORIGIN is the legacy
 * single-value form, still honoured.
 */
export function configuredOrigins(env) {
  return [...splitList(env.ALLOWED_ORIGINS), ...splitList(env.ALLOWED_ORIGIN)];
}

/**
 * Hostname suffixes that identify preview deployments of the site.
 *
 * PREVIEW_HOST_SUFFIXES is a comma-separated list. Each suffix MUST begin with
 * "." or "-" so it only matches on a label boundary:
 *   Workers previews: "<branch>-wxwords.tahliasc.workers.dev" -> "-wxwords.tahliasc.workers.dev"
 *   Pages previews:   "<branch>.wxwords.pages.dev"             -> ".wxwords.pages.dev"
 * Suffixes without a boundary character are ignored — "wxwords.pages.dev"
 * would otherwise also match "evilwxwords.pages.dev".
 *
 * Why a "-" suffix is safe for workers.dev: every host under
 * "tahliasc.workers.dev" belongs to this Cloudflare account; nobody else can
 * create one.
 */
export function previewSuffixes(env) {
  return splitList(env.PREVIEW_HOST_SUFFIXES).filter((s) => s.startsWith(".") || s.startsWith("-"));
}

/**
 * Whether a browser Origin may call this Worker with credentials.
 *
 * Allowed: configured site origins, local dev on port 8080, and https preview
 * deployments matching a configured suffix.
 */
export function isAllowedOrigin(origin, env) {
  if (!origin) return false;
  if (configuredOrigins(env).includes(origin)) return true;
  if (LOCAL_ORIGINS.includes(origin)) return true;

  const suffixes = previewSuffixes(env);
  if (suffixes.length === 0) return false;
  let url;
  try { url = new URL(origin); } catch { return false; }
  if (url.protocol !== "https:") return false;
  return suffixes.some((s) => url.hostname.endsWith(s) && url.hostname.length > s.length);
}
