export type CandidateAccount = { id: string; name: string; status: string };

/** The active accounts that are not yet members, sorted by name. A convenience: the server still decides. */
export function memberCandidates<A extends CandidateAccount>(accounts: A[], members: { id: string }[]): A[] {
  const taken = new Set(members.map((m) => m.id));
  return accounts
    .filter((a) => a.status === "active" && !taken.has(a.id))
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }));
}
