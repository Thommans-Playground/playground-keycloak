// The warning an administrator sees next to an account whose email another account also has (AC-73).
// Pure: it only builds the sentence. Nothing is blocked by it.
export type DuplicateOf = { id: string; name: string; status: "pending" | "active" | "deactivated" };

export function duplicateWarning(others: DuplicateOf[] | undefined): string | null {
  if (!others || others.length === 0) return null;
  const list = others.map((o) => `${o.name} (${o.status})`).join(", ");
  return `${others.length === 1 ? "Another account has" : "Other accounts have"} this email: ${list}`;
}
