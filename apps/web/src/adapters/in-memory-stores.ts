import type { LoginAttemptStore, SessionStore } from "../application/ports.ts";
import type { LoginAttempt } from "../domain/login-attempt.ts";
import type { Session } from "../domain/session.ts";

// In memory: a restart signs everyone out and a second copy of the server would not see these.
// For AWS, write an ElastiCache adapter with the same two interfaces and change composition.ts only.

export class InMemoryLoginAttemptStore implements LoginAttemptStore {
  private rows = new Map<string, LoginAttempt>();

  async save(id: string, attempt: LoginAttempt) {
    this.rows.set(id, attempt);
  }

  async take(id: string | undefined) {
    if (!id) return null;
    const attempt = this.rows.get(id) ?? null;
    this.rows.delete(id); // single use, even when it turns out to be expired
    return attempt;
  }
}

export class InMemorySessionStore implements SessionStore {
  private rows = new Map<string, Session>();

  async get(id: string | undefined) {
    return id ? (this.rows.get(id) ?? null) : null;
  }

  async put(id: string, session: Session) {
    this.rows.set(id, session);
  }

  async take(id: string | undefined) {
    if (!id) return null;
    const session = this.rows.get(id) ?? null;
    this.rows.delete(id);
    return session;
  }
}
