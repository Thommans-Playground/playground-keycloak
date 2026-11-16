import { redirect } from "next/navigation";
import { AccountsTable } from "@/components/accounts-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, getMe, type Account, type AuditEntry } from "@/lib/api";

export default async function AccountsPage() {
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? "/auth/login?returnTo=/admin/accounts" : "/dashboard");
  if (me.data.status !== "active" || me.data.role !== "administrator") redirect("/dashboard");

  const [accounts, audit] = await Promise.all([api<Account[]>("/accounts"), api<AuditEntry[]>("/audit")]);
  if (!accounts.ok || !audit.ok) redirect("/dashboard");
  const names = new Map(accounts.data.map((a) => [a.id, a.name]));

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
                  <TableCell>{e.actor_id ? (names.get(e.actor_id) ?? e.actor_id) : "system"}</TableCell>
                  <TableCell>{e.action}</TableCell>
                  <TableCell>{names.get(e.target_id) ?? e.target_id}</TableCell>
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
