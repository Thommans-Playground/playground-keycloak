// Helpers for the integration and acceptance tests (*.it.ts). They talk to a RUNNING stack over plain HTTP:
// no browser, no extra dependency. Run them with INTEGRATION=1 npm run test:integration (see docs/TESTING.md).
import { randomBytes } from "node:crypto";
import { after, before, test } from "node:test";

const trim = (s: string) => s.replace(/\/+$/, "");

export const config = {
  keycloakUrl: trim(process.env.KEYCLOAK_URL || "http://localhost:8080"),
  apiUrl: trim(process.env.API_URL || "http://localhost:8000"),
  appUrl: trim(process.env.APP_URL || "http://localhost:3000"),
  realm: process.env.KEYCLOAK_REALM || "playground",
  webClientId: process.env.KEYCLOAK_CLIENT_ID || "playground-web",
  webClientSecret: process.env.KEYCLOAK_CLIENT_SECRET || "playground-web-dev-secret",
  // The service account the API itself uses (apps/api/app/config.py). Here it only makes and removes throwaway people.
  backendClientId: process.env.KEYCLOAK_BACKEND_CLIENT_ID || "playground-backend",
  backendClientSecret: process.env.KEYCLOAK_BACKEND_CLIENT_SECRET || "playground-backend-dev-secret",
  get issuer() { return `${this.keycloakUrl}/realms/${this.realm}`; },
  get callbackUrl() { return `${this.appUrl}/auth/callback`; },
};

export const INTEGRATION = process.env.INTEGRATION === "1";
export const TEST_TIMEOUT = 60_000;

/** A test that runs only when INTEGRATION=1, one at a time, with a generous timeout. */
export function itest(name: string, fn: () => Promise<void>) {
  test(name, { skip: INTEGRATION ? false : "set INTEGRATION=1 to run against a running stack", timeout: TEST_TIMEOUT }, fn);
}

/** With INTEGRATION=1 an unreachable stack FAILS the suite: it never goes green by skipping. */
export async function assertStackReachable() {
  const probes: Array<[string, string]> = [
    ["keycloak", `${config.issuer}/.well-known/openid-configuration`],
    ["api", `${config.apiUrl}/health`],
    ["web", `${config.appUrl}/`],
  ];
  for (const [name, url] of probes) {
    const res = await fetch(url, { redirect: "manual", signal: AbortSignal.timeout(10_000) }).catch((e) => {
      throw new Error(`INTEGRATION=1 but ${name} is not reachable at ${url}: ${e}`);
    });
    if (res.status >= 500) throw new Error(`INTEGRATION=1 but ${name} answered ${res.status} at ${url}`);
  }
}

/** Call once at the top of a *.it.ts file: checks the stack before, removes the throwaway people after. */
export function guardStack() {
  before(async () => {
    if (INTEGRATION) await assertStackReachable();
  });
  after(async () => {
    await cleanupThrowaways();
  });
}

// ---------------------------------------------------------------- cookies and requests

type Cookie = { value: string; httpOnly: boolean; attrs: string };

/** The least a browser does with cookies: remember per address, send back, drop on delete. No paths, no expiry. */
export class CookieJar {
  private byOrigin = new Map<string, Map<string, Cookie>>();

  absorb(url: string, res: Response) {
    const origin = new URL(url).origin;
    const bag = this.byOrigin.get(origin) ?? new Map<string, Cookie>();
    this.byOrigin.set(origin, bag);
    for (const line of res.headers.getSetCookie()) {
      const [pair, ...attrs] = line.split(";").map((s) => s.trim());
      const eq = pair.indexOf("=");
      const name = pair.slice(0, eq);
      const value = pair.slice(eq + 1);
      const lower = attrs.map((a) => a.toLowerCase());
      const maxAge = lower.find((a) => a.startsWith("max-age="));
      const expires = attrs.find((a) => a.toLowerCase().startsWith("expires="));
      const gone =
        value === "" ||
        (maxAge !== undefined && Number(maxAge.split("=")[1]) <= 0) ||
        (expires !== undefined && Date.parse(expires.split("=")[1]) < Date.now());
      if (gone) bag.delete(name);
      else bag.set(name, { value, httpOnly: lower.includes("httponly"), attrs: attrs.join("; ") });
    }
  }

  header(url: string): string {
    const bag = this.byOrigin.get(new URL(url).origin);
    return bag ? [...bag].map(([k, c]) => `${k}=${c.value}`).join("; ") : "";
  }

  cookie(url: string, name: string): Cookie | undefined {
    return this.byOrigin.get(new URL(url).origin)?.get(name);
  }

  set(url: string, name: string, value: string) {
    const origin = new URL(url).origin;
    const bag = this.byOrigin.get(origin) ?? new Map<string, Cookie>();
    this.byOrigin.set(origin, bag);
    bag.set(name, { value, httpOnly: true, attrs: "" });
  }

