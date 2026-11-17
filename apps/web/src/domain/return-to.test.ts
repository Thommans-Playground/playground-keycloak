import assert from "node:assert/strict";
import { test } from "node:test";
import { safeReturnTo } from "./return-to.ts";

test("keeps local paths", () => {
  assert.equal(safeReturnTo("/admin/accounts?tab=2"), "/admin/accounts?tab=2");
});

test("refuses everything that could leave the site", () => {
  for (const bad of ["https://evil.example", "//evil.example", "/\\evil.example", "dashboard", "", null, undefined, "/a\nb"]) {
    assert.equal(safeReturnTo(bad), "/dashboard", String(bad));
  }
});
