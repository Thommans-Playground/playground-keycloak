// FetchBackendApi against a real local HTTP server (node:http on port 0). No mocking of fetch.
import assert from "node:assert/strict";
import { createServer, type IncomingMessage, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { after, before, test } from "node:test";
import { FetchBackendApi } from "./fetch-backend-api.ts";

type Seen = { method: string; url: string; headers: IncomingMessage["headers"]; body: string };
let server: Server;
let baseUrl: string;
let seen: Seen | undefined;
let reply = { status: 200, contentType: "application/json" as string | undefined, body: "{}" };

before(async () => {
  server = createServer(async (req, res) => {
    const chunks: Buffer[] = [];
    for await (const c of req) chunks.push(c as Buffer);
    seen = { method: req.method ?? "", url: req.url ?? "", headers: req.headers, body: Buffer.concat(chunks).toString("utf8") };
    res.statusCode = reply.status;
    if (reply.contentType) res.setHeader("Content-Type", reply.contentType);
    res.end(reply.body);
  });
  await new Promise<void>((ok) => server.listen(0, "127.0.0.1", ok));
  baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

after(async () => {
  server.closeAllConnections();
  await new Promise((ok) => server.close(ok));
});

const api = () => new FetchBackendApi(baseUrl);
const lastSeen = () => {
  assert.ok(seen, "the server saw no request");
  return seen;
};

test("it adds the access token as a bearer header (Verifies AC-33)", async () => {
  reply = { status: 200, contentType: "application/json", body: "{}" };
  await api().request({ method: "GET", path: "me" }, "tok-123");
  assert.equal(lastSeen().headers.authorization, "Bearer tok-123");
});

test("it builds the address from the base address, the path and the search", async () => {
  await api().request({ method: "GET", path: "accounts/42", search: "?status=active&page=2" }, "t");
  assert.equal(lastSeen().url, "/accounts/42?status=active&page=2");
  await api().request({ method: "GET", path: "accounts" }, "t");
  assert.equal(lastSeen().url, "/accounts");
});

test("it passes the method and the body, with application/json by default", async () => {
  await api().request({ method: "POST", path: "accounts", body: '{"a":1}' }, "t");
  assert.equal(lastSeen().method, "POST");
  assert.equal(lastSeen().body, '{"a":1}');
  assert.equal(lastSeen().headers["content-type"], "application/json");
});

test("it passes the content type it was given when there is a body", async () => {
  await api().request({ method: "PUT", path: "x", body: "a=1", contentType: "application/x-www-form-urlencoded" }, "t");
  assert.equal(lastSeen().headers["content-type"], "application/x-www-form-urlencoded");
  assert.equal(lastSeen().body, "a=1");
});

test("it sends no content type when there is no body", async () => {
  await api().request({ method: "GET", path: "x", contentType: "text/plain" }, "t");
  assert.equal(lastSeen().headers["content-type"], undefined);
  assert.equal(lastSeen().body, "");
});

test("it returns the status, the body text and the content type of the answer", async () => {
  reply = { status: 201, contentType: "text/plain; charset=utf-8", body: "hello" };
  const res = await api().request({ method: "GET", path: "x" }, "t");
  assert.deepEqual(res, { status: 201, body: "hello", contentType: "text/plain; charset=utf-8" });
});

test("it passes a 4xx or 5xx answer back as it is, without throwing", async () => {
  for (const status of [400, 403, 404, 409, 500, 503]) {
    reply = { status, contentType: "application/json", body: `{"code":${status}}` };
    const res = await api().request({ method: "GET", path: "x" }, "t");
    assert.deepEqual(res, { status, body: `{"code":${status}}`, contentType: "application/json" });
  }
});

test("it reports application/json when the answer names no content type", async () => {
  reply = { status: 204, contentType: undefined, body: "" };
  const res = await api().request({ method: "DELETE", path: "x" }, "t");
  assert.equal(res.status, 204);
  assert.equal(res.body, "");
  assert.equal(res.contentType, "application/json");
});

test("a closed port rejects, so the use case can report the API unreachable", async () => {
  const probe = createServer();
  await new Promise<void>((ok) => probe.listen(0, "127.0.0.1", ok));
  const closed = `http://127.0.0.1:${(probe.address() as AddressInfo).port}`;
  await new Promise((ok) => probe.close(ok));
  await assert.rejects(new FetchBackendApi(closed).request({ method: "GET", path: "x" }, "t"));
});
