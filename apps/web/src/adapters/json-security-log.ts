import { createHash } from "node:crypto";
import type { SecurityEvent, SecurityLog } from "../application/ports.ts";

const REASON = /^[a-z_]{1,40}$/;

/**
 * One JSON line on stdout for each security event (ADR 0010). On AWS the awslogs driver sends stdout to CloudWatch.
 * Only the keys below can be written. The reason must be a short code, and the session is a hash.
 */
export class JsonSecurityLog implements SecurityLog {
  private write: (line: string) => void;
  private clock: () => Date;

  constructor(
    write: (line: string) => void = (line) => void process.stdout.write(line),
    clock: () => Date = () => new Date(),
  ) {
    this.write = write;
    this.clock = clock;
  }

  event(e: SecurityEvent): void {
    const line: Record<string, string> = { ts: this.clock().toISOString(), event: e.name, result: e.result };
    if (e.personId) line.person_id = e.personId;
    if (e.sessionId) line.session = createHash("sha256").update(e.sessionId).digest("hex").slice(0, 16);
    if (e.reason && REASON.test(e.reason)) line.reason = e.reason;
    this.write(JSON.stringify(line) + "\n");
  }
}
