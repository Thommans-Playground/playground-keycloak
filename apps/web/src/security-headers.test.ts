// Every page carries the browser security headers. Verifies AC-96 (NFR-6).
// next.config.ts answers headers() for the source '/:path*', which is every path.
import assert from "node:assert/strict";
import { test } from "node:test";
import nextConfig from "../next.config.ts";

test("every page carries frame-ancestors 'none', nosniff and a Referrer-Policy", async () => {
  assert.equal(typeof nextConfig.headers, "function", "next.config.ts defines no headers()");
  const rules = await nextConfig.headers!();
  const rule = rules.find((r) => r.source === "/:path*");
  assert.ok(rule, "no header rule for the source /:path*");
  const value = (key: string) => rule.headers.find((h) => h.key.toLowerCase() === key.toLowerCase())?.value;

  assert.match(value("Content-Security-Policy") ?? "", /frame-ancestors 'none'/);
  assert.equal(value("X-Content-Type-Options"), "nosniff");
  assert.ok(value("Referrer-Policy"), "Referrer-Policy header is missing");
});
