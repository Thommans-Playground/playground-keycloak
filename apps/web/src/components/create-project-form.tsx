"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { looksLikeAName } from "@/domain/project-name";
import { projectRefusalMessage } from "@/domain/project-messages";

export function CreateProjectForm({ choices }: { choices: { id: string; name: string }[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function toggle(id: string) {
    setMembers((current) => (current.includes(id) ? current.filter((m) => m !== id) : [...current, id]));
  }

  async function create() {
    setBusy(true);
    setError(null);
    const res = await fetch("/api/backend/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, members }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setBusy(false);
      setError(projectRefusalMessage(body?.code ?? body?.detail?.code ?? ""));
      return;
    }
    const created = await res.json().catch(() => null);
    if (typeof created?.id !== "string") {
      setBusy(false);
      router.push("/projects");
      router.refresh();
      return;
    }
    router.push(`/projects/${encodeURIComponent(created.id)}`);
    router.refresh();
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!busy && looksLikeAName(name)) void create();
      }}
    >
      <div className="space-y-1">
        <label htmlFor="project-name" className="text-sm font-medium">
          Project name
        </label>
        <input
          id="project-name"
          name="name"
          maxLength={100}
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="h-8 w-full max-w-md rounded-lg border border-border bg-background px-2 text-sm"
        />
      </div>
      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">First members (optional, at most 50)</legend>
        {choices.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active people to add yet.</p>
        ) : (
          <ul className="max-h-64 space-y-1 overflow-y-auto">
            {choices.map((c) => (
              <li key={c.id}>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    name="members"
                    value={c.id}
                    checked={members.includes(c.id)}
                    disabled={!members.includes(c.id) && members.length >= 50}
                    onChange={() => toggle(c.id)}
                  />
                  {c.name}
                </label>
              </li>
            ))}
          </ul>
        )}
      </fieldset>
      <Button type="submit" disabled={busy || !looksLikeAName(name)}>
        Create
      </Button>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </form>
  );
}
