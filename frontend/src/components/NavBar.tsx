/**
 * Fixed top nav (frontend.md §7). Production collapses the prototype's 9-item demo
 * bar to Hoje · Galeria · Calendário + sign-out; active item gets a red underline.
 *
 * Presentational shell: it takes the active view + callbacks as props. The real
 * wiring to the App state machine (frontend.md §5) lands later — handlers are
 * optional so it renders standalone in the meantime.
 */
export type NavView = 'today' | 'gallery' | 'stats'

interface NavBarProps {
  active?: NavView
  onNavigate?: (view: NavView) => void
  onSignOut?: () => void
}

const ITEMS: { view: NavView; label: string }[] = [
  { view: 'today', label: 'Hoje' },
  { view: 'gallery', label: 'Galeria' },
  { view: 'stats', label: 'Calendário' },
]

export default function NavBar({ active, onNavigate, onSignOut }: NavBarProps) {
  return (
    <nav className="border-line-warm fixed inset-x-0 top-0 z-50 flex h-[46px] items-center gap-4 overflow-x-auto border-b bg-[rgba(250,250,250,0.9)] px-[22px] backdrop-blur-[8px]">
      <span className="text-accent font-mono text-[11px] font-bold tracking-[.22em] whitespace-nowrap uppercase">
        e/dl
      </span>
      {ITEMS.map(({ view, label }) => {
        const isActive = active === view
        return (
          <button
            key={view}
            type="button"
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onNavigate?.(view)}
            className={`focus-visible:outline-accent cursor-pointer border-b-2 font-mono text-[11px] tracking-[.16em] whitespace-nowrap uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 ${
              isActive
                ? 'text-accent border-accent'
                : 'text-muted hover:text-ink border-transparent'
            }`}
          >
            {label}
          </button>
        )
      })}
      <button
        type="button"
        onClick={onSignOut}
        className="text-muted-2 hover:text-ink focus-visible:outline-accent ml-auto cursor-pointer font-mono text-[11px] tracking-[.16em] whitespace-nowrap uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        sair
      </button>
    </nav>
  )
}
