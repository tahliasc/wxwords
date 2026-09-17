// Run: cd worker && npm test     (node --test test/*.test.js)
//
// Guards the CORS allowlist. The Worker answers credentialed requests (admin
// token via header or cookie), so an over-broad match would let another site
// act with a moderator's credentials.

import { test } from "node:test";
import assert from "node:assert/strict";
import { configuredOrigins, isAllowedOrigin } from "../src/origins.js";

const env = {
  ALLOWED_ORIGINS: "https://wxwords.pages.dev, https://tahliasc.github.io",
  PAGES_PREVIEW_HOST: "wxwords.pages.dev",
};

test("configured site origins are allowed", () => {
  assert.ok(isAllowedOrigin("https://wxwords.pages.dev", env), "production Pages site must be allowed");
  assert.ok(isAllowedOrigin("https://tahliasc.github.io", env), "legacy GitHub Pages site must stay allowed during migration");
});

test("local dev on port 8080 is allowed, other ports are not", () => {
  assert.ok(isAllowedOrigin("http://localhost:8080", env), "documented dev port must work");
  assert.ok(isAllowedOrigin("http://127.0.0.1:8080", env), "loopback IP on dev port must work");
  assert.ok(!isAllowedOrigin("http://localhost:3000", env), "undocumented ports must be refused");
});

test("preview deployments of this project are allowed", () => {
  assert.ok(isAllowedOrigin("https://a1b2c3d4.wxwords.pages.dev", env), "hash preview must be allowed");
  assert.ok(isAllowedOrigin("https://feature-glossary.wxwords.pages.dev", env), "branch preview must be allowed");
});

test("lookalike and insecure origins are refused", () => {
  assert.ok(!isAllowedOrigin("https://evilwxwords.pages.dev", env), "suffix match must require a dot boundary");
  assert.ok(!isAllowedOrigin("https://wxwords.pages.dev.evil.com", env), "host must END with the preview host");
  assert.ok(!isAllowedOrigin("http://x.wxwords.pages.dev", env), "previews must be https");
  assert.ok(!isAllowedOrigin("https://other-project.pages.dev", env), "other Pages projects must be refused");
  assert.ok(!isAllowedOrigin("null", env), "opaque 'null' origin must be refused");
  assert.ok(!isAllowedOrigin("", env), "missing origin must be refused");
});

test("legacy single ALLOWED_ORIGIN is still honoured", () => {
  const legacy = { ALLOWED_ORIGIN: "https://tahliasc.github.io" };
  assert.deepEqual(configuredOrigins(legacy), ["https://tahliasc.github.io"], "old config shape must keep working");
  assert.ok(!isAllowedOrigin("https://x.wxwords.pages.dev", legacy), "no preview host configured means no previews");
});
