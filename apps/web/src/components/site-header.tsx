import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { getMe } from "@/lib/api";
import { hasSession } from "@/lib/auth/session";

export async function SiteHeader() {
  const signedIn = await hasSession();
  const me = signedIn ? await getMe() : null;
  const account = me?.ok ? me.data : null;

  return (
    <header className="border-b">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="font-semibold">Playground</Link>
          {account?.status === "active" && (
            <nav className="flex gap-4 text-sm text-muted-foreground">
              <Link href="/dashboard" className="hover:text-foreground">Dashboard</Link>
              {account.role === "administrator" && (
                <Link href="/admin/accounts" className="hover:text-foreground">Accounts</Link>
              )}
            </nav>
          )}
        </div>
        {signedIn ? (
          <div className="flex items-center gap-3 text-sm">
            {account && (
              <>
                <span>{account.name}</span>
                <Badge variant="secondary">{account.role}</Badge>
              </>
            )}
            <form action="/auth/logout" method="post">
              <Button type="submit" variant="outline" size="sm">Sign out</Button>
            </form>
          </div>
        ) : (
          <a href="/auth/login" className={buttonVariants({ variant: "outline", size: "sm" })}>Sign in</a>
        )}
      </div>
    </header>
  );
}
