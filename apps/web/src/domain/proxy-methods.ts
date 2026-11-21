// The methods the BFF proxy forwards to the API (ADR 0016). PUT and PATCH are left out on purpose:
// no use case needs them, and each method is one more a browser script could send.
export const PROXY_METHODS: readonly string[] = ["GET", "POST", "DELETE"];

/** GET, HEAD and DELETE carry no body. */
export function methodHasBody(method: string): boolean {
  return !["GET", "HEAD", "DELETE"].includes(method);
}
