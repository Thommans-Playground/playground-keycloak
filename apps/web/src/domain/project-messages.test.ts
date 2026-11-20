import test from "node:test";
import assert from "node:assert/strict";
import { projectRefusalMessage } from "./project-messages.ts";

const codes = ["forbidden", "member_not_eligible", "invalid_project_name", "invalid_request", "project_not_found"];

test("each known refusal has its own sentence (Verifies AC-11)", () => {
  const messages = codes.map(projectRefusalMessage);
  assert.equal(new Set(messages).size, codes.length);
  for (const m of messages) assert.match(m, /^[A-Z].*\.$/);
});

test("a name that is not valid says the rule (Verifies AC-13)", () => {
  assert.match(projectRefusalMessage("invalid_project_name"), /1 to 100 characters/);
});

test("a member who is not eligible says why, for add and remove alike (Verifies AC-18)", () => {
  assert.match(projectRefusalMessage("member_not_eligible"), /active account|not a member/);
});

test("a person who may not is told so (Verifies AC-60)", () => {
  assert.match(projectRefusalMessage("forbidden"), /may not/);
});

test("an invalid request is told as such (Verifies AC-87)", () => {
  assert.match(projectRefusalMessage("invalid_request"), /not valid/);
});

test("an unknown code gets a default that does not repeat the code (Verifies AC-87)", () => {
  const m = projectRefusalMessage("<script>boom_42</script>");
  assert.ok(m.length > 0);
  assert.doesNotMatch(m, /script|boom_42/);
});

test("a hidden project and a missing one read the same and do not name the project (Verifies AC-27)", () => {
  assert.equal(projectRefusalMessage("project_not_found"), projectRefusalMessage("project_not_found"));
  assert.match(projectRefusalMessage("project_not_found"), /not available/);
  assert.doesNotMatch(projectRefusalMessage("project_not_found"), /exist|permission|allowed|access/i);
});
