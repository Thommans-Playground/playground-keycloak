import { LOGIN_ATTEMPT_TTL_MS, type LoginAttempt } from "../domain/login-attempt.ts";
import type { Session } from "../domain/session.ts";
import type { LoginAttemptStore, SessionStore } from "../application/ports.ts";

// Redis, the engine of Amazon ElastiCache. Every entry has a TTL, so entries expire by themselves.

/** The few commands we use. A node-redis client fits; so does anything with the same shape. */
export interface RedisLike {
  set(key: string, value: string, options: { expiration: { type: "EX" | "PX"; value: number } }): Promise<unknown>;
  get(key: string): Promise<string | null>;
  getDel(key: string): Promise<string | null>;
}

export class RedisLoginAttemptStore implements LoginAttemptStore {
  private prefix: string;
  private now: () => number;
  private redis: RedisLike;
  constructor(redis: RedisLike, opts: { prefix?: string; now?: () => number } = {}) {
    this.redis = redis;
    this.prefix = opts.prefix ?? "login-attempt:";
    this.now = opts.now ?? Date.now;
  }

  async save(id: string, attempt: LoginAttempt) {
    // Live for the time it has left, so it vanishes when it would be refused anyway.
    const remainingMs = attempt.startedAt + LOGIN_ATTEMPT_TTL_MS - this.now();
    if (remainingMs <= 0) return;
    await this.redis.set(this.prefix + id, JSON.stringify(attempt), { expiration: { type: "PX", value: remainingMs } });
  }

  async take(id: string | undefined) {
    if (!id) return null;
    const raw = await this.redis.getDel(this.prefix + id); // atomic: read and forget in one command
    return raw ? (JSON.parse(raw) as LoginAttempt) : null;
  }
}

/** A session has no end of its own in the domain, so an abandoned one is dropped after this long. */
export const DEFAULT_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60;

export class RedisSessionStore implements SessionStore {
  private prefix: string;
  private ttlSeconds: number;
  private redis: RedisLike;
  constructor(redis: RedisLike, opts: { prefix?: string; ttlSeconds?: number } = {}) {
    this.redis = redis;
    this.prefix = opts.prefix ?? "session:";
    this.ttlSeconds = opts.ttlSeconds ?? DEFAULT_SESSION_TTL_SECONDS;
  }

  async get(id: string | undefined) {
    if (!id) return null;
    return parse(await this.redis.get(this.prefix + id));
  }

  async put(id: string, session: Session) {
    await this.redis.set(this.prefix + id, JSON.stringify(session), {
      expiration: { type: "EX", value: this.ttlSeconds },
    });
  }

  async take(id: string | undefined) {
    if (!id) return null;
    return parse(await this.redis.getDel(this.prefix + id));
  }
}

const parse = (raw: string | null) => (raw ? (JSON.parse(raw) as Session) : null);
