import test from "node:test";
import assert from "node:assert/strict";
import { memberLabel, projectSummary } from "./project-summary.ts";

const members = (n: number) => Array.from({ length: n }, (_, i) => ({ id: `id${i}`, name: `P${i}` }));

test("no members reads 'No members yet' (Verifies AC-86)", () => {
  assert.equal(projectSummary({ members: [] }), "No members yet");
});

test("one member is singular (Verifies AC-28)", () => {
  assert.equal(projectSummary({ members: members(1) }), "1 member");
});

test("several members are counted (Verifies AC-28)", () => {
  assert.equal(projectSummary({ members: members(3) }), "3 members");
});

test("a member is shown by name (Verifies AC-28)", () => {
  assert.equal(memberLabel({ id: "u1", name: "Maya Lopez" }), "Maya Lopez");
});

test("a member with no name is neutral and never shows the raw id (Verifies AC-28)", () => {
  const label = memberLabel({ id: "7f3c-secret-id", name: null });
  assert.equal(label, "Unknown person");
  assert.doesNotMatch(label, /7f3c/);
});
