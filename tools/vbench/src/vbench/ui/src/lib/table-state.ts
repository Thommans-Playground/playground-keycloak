// A table's search, filters, sort and page, kept in the URL so a filtered view can be linked to and survives a
// refresh. A prefix keeps two tables on one page apart; parameters that are not the table's are left alone.

export interface TableState {
  q: string
  filters: Record<string, string[]>
  sort: { id: string; desc: boolean } | null
  page: number // 1-based
}

export const emptyState: TableState = { q: "", filters: {}, sort: null, page: 1 }

export function readTableState(params: URLSearchParams, prefix: string, filterIds: string[]): TableState {
  const filters: Record<string, string[]> = {}
  for (const id of filterIds) {
    const raw = params.get(`${prefix}f.${id}`)
    if (raw) filters[id] = raw.split(",").filter(Boolean)
  }
  const sort = params.get(`${prefix}sort`)
  const page = Number.parseInt(params.get(`${prefix}page`) ?? "1", 10)
  return {
    q: params.get(`${prefix}q`) ?? "",
    filters,
    sort: sort ? { id: sort.replace(/^-/, ""), desc: sort.startsWith("-") } : null,
    page: Number.isFinite(page) && page > 0 ? page : 1,
  }
}

export function writeTableState(params: URLSearchParams, prefix: string, filterIds: string[], state: TableState): URLSearchParams {
  const next = new URLSearchParams(params)
  const set = (key: string, value: string | null) => (value ? next.set(`${prefix}${key}`, value) : next.delete(`${prefix}${key}`))
  set("q", state.q || null)
  set("sort", state.sort ? `${state.sort.desc ? "-" : ""}${state.sort.id}` : null)
  set("page", state.page > 1 ? String(state.page) : null)
  for (const id of filterIds) set(`f.${id}`, state.filters[id]?.length ? state.filters[id].join(",") : null)
  return next
}

export const hasActiveFilters = (s: TableState) => Boolean(s.q) || Object.values(s.filters).some((v) => v.length > 0)
