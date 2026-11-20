import Link from "next/link";
import { redirect } from "next/navigation";
import { ProjectsTable } from "@/components/projects-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getMe, type Project } from "@/lib/api";

export default async function ProjectsPage() {
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why

  const projects = await api<Project[]>("/projects");
  if (!projects.ok) redirect(projects.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");

  const isAdmin = me.data.role === "administrator";
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Projects</CardTitle>
        {isAdmin && <Button render={<Link href="/projects/new" />}>Create project</Button>}
      </CardHeader>
      <CardContent>
        <ProjectsTable projects={projects.data} isAdmin={isAdmin} />
      </CardContent>
    </Card>
  );
}
