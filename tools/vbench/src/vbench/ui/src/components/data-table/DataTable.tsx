import { useMemo } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import {
  flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, useReactTable,
  type ColumnDef, type FilterFn, type Row, type SortingState,
} from "@tanstack/react-table"
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, ChevronsUpDown, Search, X } from "lucide-react"

import { FacetFilter } from "@/components/data-table/FacetFilter"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { emptyState, hasActiveFilters, readTableState, writeTableState, type TableState } from "@/lib/table-state"
import { cn } from "@/lib/utils"

declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  interface ColumnMeta<TData, TValue> {
    facet?: string // a filter label: the column becomes a multi-select filter
    optionLabel?: (value: string) => string // the word shown for a value in the filter
    className?: string
  }
}

const PAGE_SIZES = [10, 25, 50]

// A facet matches when the row's value (or any of its values, for a list) is one of the chosen ones.
const facetFilter: FilterFn<unknown> = (row, id, chosen: string[]) => {
  if (!chosen?.length) return true
  const value = row.getValue(id)
  return (Array.isArray(value) ? value : [value]).some((v) => chosen.includes(String(v)))
}
facetFilter.autoRemove = (v: string[]) => !v?.length

const searchFilter: FilterFn<unknown> = (row, _id, q: string) =>
  row
    .getAllCells()
    .map((c) => c.getValue())
    .join(" ")
    .toLowerCase()
    .includes(q.toLowerCase())

const valuesOf = (v: unknown): string[] => (Array.isArray(v) ? v.map(String) : v == null || v === "" ? [] : [String(v)])

/**
 * A real table: sortable columns, a search box, multi-select filters for the columns that opt in (`meta.facet`),
 * and pagination. Its search, filters, sort and page live in the URL (under `urlPrefix`), so a filtered view can be
 * linked to, and a card elsewhere can send you here with a filter already set.
 */
