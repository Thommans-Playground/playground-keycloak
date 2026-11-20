/**
 * Where a person changes their name, email or password: Keycloak's account console for the realm.
 * The issuer is the public address of the realm (`<keycloak>/realms/<realm>`), the one address we already configure.
 */
export function accountPageUrl(issuer: string): string {
  return `${issuer.replace(/\/+$/, "")}/account`;
}
