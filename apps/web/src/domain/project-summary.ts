export type ProjectMember = { id: string; name: string | null };

/** The line shown for a project on the list. */
export function projectSummary(project: { members: ProjectMember[] }): string {
  const n = project.members.length;
  if (n === 0) return "No members yet";
  return n === 1 ? "1 member" : `${n} members`;
}

/** A member by name; neutral when the name is unknown, never the raw id. */
export function memberLabel(member: ProjectMember): string {
  return member.name ?? "Unknown person";
}
