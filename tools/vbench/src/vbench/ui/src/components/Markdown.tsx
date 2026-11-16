import { Link } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { useProject } from "@/components/AppShell"
import { Mermaid } from "@/components/Mermaid"

const EXTERNAL = /^[a-z][a-z0-9+.-]*:/i

/** `docs/usecase-diagrams` + `../_style.puml` -> `docs/_style.puml` */
function resolve(from: string, href: string): string {
  const parts = from.split("/").slice(0, -1)
  for (const seg of href.split("#")[0].split("/")) {
    if (seg === "..") parts.pop()
    else if (seg && seg !== ".") parts.push(seg)
  }
  return parts.join("/")
}

// Generated blocks are labelled, not hidden: a reader should know which text a command rewrites.
function label(source: string): string {
  return source
    .replace(/<!-- vbench:begin ([\w-]+) -->\n/g, "*Generated block `$1`. Do not edit it; change the specs and run `vbench sync`.*\n\n")
    .replace(/<!-- vbench:end [\w-]+ -->\n?/g, "")
}

// Rendered without raw HTML, so a document cannot inject markup. Mermaid fences are drawn as diagrams, and
// relative links to specs, documents and diagrams open the matching page here instead of a dead path.
export function Markdown({ source, basePath }: { source: string; basePath: string }) {
  const { useCases } = useProject()
  return (
    <div className="prose-doc">
      <ReactMarkdown
        skipHtml
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href = "", children }) {
            if (href.startsWith("#")) return <a href={href}>{children}</a>
            if (EXTERNAL.test(href)) return <a href={href} target="_blank" rel="noreferrer noopener">{children}</a>
            const target = resolve(basePath, href)
            const uc = useCases.find((u) => u.path === target)
            if (uc) return <Link to={`/use-cases/${uc.id}`}>{children}</Link>
            if (target.endsWith(".puml")) return <Link to={`/diagrams?path=${encodeURIComponent(target)}`}>{children}</Link>
            if (target.endsWith(".md")) return <Link to={`/docs?path=${encodeURIComponent(target)}`}>{children}</Link>
            return <span>{children}</span>
          },
          code({ className, children, ...props }) {
            if (/language-mermaid/.test(className ?? "")) return <Mermaid source={String(children).trim()} />
            return (
              <code className={className} {...props}>
                {children}
              </code>
            )
          },
          pre({ children }) {
            // A mermaid fence has already become a figure; do not wrap it in a code block.
            const only = Array.isArray(children) ? children[0] : children
            const isMermaid = typeof only === "object" && only !== null && "type" in only && only.type === Mermaid
            return isMermaid ? <>{children}</> : <pre>{children}</pre>
          },
        }}
      >
        {label(source)}
      </ReactMarkdown>
    </div>
  )
}
