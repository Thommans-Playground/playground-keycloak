import Link from "next/link";
import { redirect } from "next/navigation";
import { KeyRound, ScrollText, UserCheck } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { hasSession } from "@/lib/auth/session";

const FEATURES = [
  {
    icon: KeyRound,
    title: "Single sign on",
    text: "Sign in through Keycloak with Authorization Code and PKCE. The browser never sees a token.",
  },
  {
    icon: UserCheck,
    title: "Approval before access",
    text: "New accounts wait for an administrator. Roles and status are checked on every request.",
  },
  {
    icon: ScrollText,
    title: "Audited changes",
    text: "Every account change needs a reason and lands in the audit trail.",
  },
];

export default async function Landing() {
  if (await hasSession()) redirect("/dashboard");

  return (
    <>
      <section className="border-b bg-accent">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
          <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
            A small app to learn Keycloak with
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-muted-foreground">
            Sign in, get approved, and see how identity and permissions fit together between Keycloak, a Next.js front
            end and a FastAPI back end.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/login" className={buttonVariants({ size: "lg" })}>
              Sign in
            </Link>
            <a href="/auth/login?register=1" className={buttonVariants({ size: "lg", variant: "outline" })}>
              Create account
            </a>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold">What you can try</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="mb-2 size-6 text-primary" aria-hidden />
                <CardTitle>{title}</CardTitle>
                <CardDescription>{text}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>
    </>
  );
}
