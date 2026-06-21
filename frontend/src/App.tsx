import { useState } from 'react'
import { ApiError } from './api/client'
import {
  useAdvanceDay,
  useConfig,
  useResetDb,
  useToday,
  type FrozenEntry,
} from './api/hooks'
import NavBar, { type NavView } from './components/NavBar'
import Editor from './screens/Editor'
import Gallery from './screens/Gallery'
import JaEntregue from './screens/JaEntregue'
import Menu from './screens/Menu'
import Reveal from './screens/Reveal'
import SignIn from './screens/SignIn'
import Stats from './screens/Stats'

/**
 * Resume-first routing (frontend.md §5): GET /api/today returns the day state and
 * a single switch picks the screen — no react-router in v1. Gallery/Stats are nav
 * overlays; Reveal is a transient post-submit outcome (reload → JáEntregue).
 */
export default function App() {
  const today = useToday()
  const config = useConfig()
  const advanceDay = useAdvanceDay()
  const resetDb = useResetDb()
  const [view, setView] = useState<NavView>('today')
  const [reveal, setReveal] = useState<FrozenEntry | null>(null)

  const isAuthError =
    today.error instanceof ApiError &&
    (today.error.status === 401 || today.error.status === 403)
  if (isAuthError) return <SignIn />

  if (today.isLoading) return <Splash>carregando…</Splash>
  if (today.isError || !today.data)
    return <Splash>algo deu errado. recarregue a página.</Splash>

  const data = today.data

  return (
    <div className="min-h-screen pt-[60px]">
      <NavBar
        active={view}
        onNavigate={setView}
        onSignOut={() => {
          window.location.href = '/accounts/logout/'
        }}
        showDev={!!config.data?.devLogin}
        onAdvanceDay={() => advanceDay.mutate()}
        onResetDb={() => resetDb.mutate()}
      />
      {view === 'gallery' ? (
        <Gallery />
      ) : view === 'stats' ? (
        <Stats />
      ) : reveal ? (
        <Reveal
          entry={reveal}
          onDone={() => {
            setReveal(null)
            setView('gallery')
          }}
        />
      ) : data.state === 'picked' && data.picked ? (
        <Editor picked={data.picked} onReveal={setReveal} />
      ) : data.state === 'submitted' && data.submitted ? (
        <JaEntregue entry={data.submitted} />
      ) : (
        <Menu offer={data.offer ?? []} today={data.today} />
      )}
    </div>
  )
}

function Splash({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <p className="text-muted-2 font-mono text-[13px] tracking-[.16em] uppercase">
        {children}
      </p>
    </main>
  )
}
