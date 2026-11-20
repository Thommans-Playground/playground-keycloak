"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import type { Account } from "@/lib/api";
import { duplicateWarning } from "@/domain/duplicate-warning";

type Action = "approve" | "deactivate" | "reinstate" | "promote" | "demote";

// Approving needs no reason. Every other change does (RULE-A3).
const NEEDS_REASON: Record<Action, boolean> = {
  approve: false, deactivate: true, reinstate: true, promote: true, demote: true,
};

function actionsFor(a: Account, isSelf: boolean): Action[] {
  if (a.status === "pending") return ["approve"];
  if (a.status === "deactivated") return ["reinstate"];
  if (isSelf) return []; // nobody changes themselves (RULE-A2)
  return [a.role === "administrator" ? "demote" : "promote", "deactivate"];
}

export function AccountsTable({ accounts, currentId }: { accounts: Account[]; currentId: string }) {
  const router = useRouter();
  const [pending, setPending] = useState<{ account: Account; action: Action } | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(account: Account, action: Action, why?: string) {
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/backend/accounts/${account.id}/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: why }),
    });
    setBusy(false);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(body.message ?? body.detail?.message ?? "That did not work.");
      return;
    }
    setPending(null);
    setReason("");
    router.refresh();
  }

  function choose(account: Account, action: Action) {
    setError(null);
    if (NEEDS_REASON[action]) setPending({ account, action });
    else void run(account, action);
  }

  return (
    <>
      {error && !pending && (
        <Alert variant="destructive" className="mb-4"><AlertDescription>{error}</AlertDescription></Alert>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Person</TableHead><TableHead>Role</TableHead>
            <TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {accounts.map((a) => (
            <TableRow key={a.id}>
              <TableCell>
                <div className="font-medium">{a.name}{a.id === currentId && " (you)"}</div>
                <div className="text-xs text-muted-foreground">{a.email}</div>
                {duplicateWarning(a.duplicate_of) && (
                  <div className="mt-1 text-xs font-medium text-amber-700 dark:text-amber-400" role="note">
                    {duplicateWarning(a.duplicate_of)}
                  </div>
                )}
              </TableCell>
              <TableCell><Badge variant="secondary">{a.role}</Badge></TableCell>
              <TableCell>
                <Badge variant={a.status === "deactivated" ? "destructive" : a.status === "pending" ? "outline" : "default"}>
                  {a.status}
                </Badge>
              </TableCell>
              <TableCell className="space-x-2 text-right">
                {actionsFor(a, a.id === currentId).map((action) => (
                  <Button
                    key={action}
                    size="sm"
                    variant={action === "deactivate" ? "destructive" : "outline"}
                    disabled={busy}
                    onClick={() => choose(a, action)}
                  >
                    {action}
                  </Button>
                ))}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={pending !== null} onOpenChange={(open) => !open && (setPending(null), setReason(""), setError(null))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="capitalize">{pending?.action} {pending?.account.name}</DialogTitle>
            <DialogDescription>Say why. The reason goes into the audit trail.</DialogDescription>
          </DialogHeader>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="For example: left the team" />
          {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
          <DialogFooter>
            <Button disabled={busy} onClick={() => pending && run(pending.account, pending.action, reason)}>
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
