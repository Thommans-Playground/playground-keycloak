import { Children, isValidElement, type ReactNode } from "react"

/** The words in some React content, so a card's header can be quoted to the assistant as text. */
export function textOf(node: ReactNode): string {
  if (node === null || node === undefined || typeof node === "boolean") return ""
  if (typeof node === "string" || typeof node === "number") return String(node)
  if (Array.isArray(node)) return Children.toArray(node).map(textOf).filter(Boolean).join(" ")
  if (isValidElement<{ children?: ReactNode }>(node)) return textOf(node.props.children)
  return ""
}
