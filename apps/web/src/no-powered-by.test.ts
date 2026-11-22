// No answer of the web app names its framework. Verifies AC-97 (NFR-6).
import assert from "node:assert/strict";
import { test } from "node:test";

import nextConfig from "../next.config.ts";

test("the web app sends no X-Powered-By header (poweredByHeader is false)", () => {
  assert.equal(nextConfig.poweredByHeader, false);
});
