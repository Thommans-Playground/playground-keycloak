import test from "node:test";
import assert from "node:assert/strict";
import { personAtTheTime } from "./audit-person.ts";

const now = new Map([["a1", { name: "Maya Lopez", email: "maya.lopez@x.test" }]]);

test("the entry's own name and email are shown when it has them (Verifies AC-70)", () => {
  assert.deepEqual(personAtTheTime({ id: "a1", name: "Maya", email: "maya@x.test" }, now), {
    name: "Maya",
    email: "maya@x.test",
  });
});

test("the current name is never shown when the entry has one (Verifies AC-70)", () => {
  const shown = personAtTheTime({ id: "a1", name: "Maya", email: null }, now);
  assert.equal(shown.name, "Maya");
  assert.notEqual(shown.name, "Maya Lopez");
  assert.equal(shown.email, null);
});

test("an old entry with no name falls back to the current account (Verifies AC-70)", () => {
  assert.deepEqual(personAtTheTime({ id: "a1", name: null, email: null }, now), {
    name: "Maya Lopez",
    email: "maya.lopez@x.test",
  });
});

test("an old entry whose account is unknown shows the id (Verifies AC-70)", () => {
  assert.deepEqual(personAtTheTime({ id: "gone", name: null, email: null }, now), { name: "gone", email: null });
});

test("no person at all is the system (Verifies AC-70)", () => {
  assert.deepEqual(personAtTheTime({ id: null, name: null, email: null }, now), { name: "system", email: null });
});
