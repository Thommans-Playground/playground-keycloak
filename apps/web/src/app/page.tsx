import { redirect } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { hasSession } from "@/lib/auth/session";

const ERRORS: Record<string, string> = {
  login_expired: "That sign in took too long, or was already used. Please try again.",
  login_refused: "Keycloak did not sign you in.",
  login_failed: "Sign in could not be completed. Please try again.",
  identity_provider_unavailable: "Keycloak is not reachable. Is it running on port 8080?",
};

export default async function Home({ searchParams }: PageProps<"/">) {
  if (await hasSession()) redirect("/dashboard");
  const { error } = await searchParams;
  const message = typeof error === "string" ? (ERRORS[error] ?? "Something went wrong.") : null;

  return (
    <div className="mx-auto max-w-md space-y-4">
      {message && (
        <Alert variant="destructive">
          <AlertTitle>Could not sign in</AlertTitle>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Welcome to Playground</CardTitle>
          <CardDescription>
            Sign in with Keycloak. New here? Create an account, then wait for an administrator to approve it.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <a href="/auth/login" className={buttonVariants()}>Sign in</a>
          <a href="/auth/login?register=1" className={buttonVariants({ variant: "outline" })}>Create account</a>
        </CardContent>
      </Card>
    </div>
  );
}
