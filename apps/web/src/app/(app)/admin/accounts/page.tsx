import { redirect } from "next/navigation";
import { AccountsTable } from "@/components/accounts-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { personAtTheTime, type ShownPerson } from "@/domain/audit-person";
import { api, getMe, type Account, type AuditEntry } from "@/lib/api";

function Person({ p }: { p: ShownPerson }) {
  return (
    <>
      <div>{p.name}</div>
      {p.email && <div className="text-xs text-muted-foreground">{p.email}</div>}
    </>
  );
}

export default async function AccountsPage() {
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? "/auth/login?returnTo=/admin/accounts" : "/dashboard");
  if (me.data.status !== "active" || me.data.role !== "administrator") redirect("/dashboard");

  const [accounts, audit] = await Promise.all([api<Account[]>("/accounts"), api<AuditEntry[]>("/audit")]);
  if (!accounts.ok || !audit.ok) redirect("/dashboard");
  const current = new Map(accounts.data.map((a) => [a.id, { name: a.name, email: a.email }]));

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader><CardTitle>Accounts</CardTitle></CardHeader>
        <CardContent><AccountsTable accounts={accounts.data} currentId={me.data.id} /></CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Audit trail</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>When</TableHead><TableHead>Who</TableHead><TableHead>What</TableHead>
                <TableHead>To</TableHead><TableHead>Why</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {audit.data.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="whitespace-nowrap">{new Date(e.at + "Z").toLocaleString()}</TableCell>
                  <TableCell><Person p={personAtTheTime({ id: e.actor_id, name: e.actor_name, email: e.actor_email }, current)} /></TableCell>
                  <TableCell>{e.action}</TableCell>
                  <TableCell><Person p={personAtTheTime({ id: e.target_id, name: e.target_name, email: e.target_email }, current)} /></TableCell>
                  <TableCell className="text-muted-foreground">{e.reason ?? ""}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
