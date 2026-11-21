import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { projectSummary } from "@/domain/project-summary";
import type { Project } from "@/lib/api";

export function ProjectsTable({ projects, isAdmin }: { projects: Project[]; isAdmin: boolean }) {
  if (projects.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {isAdmin ? "No projects exist yet." : "You are not in any project yet."}
      </p>
    );
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Members</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {projects.map((p) => (
          <TableRow key={p.id}>
            <TableCell>
              <Link href={`/projects/${p.id}`} className="font-medium underline-offset-4 hover:underline">
                {p.name}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{projectSummary(p)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
