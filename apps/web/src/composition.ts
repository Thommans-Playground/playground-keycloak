import "server-only";
import { randomBytes } from "node:crypto";
import { createClient } from "redis";
import { env } from "@/lib/auth/config";
import { FetchBackendApi } from "./adapters/fetch-backend-api.ts";
import { InMemoryLoginAttemptStore, InMemorySessionStore } from "./adapters/in-memory-stores.ts";
import { RedisLoginAttemptStore, RedisSessionStore } from "./adapters/redis-stores.ts";
import { KeycloakIdentityProvider } from "./adapters/keycloak-identity-provider.ts";
import { makeAccessToken } from "./application/access-token.ts";
import { makeCallBackend } from "./application/call-backend.ts";
import { finishLogin, startLogin } from "./application/sign-in.ts";
import { signOut } from "./application/sign-out.ts";

/**
 * The one place that says "use Keycloak, keep sessions in Redis (or in memory), call the API over HTTP".
 * REDIS_URL set: Redis (Amazon ElastiCache on AWS). Not set: in memory, one process, lost on restart.
 */
function buildStores() {
  const url = process.env.REDIS_URL;
  if (!url) return { attempts: new InMemoryLoginAttemptStore(), sessions: new InMemorySessionStore() };
  const client = createClient({ url });
  client.on("error", (e) => console.error("redis:", e)); // node-redis reconnects by itself
  void client.connect().catch((e) => console.error("redis connect:", e));
  return { attempts: new RedisLoginAttemptStore(client), sessions: new RedisSessionStore(client) };
}

function build() {
  const now = () => Date.now();
  const newId = () => randomBytes(32).toString("base64url");

  const idp = new KeycloakIdentityProvider({
    appUrl: env.appUrl,
    issuer: env.issuer,
    internalIssuer: env.internalIssuer,
    clientId: env.clientId,
    clientSecret: env.clientSecret,
  });
  const { attempts, sessions } = buildStores();
  const backend = new FetchBackendApi(env.apiUrl);

  const signInDeps = { idp, attempts, sessions, now, newId };
  const accessTokenFor = makeAccessToken({ idp, sessions, now });

  return {
    startLogin: (input: { returnTo: string | null | undefined; register: boolean }) => startLogin(signInDeps, input),
    finishLogin: (attemptId: string | undefined, callbackUrl: URL) => finishLogin(signInDeps, attemptId, callbackUrl),
    signOut: (sessionId: string | undefined) => signOut({ idp, sessions }, sessionId),
    callBackend: makeCallBackend({ accessTokenFor, backend }),
    hasSession: async (sessionId: string | undefined) => (await sessions.get(sessionId)) !== null,
  };
}

// Built on first use (so the environment is read at run time, not at build time), and kept across dev reloads.
const g = globalThis as unknown as { __playgroundApp?: ReturnType<typeof build> };
export const app = () => (g.__playgroundApp ??= build());