export function DataTable<T>({ data, columns, noun, rowHref, urlPrefix = "", initialSort, searchPlaceholder, empty }: {
  data: T[]
  columns: ColumnDef<T, any>[] // eslint-disable-line @typescript-eslint/no-explicit-any
  noun: string // "use case", "test": what a row is
  rowHref?: (row: T) => string
  urlPrefix?: string
  initialSort?: { id: string; desc?: boolean }
  searchPlaceholder?: string
  empty?: React.ReactNode
}) {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const facetIds = useMemo(() => columns.filter((c) => c.meta?.facet).map((c) => String(c.id ?? (c as { accessorKey?: string }).accessorKey)), [columns])
  // Everything handed to the table is memoised on the URL, so its identity changes only when the URL does. A fresh
  // array on every render makes TanStack recompute, queue its automatic page reset and render again, without end.
  const urlKey = params.toString()
  const state: TableState = useMemo(() => readTableState(params, urlPrefix, facetIds), [urlKey, urlPrefix, facetIds]) // eslint-disable-line react-hooks/exhaustive-deps
  const sort = state.sort ?? (initialSort ? { id: initialSort.id, desc: Boolean(initialSort.desc) } : null)
  const pageSize = Number(params.get(`${urlPrefix}size`)) || PAGE_SIZES[0]
  const sorting = useMemo<SortingState>(() => (sort ? [{ id: sort.id, desc: sort.desc }] : []), [sort?.id, sort?.desc]) // eslint-disable-line react-hooks/exhaustive-deps
  const columnFilters = useMemo(() => Object.entries(state.filters).map(([id, value]) => ({ id, value })), [state.filters])
  const pagination = useMemo(() => ({ pageIndex: state.page - 1, pageSize }), [state.page, pageSize])
  const columnDefs = useMemo(() => columns.map((c) => (c.meta?.facet ? { ...c, filterFn: facetFilter as FilterFn<T> } : c)), [columns])

  const update = (patch: Partial<TableState>, resetPage = true) =>
    setParams(writeTableState(params, urlPrefix, facetIds, { ...state, ...patch, page: resetPage ? 1 : (patch.page ?? state.page) }), { replace: true })

  const table = useReactTable<T>({
    data,
    columns: columnDefs,
    state: { sorting, columnFilters, globalFilter: state.q, pagination },
    autoResetPageIndex: false, // the URL owns the page; a reset here would only set state we do not use
    onPaginationChange: () => {}, // likewise: page changes go through the URL
    globalFilterFn: searchFilter as FilterFn<T>,
    onSortingChange: (u) => {
      const next = (typeof u === "function" ? u(sorting) : u)[0]
      update({ sort: next ? { id: next.id, desc: next.desc } : null })
    },
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    enableSortingRemoval: true,
  })

  const rows = table.getRowModel().rows
  const total = table.getPreFilteredRowModel().rows.length
  const matched = table.getFilteredRowModel().rows.length
  const pages = Math.max(1, Math.ceil(matched / pageSize))
  const page = Math.min(state.page, pages)
  const from = matched === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, matched)
  const active = hasActiveFilters(state)

  const facets = table.getAllLeafColumns().filter((c) => c.columnDef.meta?.facet)
  const options = (colId: string) => {
    const counts = new Map<string, number>()
    for (const r of table.getPreFilteredRowModel().rows) for (const v of valuesOf(r.getValue(colId))) counts.set(v, (counts.get(v) ?? 0) + 1)
    const label = table.getColumn(colId)?.columnDef.meta?.optionLabel ?? ((v: string) => v)
    return [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], undefined, { numeric: true })).map(([value, count]) => ({ value, label: label(value), count }))
  }

  const open = (row: Row<T>) => rowHref && navigate(rowHref(row.original))

  if (total === 0) return <>{empty ?? <p className="text-sm text-muted-foreground">There are no {noun}s yet.</p>}</>

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 border-b border-divider bg-surface-2 px-3 py-3">
        <label className="relative min-w-52 flex-1 sm:max-w-xs">
          <span className="sr-only">Search the {noun}s</span>
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-subtle" aria-hidden="true" />
          <input
            type="search"
            value={state.q}
            onChange={(e) => update({ q: e.target.value })}
            placeholder={searchPlaceholder ?? `Search ${noun}s`}
            className="min-h-9 w-full rounded-control border border-input bg-surface pl-8 pr-3 text-[13px] text-ink placeholder:text-subtle focus:border-ink focus:outline-none focus:ring-3 focus:ring-ink/10"
          />
        </label>
        {facets.map((c) => (
          <FacetFilter key={c.id} label={c.columnDef.meta!.facet!} options={options(c.id)} selected={state.filters[c.id] ?? []}
            onChange={(next) => update({ filters: { ...state.filters, [c.id]: next } })} />
        ))}
        {active && (
          <button type="button" onClick={() => update({ ...emptyState, sort: state.sort })} className="inline-flex min-h-9 items-center gap-1 rounded-control px-2 text-[13px] font-medium text-link hover:bg-hover">
            <X className="size-3.5" aria-hidden="true" /> Clear filters
          </button>
        )}
        <p className="ml-auto text-xs text-muted-foreground" aria-live="polite">
          {active ? `${matched} of ${total}` : total} {noun}{total === 1 ? "" : "s"}
        </p>
      </div>

      <Table aria-label={`The ${noun}s`}>
        <TableHeader>
          {table.getHeaderGroups().map((g) => (
            <TableRow key={g.id} className="hover:bg-transparent">
              {g.headers.map((h) => {
                const dir = h.column.getIsSorted()
                return (
                  <TableHead key={h.id} aria-sort={dir === "asc" ? "ascending" : dir === "desc" ? "descending" : undefined} className={h.column.columnDef.meta?.className}>
                    {h.isPlaceholder ? null : h.column.getCanSort() ? (
                      <button type="button" onClick={h.column.getToggleSortingHandler()} className="inline-flex min-h-8 items-center gap-1 font-semibold hover:text-ink">
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {dir === "asc" ? <ArrowUp className="size-3.5" aria-hidden="true" /> : dir === "desc" ? <ArrowDown className="size-3.5" aria-hidden="true" /> : <ChevronsUpDown className="size-3.5 text-subtle" aria-hidden="true" />}
                      </button>
                    ) : flexRender(h.column.columnDef.header, h.getContext())}
                  </TableHead>
                )
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={columns.length} className="py-10 text-center text-sm text-muted-foreground">
                No {noun}s match. <button type="button" onClick={() => update(emptyState)} className="font-medium text-link hover:underline">Clear the filters</button>
              </TableCell>
            </TableRow>
          ) : rows.map((row) => (
            <TableRow key={row.id} onClick={rowHref ? () => open(row) : undefined} className={cn(rowHref && "cursor-pointer")}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id} className={cell.column.columnDef.meta?.className}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {matched > PAGE_SIZES[0] || pageSize !== PAGE_SIZES[0] ? (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-divider bg-surface-2 px-3 py-2.5 text-[13px] text-muted-foreground">
          <p>Showing {from} to {to} of {matched}</p>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5">
              Rows
              <select value={pageSize} onChange={(e) => setParams(writeSize(params, urlPrefix, Number(e.target.value), state, facetIds), { replace: true })}
                className="min-h-9 rounded-control border border-input bg-surface px-2 text-[13px] text-ink">
                {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
            <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => update({ page: page - 1 }, false)} aria-label="Previous page"><ChevronLeft aria-hidden="true" /></Button>
            <span className="min-w-16 text-center font-mono text-xs">{page} / {pages}</span>
            <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => update({ page: page + 1 }, false)} aria-label="Next page"><ChevronRight aria-hidden="true" /></Button>
          </div>
        </div>
      ) : null}
    </Card>
  )
}

function writeSize(params: URLSearchParams, prefix: string, size: number, state: TableState, facetIds: string[]): URLSearchParams {
  const next = writeTableState(params, prefix, facetIds, { ...state, page: 1 })
  if (size === PAGE_SIZES[0]) next.delete(`${prefix}size`)
  else next.set(`${prefix}size`, String(size))
  return next
}
