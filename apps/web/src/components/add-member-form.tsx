"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { projectRefusalMessage } from "@/domain/project-messages";

export function AddMemberForm({
  projectId,
  candidates,
}: {
  projectId: string;
  candidates: { id: string; name: string }[];
}) {
  const router = useRouter();
  const [accountId, setAccountId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (candidates.length === 0) {
    return <p className="text-sm text-muted-foreground">Nobody is left to add: every active person is a member.</p>;
  }

  async function add() {
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/backend/projects/${encodeURIComponent(projectId)}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_id: accountId }),
    });
    setBusy(false);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(projectRefusalMessage(body?.code ?? body?.detail?.code ?? ""));
      return;
    }
    setAccountId("");
    router.refresh();
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <select
          aria-label="Person to add"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="h-8 min-w-48 rounded-lg border border-border bg-background px-2 text-sm"
        >
          <option value="">Choose a person</option>
          {candidates.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <Button disabled={busy || accountId === ""} onClick={add}>
          Add member
        </Button>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
