import Link from "next/link";
import { redirect } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { AppNav } from "@/components/app-nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getMe } from "@/lib/api";

export default async function AppShell({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  if (!me.ok && me.status === 401) redirect("/auth/login?returnTo=/dashboard");
  const account = me.ok ? me.data : null;
  const isAdmin = account?.status === "active" && account.role === "administrator";

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <aside className="border-b bg-sidebar md:w-60 md:border-r md:border-b-0">
        <div className="flex h-16 items-center gap-2 border-b px-4 font-semibold">
          <ShieldCheck className="size-5 text-primary" aria-hidden />
          <Link href="/dashboard">Playground</Link>
        </div>
        <div className="p-3">{account?.status === "active" ? <AppNav isAdmin={isAdmin} /> : null}</div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-end gap-3 border-b bg-card px-4 text-sm">
          {account && (
            <>
              <span className="font-medium">{account.name}</span>
              <Badge variant="secondary">{account.role}</Badge>
            </>
          )}
          <form action="/auth/logout" method="post">
            <Button type="submit" variant="outline" size="sm">
              Sign out
            </Button>
          </form>
        </header>
        <main className="flex-1 bg-muted/40 p-6">
          <div className="mx-auto w-full max-w-5xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
