function need(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing environment variable ${name}`);
  return v;
}

export const env = {
  get appUrl() {
    return need("APP_URL");
  },
  get apiUrl() {
    return need("API_URL");
  },
  get issuer() {
    return need("KEYCLOAK_ISSUER");
  },
  /** Set in Docker, where the server reaches Keycloak at a different address than the browser does. */
  get internalIssuer() {
    return process.env.KEYCLOAK_INTERNAL_ISSUER || undefined;
  },
  get clientId() {
    return need("KEYCLOAK_CLIENT_ID");
  },
  get clientSecret() {
    return need("KEYCLOAK_CLIENT_SECRET");
  },
};

export const SESSION_COOKIE = "playground_session";
export const LOGIN_COOKIE = "playground_login";
