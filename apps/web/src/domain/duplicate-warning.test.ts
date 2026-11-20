import test from "node:test";
import assert from "node:assert/strict";
import { duplicateWarning } from "./duplicate-warning.ts";

// These tests prove the WORDING of the warning only. That the row shows it in the browser
// is not tested by a browser test (no browser test tool is installed).

test("no other account with the email: no warning (Verifies AC-73)", () => {
  assert.equal(duplicateWarning([]), null);
});

test("a missing field means none (Verifies AC-73)", () => {
  assert.equal(duplicateWarning(undefined), null);
});

test("one other account: the warning names it and its status (Verifies AC-73)", () => {
  assert.equal(
    duplicateWarning([{ id: "1", name: "Maya", status: "active" }]),
    "Another account has this email: Maya (active)",
  );
});

test("a deactivated one is named as deactivated (Verifies AC-73)", () => {
  assert.equal(
    duplicateWarning([{ id: "1", name: "Maya", status: "deactivated" }]),
    "Another account has this email: Maya (deactivated)",
  );
});

test("several: each is named (Verifies AC-73)", () => {
  assert.equal(
    duplicateWarning([
      { id: "1", name: "Maya", status: "deactivated" },
      { id: "2", name: "Sam", status: "pending" },
    ]),
    "Other accounts have this email: Maya (deactivated), Sam (pending)",
  );
});
