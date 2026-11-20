import assert from "node:assert/strict";
import { test } from "node:test";
import { accountPageUrl } from "./account-page.ts";

test("the account page is the account console of the realm (Verifies AC-78)", () => {
  assert.equal(
    accountPageUrl("http://localhost:8080/realms/playground"),
    "http://localhost:8080/realms/playground/account",
  );
});

test("a trailing slash on the address does not double the slash (Verifies AC-78)", () => {
  assert.equal(accountPageUrl("https://auth.example.com/realms/acme/"), "https://auth.example.com/realms/acme/account");
});
