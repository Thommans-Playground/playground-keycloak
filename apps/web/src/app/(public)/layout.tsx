import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { hasSession } from "@/lib/auth/session";

export default async function PublicLayout({ children }: { children: React.ReactNode }) {
  const signedIn = await hasSession();
  return (
    <>
      <header className="border-b bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <ShieldCheck className="size-5 text-primary" aria-hidden />
            Playground
          </Link>
          <nav className="flex items-center gap-3">
            {signedIn ? (
              <Link href="/dashboard" className={buttonVariants({ size: "sm" })}>Go to dashboard</Link>
            ) : (
              <Link href="/login" className={buttonVariants({ size: "sm" })}>Sign in</Link>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t bg-muted">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:justify-between">
          <span>Playground: a Keycloak learning app.</span>
          <span>Styled with the Singapore Government Design System.</span>
        </div>
      </footer>
    </>
  );
}
