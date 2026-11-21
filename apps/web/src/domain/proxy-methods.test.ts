import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PROXY_METHODS, methodHasBody } from "./proxy-methods.ts";

test("the proxy forwards GET, POST and DELETE and nothing else (Verifies AC-32)", () => {
  assert.deepEqual([...PROXY_METHODS].sort(), ["DELETE", "GET", "POST"]);
  assert.ok(!PROXY_METHODS.includes("PUT") && !PROXY_METHODS.includes("PATCH"));
});

test("only a method that carries a body gets one: DELETE, GET and HEAD do not (Verifies AC-32)", () => {
  assert.equal(methodHasBody("POST"), true);
  for (const m of ["GET", "HEAD", "DELETE"]) assert.equal(methodHasBody(m), false, m);
});

// The route module imports the composition root (Keycloak, Redis), so node --test does not import it:
// its export line is read as text and must match the method list.
test("the proxy route exports exactly the allowed methods, never PUT or PATCH (Verifies AC-32)", () => {
  const src = readFileSync(import.meta.dirname + "/../app/api/backend/[...path]/route.ts", "utf8");
  const exported = [...src.matchAll(/forward as (\w+)/g)].map((m) => m[1]).sort();
  assert.deepEqual(exported, [...PROXY_METHODS].sort());
  assert.doesNotMatch(src, /export\s+(async\s+)?(function|const)\s+(PUT|PATCH)\b/);
});
