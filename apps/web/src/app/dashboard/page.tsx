import Link from "next/link";
import { redirect } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getMe } from "@/lib/api";

export default async function Dashboard() {
  const me = await getMe();

  if (!me.ok) {
    // No session on the server (it restarted) or the token is no longer good: sign in again.
    if (me.status === 401) redirect("/auth/login?returnTo=/dashboard");
    if (me.code === "account_deactivated") {
      return (
        <Notice title="Your account is deactivated">
          An administrator has switched off your access. Nothing you made was removed. Ask an administrator to reinstate you.
        </Notice>
      );
    }
    return <Notice title="The API is not reachable">Start it with <code>uv run uvicorn app.main:create_app --factory</code>.</Notice>;
  }

  const account = me.data;
  if (account.status === "pending") {
    return (
      <Notice title="Waiting for approval">
        Hello {account.name}. Your account was created, and an administrator needs to approve it before you can use Playground.
        Until then this is the only page you can see.
      </Notice>
    );
  }

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Hello, {account.name}</CardTitle>
        <CardDescription>You are signed in through Keycloak.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Row label="Email">{account.email}</Row>
        <Row label="Role"><Badge variant="secondary">{account.role}</Badge></Row>
        <Row label="Status"><Badge>{account.status}</Badge></Row>
        {account.role === "administrator" && (
          <Link href="/admin/accounts" className={buttonVariants({ variant: "outline" })}>Manage accounts</Link>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b pb-2">
      <span className="text-muted-foreground">{label}</span>
      <span>{children}</span>
    </div>
  );
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">{children}</CardContent>
    </Card>
  );
}
