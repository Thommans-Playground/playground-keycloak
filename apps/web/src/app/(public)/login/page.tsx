import Link from "next/link";
import { redirect } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { hasSession } from "@/lib/auth/session";

const ERRORS: Record<string, string> = {
  login_expired: "That sign in took too long, or was already used. Please try again.",
  login_refused: "Keycloak did not sign you in.",
  login_failed: "Sign in could not be completed. Please try again.",
  identity_provider_unavailable: "Sign in is not available right now. Please try again in a moment.",
};

export default async function Login({ searchParams }: PageProps<"/login">) {
  if (await hasSession()) redirect("/dashboard");
  const { error } = await searchParams;
  const message = typeof error === "string" ? (ERRORS[error] ?? "Something went wrong.") : null;

  return (
    <div className="mx-auto w-full max-w-md px-4 py-16">
      <div className="space-y-4">
        {message && (
          <Alert variant="destructive">
            <AlertTitle>Could not sign in</AlertTitle>
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Sign in</CardTitle>
            <CardDescription>You will be taken to Keycloak to sign in, then brought back here.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <a href="/auth/login" className={buttonVariants({ size: "lg", className: "w-full" })}>
              Sign in with Keycloak
            </a>
            <p className="text-center text-sm text-muted-foreground">
              New here?{" "}
              <a href="/auth/login?register=1" className="text-primary underline underline-offset-4">
                Create an account
              </a>
              . An administrator must approve it before you can use the app.
            </p>
          </CardContent>
        </Card>
        <p className="text-center text-sm">
          <Link href="/" className="text-muted-foreground hover:text-foreground">
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
