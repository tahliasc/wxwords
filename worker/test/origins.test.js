// Run: cd worker && npm test     (node --test test/*.test.js)
//
// Guards the CORS allowlist. The Worker answers credentialed requests (admin
// token via header or cookie), so an over-broad match would let another site
// act with a moderator's credentials.

import { test } from "node:test";
import assert from "node:assert/strict";
import { configuredOrigins, isAllowedOrigin, previewSuffixes } from "../src/origins.js";

const env = {
  ALLOWED_ORIGINS: "https://wxwords.tahliasc.workers.dev, https://tahliasc.github.io",
  PREVIEW_HOST_SUFFIXES: "-wxwords.tahliasc.workers.dev",
};

test("configured site origins are allowed", () => {
  assert.ok(isAllowedOrigin("https://wxwords.tahliasc.workers.dev", env), "live site must be allowed");
  assert.ok(isAllowedOrigin("https://tahliasc.github.io", env), "legacy GitHub Pages site must stay allowed during migration");
});

test("local dev on port 8080 is allowed, other ports are not", () => {
  assert.ok(isAllowedOrigin("http://localhost:8080", env), "documented dev port must work");
  assert.ok(isAllowedOrigin("http://127.0.0.1:8080", env), "loopback IP on dev port must work");
  assert.ok(!isAllowedOrigin("http://localhost:3000", env), "undocumented ports must be refused");
});

test("Workers preview deployments are allowed", () => {
  assert.ok(isAllowedOrigin("https://feature-glossary-wxwords.tahliasc.workers.dev", env), "branch alias preview must be allowed");
  assert.ok(isAllowedOrigin("https://a1b2c3d4-wxwords.tahliasc.workers.dev", env), "version-id preview must be allowed");
});

test("lookalike, bare and insecure origins are refused", () => {
  assert.ok(!isAllowedOrigin("https://evilwxwords.tahliasc.workers.dev", env), "suffix must match on a '-' boundary");
  assert.ok(!isAllowedOrigin("https://x-wxwords.tahliasc.workers.dev.evil.com", env), "host must END with the suffix");
  assert.ok(!isAllowedOrigin("https://-wxwords.tahliasc.workers.dev", env), "the suffix alone is not a preview host");
  assert.ok(!isAllowedOrigin("http://x-wxwords.tahliasc.workers.dev", env), "previews must be https");
  assert.ok(!isAllowedOrigin("https://x-wxwords.someoneelse.workers.dev", env), "other accounts' workers must be refused");
  assert.ok(!isAllowedOrigin("https://wxwords-upload-api.tahliasc.workers.dev", env), "the API's own host is not a site origin");
  assert.ok(!isAllowedOrigin("null", env), "opaque 'null' origin must be refused");
  assert.ok(!isAllowedOrigin("", env), "missing origin must be refused");
});

test("suffixes without a boundary character are ignored", () => {
  const risky = { PREVIEW_HOST_SUFFIXES: "wxwords.pages.dev, .wxwords.pages.dev" };
  assert.deepEqual(previewSuffixes(risky), [".wxwords.pages.dev"], "a suffix with no leading '.'/'-' must be dropped");
  assert.ok(!isAllowedOrigin("https://evilwxwords.pages.dev", risky), "dropped suffix must not match lookalikes");
  assert.ok(isAllowedOrigin("https://branch.wxwords.pages.dev", risky), "the bounded Pages-style suffix still works");
});

test("legacy single ALLOWED_ORIGIN is still honoured", () => {
  const legacy = { ALLOWED_ORIGIN: "https://tahliasc.github.io" };
  assert.deepEqual(configuredOrigins(legacy), ["https://tahliasc.github.io"], "old config shape must keep working");
  assert.ok(!isAllowedOrigin("https://x-wxwords.tahliasc.workers.dev", legacy), "no suffixes configured means no previews");
});
