import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { projectRefusalMessage } from "@/domain/project-messages";

// One page for a hidden, a missing and a malformed project, with no hint which (AC-27, AC-84).
export default function ProjectNotFound() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Project</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p>{projectRefusalMessage("project_not_found")}</p>
        <Link href="/projects" className="text-sm underline-offset-4 hover:underline">
          Back to projects
        </Link>
      </CardContent>
    </Card>
  );
}
