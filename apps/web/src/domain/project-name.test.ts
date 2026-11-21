import test from "node:test";
import assert from "node:assert/strict";
import { looksLikeAName } from "./project-name.ts";

test("a name of 1 to 100 characters after trimming looks fine (Verifies AC-12)", () => {
  assert.equal(looksLikeAName("Apollo"), true);
  assert.equal(looksLikeAName("  Apollo  "), true);
  assert.equal(looksLikeAName("a".repeat(100)), true);
});

test("an empty or blank name, or one over 100 characters, does not (Verifies AC-12)", () => {
  assert.equal(looksLikeAName(""), false);
  assert.equal(looksLikeAName("   \t "), false);
  assert.equal(looksLikeAName("a".repeat(101)), false);
});
