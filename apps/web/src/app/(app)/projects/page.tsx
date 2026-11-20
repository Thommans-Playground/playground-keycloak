import { redirect } from "next/navigation";
import { ProjectsTable } from "@/components/projects-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getMe, type Project } from "@/lib/api";

export default async function ProjectsPage() {
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why

  const projects = await api<Project[]>("/projects");
  if (!projects.ok) redirect(projects.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Projects</CardTitle>
      </CardHeader>
      <CardContent>
        <ProjectsTable projects={projects.data} isAdmin={me.data.role === "administrator"} />
      </CardContent>
    </Card>
  );
}