  clone(): CookieJar {
    const copy = new CookieJar();
    for (const [origin, bag] of this.byOrigin) copy.byOrigin.set(origin, new Map(bag));
    return copy;
  }
}

/** One request, redirects NOT followed, cookies sent and kept. */
export async function http(
  url: string,
  opts: { method?: string; jar?: CookieJar; headers?: Record<string, string>; body?: string } = {},
): Promise<Response> {
  const headers: Record<string, string> = { ...(opts.headers ?? {}) };
  const cookie = opts.jar?.header(url);
  if (cookie) headers.cookie = cookie;
  const res = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body,
    redirect: "manual",
    cache: "no-store",
    signal: AbortSignal.timeout(30_000),
  });
  opts.jar?.absorb(url, res);
  return res;
}

const isRedirect = (res: Response) => res.status >= 300 && res.status < 400 && res.headers.has("location");
const locationOf = (res: Response, from: string) => new URL(res.headers.get("location")!, from).href;

/** Follow redirects by hand until `stop(nextUrl)` says so, or the answer is not a redirect. */
export async function follow(
  start: string,
  jar: CookieJar,
  stop: (nextUrl: string) => boolean = () => false,
): Promise<{ res: Response; url: string }> {
  let url = start;
  for (let i = 0; i < 20; i++) {
    const res = await http(url, { jar });
    if (!isRedirect(res)) return { res, url };
    const next = locationOf(res, url);
    if (stop(next)) return { res, url: next };
    await res.body?.cancel();
    url = next;
  }
  throw new Error(`too many redirects from ${start}`);
}

// ---------------------------------------------------------------- Keycloak admin (throwaway people only)

async function backendToken(): Promise<string> {
  const res = await fetch(`${config.issuer}/protocol/openid-connect/token`, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "client_credentials",
      client_id: config.backendClientId,
      client_secret: config.backendClientSecret,
    }),
  });
  if (!res.ok) throw new Error(`could not get a service account token: ${res.status} ${await res.text()}`);
  return ((await res.json()) as { access_token: string }).access_token;
}

