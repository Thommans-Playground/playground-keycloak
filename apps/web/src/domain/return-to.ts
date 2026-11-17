const DEFAULT = "/dashboard";

/** A return address must be a local path. Anything else would be an open redirect. */
export function safeReturnTo(value: string | null | undefined): string {
  if (!value || !value.startsWith("/")) return DEFAULT;
  if (value.startsWith("//") || value.startsWith("/\\")) return DEFAULT;
  if (/[\u0000-\u001f]/.test(value)) return DEFAULT;
  return value;
}
