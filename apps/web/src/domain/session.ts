/** The tokens. They live on the server. The browser holds only an opaque session id. */
export type Session = {
  idToken: string;
  accessToken: string;
  refreshToken: string | undefined;
  accessExpiresAt: number; // ms since epoch
};

/** Refresh a little early, so a token never expires in flight. */
export const REFRESH_SKEW_MS = 30_000;

export function needsRefresh(session: Session, now: number): boolean {
  return session.accessExpiresAt - now <= REFRESH_SKEW_MS;
}
