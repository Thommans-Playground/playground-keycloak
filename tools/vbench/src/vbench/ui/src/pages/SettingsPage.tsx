import { Monitor, Moon, Sun } from "lucide-react"

import { PageHeader } from "@/components/PageHeader"
import { Segmented } from "@/components/Segmented"
import { Card } from "@/components/ui/card"
import { useDisplayName } from "@/lib/profile"
import { THEMES, useTheme, type Theme } from "@/lib/theme"

const WORD: Record<Theme, string> = { light: "Light", dark: "Dark", system: "System" }
const ICON: Record<Theme, React.ReactNode> = {
  light: <Sun className="size-3.5" aria-hidden="true" />,
  dark: <Moon className="size-3.5" aria-hidden="true" />,
  system: <Monitor className="size-3.5" aria-hidden="true" />,
}

function Row({ title, hint, children }: { title: string; hint: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-divider px-6 py-4 last:border-0">
      <div className="min-w-0 max-w-md">
        <p className="t-headline text-ink">{title}</p>
        <p className="t-footnote mt-0.5 text-muted-foreground">{hint}</p>
      </div>
      {children}
    </div>
  )
}

export default function SettingsPage() {
  const [theme, setTheme] = useTheme()
  const [name, setName] = useDisplayName()
  return (
    <>
      <PageHeader title="Settings" crumbs={[{ label: "Settings" }]} description="These are kept in this browser only. The dashboard itself never changes the project." />
      <div className="space-y-8">
        <section aria-labelledby="appearance-h">
          <h2 id="appearance-h" className="t-title mb-3 text-ink">Appearance</h2>
          <Card>
            <Row title="Theme" hint="Light is the default. System follows your device and changes with it.">
              <Segmented
                label="Theme" value={theme} onChange={setTheme}
                segments={THEMES.map((t) => ({ key: t, label: WORD[t], icon: ICON[t] }))}
              />
            </Row>
          </Card>
        </section>
        <section aria-labelledby="profile-h">
          <h2 id="profile-h" className="t-title mb-3 text-ink">Profile</h2>
          <Card>
            <Row title="Your name" hint="Shown on the profile button. There are no accounts; this is only a label.">
              <label className="block">
                <span className="sr-only">Your name</span>
                <input
                  type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Add your name" maxLength={60} autoComplete="name"
                  className="min-h-11 w-64 rounded-control border border-input bg-surface px-3 text-[15px] placeholder:text-subtle"
                />
              </label>
            </Row>
          </Card>
        </section>
      </div>
    </>
  )
}