/** The Keycloak admin REST API as the playground-backend service account. */
export async function kcAdmin(method: string, path: string, body?: unknown): Promise<Response> {
  return fetch(`${config.keycloakUrl}/admin/realms/${config.realm}${path}`, {
    method,
    headers: { authorization: `Bearer ${await backendToken()}`, "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export type ThrowawayUser = {
  id: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  /** Removes the person from Keycloak. Safe to call twice. */
  delete(): Promise<void>;
};

const made: ThrowawayUser[] = [];

export async function createThrowawayUser(): Promise<ThrowawayUser> {
  const email = `it-${Math.floor(Date.now() / 1000)}-${randomBytes(4).toString("hex")}@example.test`;
  const password = `Pw-${randomBytes(9).toString("base64url")}1!`;
  const firstName = "Integration";
  const lastName = "Throwaway";
  const res = await kcAdmin("POST", "/users", {
    username: email,
    email,
    firstName,
    lastName,
    emailVerified: false,
    enabled: true,
    credentials: [{ type: "password", value: password, temporary: false }],
  });
  if (res.status !== 201) throw new Error(`could not create ${email}: ${res.status} ${await res.text()}`);
  const id = res.headers.get("location")!.split("/").pop()!;
  let deleted = false;
  const user: ThrowawayUser = {
    id, email, password, firstName, lastName,
    async delete() {
      if (deleted) return;
      const r = await kcAdmin("DELETE", `/users/${id}`);
      if (r.status !== 204 && r.status !== 404) throw new Error(`could not delete ${email}: ${r.status}`);
      deleted = true;
    },
  };
  return user;
}

/** A throwaway person that is removed again when the file ends, pass or fail. */
export async function throwaway(): Promise<ThrowawayUser> {
  const user = await createThrowawayUser();
  made.push(user);
  return user;
}

export async function cleanupThrowaways() {
  const errors: unknown[] = [];
  for (const u of made.splice(0)) await u.delete().catch((e) => errors.push(e));
  if (errors.length) throw new Error(`cleanup failed: ${errors.join("; ")}`);
}

export const keycloakUser = async (id: string) => (await (await kcAdmin("GET", `/users/${id}`)).json()) as { enabled: boolean };

// ---------------------------------------------------------------- the real login, without a browser

export type KeycloakResult =
  | { kind: "callback"; url: string; code: string; state: string }
  | { kind: "form"; html: string };

const unescapeHtml = (s: string) => s.replace(/&amp;/g, "&").replace(/&#x3D;/gi, "=").replace(/&quot;/g, '"').replace(/&#39;/g, "'");

function loginFormAction(html: string): string | null {
  const form = html.match(/<form\b[^>]*\bid="kc-form-login"[^>]*>/i)?.[0];
  const action = form?.match(/\baction="([^"]+)"/i)?.[1];
  return action ? unescapeHtml(action) : null;
}

export const hasLoginForm = (html: string) => loginFormAction(html) !== null;

function asCallback(url: string): KeycloakResult {
  const u = new URL(url);
  return { kind: "callback", url, code: u.searchParams.get("code") ?? "", state: u.searchParams.get("state") ?? "" };
}

const isCallback = (url: string) => url.startsWith(config.callbackUrl);

/** Open the authorization URL. Either Keycloak signs the person in silently (a callback) or it shows a page. */
export async function openAtKeycloak(authUrl: string, jar: CookieJar): Promise<KeycloakResult & { pageUrl?: string }> {
  const { res, url } = await follow(authUrl, jar, isCallback);
  if (isCallback(url)) return asCallback(url);
  return { kind: "form", html: await res.text(), pageUrl: url };
}

/** Log in at Keycloak's own page. Returns the callback URL (not requested), or the page again if Keycloak refused. */
export async function loginAtKeycloak(
  authUrl: string,
  jar: CookieJar,
  user: Pick<ThrowawayUser, "email" | "password">,
): Promise<KeycloakResult> {
  const first = await openAtKeycloak(authUrl, jar);
  if (first.kind === "callback") return first;
  const action = loginFormAction(first.html);
  if (!action) return first; // not a login form: the caller looks at the page
  const posted = await http(action, {
    method: "POST",
    jar,
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: user.email, password: user.password, credentialId: "" }).toString(),
  });
  if (!isRedirect(posted)) return { kind: "form", html: await posted.text() };
  const next = locationOf(posted, action);
  await posted.body?.cancel();
  if (isCallback(next)) return asCallback(next);
  const { res, url } = await follow(next, jar, isCallback);
  if (isCallback(url)) return asCallback(url);
  return { kind: "form", html: await res.text() };
}

export type SignedIn = { jar: CookieJar; location: string; callbackUrl: string; loginCookie: string | undefined; sessionCookie: string | undefined };

/** GET /auth/login, log in at Keycloak, GET the callback. The jar then holds the session cookie. */
export async function signIn(
  user: Pick<ThrowawayUser, "email" | "password">,
  opts: { returnTo?: string; jar?: CookieJar } = {},
): Promise<SignedIn> {
  const jar = opts.jar ?? new CookieJar();
  const q = opts.returnTo === undefined ? "" : `?returnTo=${encodeURIComponent(opts.returnTo)}`;
  const start = await http(`${config.appUrl}/auth/login${q}`, { jar });
  if (!isRedirect(start)) throw new Error(`/auth/login answered ${start.status}, not a redirect`);
  const authUrl = locationOf(start, config.appUrl);
  const loginCookie = jar.cookie(config.appUrl, "playground_login")?.value;
  const kc = await loginAtKeycloak(authUrl, jar, user);
  if (kc.kind !== "callback") throw new Error("Keycloak did not send the person back with a code");
  const back = await http(kc.url, { jar });
  if (!isRedirect(back)) throw new Error(`the callback answered ${back.status}, not a redirect`);
  return {
    jar,
    location: locationOf(back, config.appUrl),
    callbackUrl: kc.url,
    loginCookie,
    sessionCookie: jar.cookie(config.appUrl, "playground_session")?.value,
  };
}

/** The bootstrap administrator. Used only to decide on the throwaway accounts. */
export const ADMIN = { email: "admin@example.test", password: "Admin123!" };
export async function adminSignIn(): Promise<CookieJar> {
  const s = await signIn(ADMIN);
  if (!new URL(s.location).pathname.startsWith("/dashboard")) throw new Error(`admin sign in ended at ${s.location}`);
  return s.jar;
}

/** A call to the API through the web app's own route, with the session cookie. */
export async function backend(jar: CookieJar, method: string, path: string, body?: unknown) {
  const res = await http(`${config.appUrl}/api/backend/${path.replace(/^\//, "")}`, {
    method,
    jar,
    headers: body === undefined ? {} : { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let json: any = null; // eslint-disable-line @typescript-eslint/no-explicit-any
  try { json = JSON.parse(text); } catch { /* not JSON */ }
  // FastAPI wraps a refusal raised in a dependency as {detail: {code}}, a domain refusal as {code}
  const code: string | undefined = json?.code ?? json?.detail?.code;
  return { status: res.status, json, text, code };
}

/** Three base64url parts joined by dots. */
export const looksLikeJwt = (s: string) => /^[\w-]+\.[\w-]+\.[\w-]*$/.test(s);
