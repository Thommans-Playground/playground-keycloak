// The hexagon holds on the web side too. Verifies AC-36 (NFR-3).
//   domain/       imports only other domain files
//   application/  imports only the domain and itself: no adapter, no framework, no library
//   adapters/     are imported only by composition.ts, the one place that picks them
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { test } from "node:test";

const SRC = import.meta.dirname;

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? files(p) : [p];
  });
}
const isCode = (f: string) => /\.(ts|tsx)$/.test(f) && !/\.test\.ts$/.test(f);
const importsOf = (f: string) =>
  [...readFileSync(f, "utf8").matchAll(/(?:from|import)\s*\(?\s*["']([^"']+)["']/g)].map((m) => m[1]);

test("the domain imports only the domain", () => {
  for (const f of files(join(SRC, "domain")).filter(isCode)) {
    for (const spec of importsOf(f)) assert.match(spec, /^\.\/[\w-]+\.ts$/, `${relative(SRC, f)} imports ${spec}`);
  }
});

test("the use cases import only the domain and each other", () => {
  for (const f of files(join(SRC, "application")).filter(isCode)) {
    for (const spec of importsOf(f)) {
      assert.match(spec, /^(\.\/[\w-]+\.ts|\.\.\/domain\/[\w-]+\.ts)$/, `${relative(SRC, f)} imports ${spec}`);
    }
  }
});

test("only composition.ts imports an adapter", () => {
  for (const f of files(SRC).filter(isCode)) {
    if (f.includes(`${join(SRC, "adapters")}`) || f === join(SRC, "composition.ts")) continue;
    for (const spec of importsOf(f)) assert.ok(!spec.includes("/adapters/"), `${relative(SRC, f)} imports ${spec}`);
  }
});

test("there is a domain, a set of use cases and at least one adapter", () => {
  assert.ok(files(join(SRC, "domain")).some(isCode));
  assert.ok(files(join(SRC, "application")).some(isCode));
  assert.ok(files(join(SRC, "adapters")).some(isCode));
});
