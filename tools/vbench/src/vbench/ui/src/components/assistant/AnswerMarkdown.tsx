import { Link } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

const EXTERNAL = /^[a-z][a-z0-9+.-]*:/i

// An answer as light markdown, with no raw HTML. A link that starts with `/` is a page of this dashboard; anything else
// that is not a web address is shown as text, so a made-up path is never a dead link.
export function AnswerMarkdown({ source }: { source: string }) {
  return (
    <div className="prose-doc prose-chat">
      <ReactMarkdown
        skipHtml
        remarkPlugins={[remarkGfm]}
        components={{
          a({ href = "", children }) {
            if (EXTERNAL.test(href)) return <a href={href} target="_blank" rel="noreferrer noopener">{children}</a>
            if (href.startsWith("/")) return <Link to={href}>{children}</Link>
            return <span>{children}</span>
          },
        }}
      >
        {source}
      </ReactMarkdown>
    </div>
  )
}
