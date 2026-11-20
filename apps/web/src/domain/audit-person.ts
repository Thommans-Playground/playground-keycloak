// Who an audit entry shows: the name and email the person had at the time (AC-70, RULE-L4).
// Only an old entry, stored before names were kept, falls back to the current account. Pure.
export type EntryPerson = { id: string | null; name: string | null; email: string | null };
export type CurrentAccounts = ReadonlyMap<string, { name: string; email: string }>;
export type ShownPerson = { name: string; email: string | null };

export function personAtTheTime(person: EntryPerson, current: CurrentAccounts): ShownPerson {
  if (person.id === null) return { name: "system", email: null };
  if (person.name !== null) return { name: person.name, email: person.email };
  const now = current.get(person.id);
  return now ? { name: now.name, email: now.email } : { name: person.id, email: null };
}
