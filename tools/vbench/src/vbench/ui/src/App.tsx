import { lazy, Suspense } from "react"
import { BrowserRouter, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/AppShell"
import { Skeleton } from "@/components/ui/skeleton"
import Overview from "@/pages/Overview"
import UseCaseDetail from "@/pages/UseCaseDetail"
import UseCases from "@/pages/UseCases"

// The heavier pages (they pull in Mermaid or the diagram viewer) load when first opened.
const BuildOrder = lazy(() => import("@/pages/BuildOrder"))
const Traceability = lazy(() => import("@/pages/Traceability"))
const Diagrams = lazy(() => import("@/pages/Diagrams"))
const Docs = lazy(() => import("@/pages/Docs"))
const SettingsPage = lazy(() => import("@/pages/SettingsPage"))
const Phase = lazy(() => import("@/pages/Phase"))
const VItemPage = lazy(() => import("@/pages/VItemPage"))

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Skeleton className="m-8 h-64" />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Overview />} />
            <Route path="v/:phase" element={<Phase />} />
            <Route path="v/:phase/:item" element={<VItemPage />} />
            <Route path="use-cases" element={<UseCases />} />
            <Route path="use-cases/:id" element={<UseCaseDetail />} />
            <Route path="build-order" element={<BuildOrder />} />
            <Route path="traceability" element={<Traceability />} />
            <Route path="diagrams" element={<Diagrams />} />
            <Route path="docs" element={<Docs />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Overview />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
