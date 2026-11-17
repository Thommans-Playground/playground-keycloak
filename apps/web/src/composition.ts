import "server-only";
import { randomBytes } from "node:crypto";
import { env } from "@/lib/auth/config";
import { FetchBackendApi } from "./adapters/fetch-backend-api.ts";
import { InMemoryLoginAttemptStore, InMemorySessionStore } from "./adapters/in-memory-stores.ts";
import { KeycloakIdentityProvider } from "./adapters/keycloak-identity-provider.ts";
import { makeAccessToken } from "./application/access-token.ts";
import { makeCallBackend } from "./application/call-backend.ts";
import { finishLogin, startLogin } from "./application/sign-in.ts";
import { signOut } from "./application/sign-out.ts";

/**
 * The one place that says "use Keycloak, keep sessions in memory, call the API over HTTP".
 * To use ElastiCache for sessions, write an adapter and change the two `new InMemory...` lines here.
 */
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
  const attempts = new InMemoryLoginAttemptStore();
  const sessions = new InMemorySessionStore();
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
