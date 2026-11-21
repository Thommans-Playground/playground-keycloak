import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { AddMemberForm } from "@/components/add-member-form";
import { RemoveMemberButton } from "@/components/remove-member-button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { memberCandidates } from "@/domain/member-candidates";
import { memberLabel, projectSummary } from "@/domain/project-summary";
import { api, getMe, type Account, type Project } from "@/lib/api";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const back = `/auth/login?returnTo=${encodeURIComponent(`/projects/${id}`)}`;
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? back : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why

  const project = await api<Project>(`/projects/${encodeURIComponent(id)}`);
  if (!project.ok) {
    if (project.status === 404) notFound(); // hidden, missing and malformed read the same
    redirect(project.status === 401 ? back : "/dashboard");
  }

  const isAdmin = me.data.role === "administrator";
  let candidates: Account[] = [];
  if (isAdmin) {
    const accounts = await api<Account[]>("/accounts?status=active");
    if (accounts.ok) candidates = memberCandidates(accounts.data, project.data.members);
  }

  const { name, members } = project.data;
  return (
    <div className="space-y-4">
      <Link href="/projects" className="text-sm underline-offset-4 hover:underline">
        Back to projects
      </Link>
      <Card>
        <CardHeader>
          <CardTitle>{name}</CardTitle>
          <CardDescription>{projectSummary(project.data)}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {members.length === 0 ? (
            <p className="text-sm text-muted-foreground">This project has no members yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Member</TableHead>
                  {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell>{memberLabel(m)}</TableCell>
                    {isAdmin && (
                      <TableCell className="text-right">
                        <RemoveMemberButton projectId={project.data.id} member={{ id: m.id, name: memberLabel(m) }} />
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {isAdmin && (
            <AddMemberForm
              projectId={project.data.id}
              candidates={candidates.map((c) => ({ id: c.id, name: c.name }))}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
