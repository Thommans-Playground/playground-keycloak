import Link from "next/link";
import { redirect } from "next/navigation";
import { CreateProjectForm } from "@/components/create-project-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { memberCandidates } from "@/domain/member-candidates";
import { api, getMe, type Account } from "@/lib/api";

export default async function NewProjectPage() {
  const back = "/auth/login?returnTo=/projects/new";
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? back : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why
  if (me.data.role !== "administrator") redirect("/projects"); // the server refuses anyway (AC-11)

  const accounts = await api<Account[]>("/accounts?status=active");
  if (!accounts.ok) redirect(accounts.status === 401 ? back : "/projects");

  return (
    <div className="space-y-4">
      <Link href="/projects" className="text-sm underline-offset-4 hover:underline">
        Back to projects
      </Link>
      <Card>
        <CardHeader>
          <CardTitle>Create project</CardTitle>
        </CardHeader>
        <CardContent>
          <CreateProjectForm choices={memberCandidates(accounts.data, []).map((a) => ({ id: a.id, name: a.name }))} />
        </CardContent>
      </Card>
    </div>
  );
}
