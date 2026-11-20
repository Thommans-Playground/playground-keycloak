import test from "node:test";
import assert from "node:assert/strict";
import { memberCandidates } from "./member-candidates.ts";

const acc = (id: string, name: string, status = "active") => ({ id, name, status });

test("only active accounts are candidates (Verifies AC-18)", () => {
  const got = memberCandidates([acc("a", "Ann"), acc("b", "Bo", "pending"), acc("c", "Cy", "deactivated")], []);
  assert.deepEqual(
    got.map((a) => a.id),
    ["a"],
  );
});

test("people who are already members are not offered (Verifies AC-17)", () => {
  const got = memberCandidates([acc("a", "Ann"), acc("b", "Bo")], [{ id: "a" }]);
  assert.deepEqual(
    got.map((a) => a.id),
    ["b"],
  );
});

test("candidates are sorted by name, ignoring case, and the input is not changed (Verifies AC-17)", () => {
  const input = [acc("z", "zed"), acc("m", "Maya"), acc("a", "Ann")];
  assert.deepEqual(
    memberCandidates(input, []).map((a) => a.name),
    ["Ann", "Maya", "zed"],
  );
  assert.deepEqual(
    input.map((a) => a.id),
    ["z", "m", "a"],
  );
});

test("no accounts gives no candidates (Verifies AC-18)", () => {
  assert.deepEqual(memberCandidates([], [{ id: "a" }]), []);
});
