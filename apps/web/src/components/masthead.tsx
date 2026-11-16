import { Landmark } from "lucide-react";

/** The official-site banner, in the style of the SGDS masthead. */
export function Masthead() {
  return (
    <div className="bg-muted text-xs">
      <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-1.5">
        <Landmark className="size-3.5 text-muted-foreground" aria-hidden />
        <span>This is a learning playground, styled after the Singapore Government Design System.</span>
      </div>
    </div>
  );
}
