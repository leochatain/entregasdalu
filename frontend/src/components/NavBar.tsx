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
    <nav className="border-line-warm fixed inset-x-0 top-0 z-50 flex h-[60px] items-center gap-5 overflow-x-auto border-b bg-[rgba(250,250,250,0.9)] px-[22px] backdrop-blur-[8px]">
      <button
        type="button"
        onClick={() => onNavigate?.('today')}
        aria-label="entregas da lu — início"
        className="text-ink font-display focus-visible:outline-accent mr-1 cursor-pointer text-[32px] leading-none whitespace-nowrap italic focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        entregas da <span className="text-accent">lu</span>
      </button>
      {ITEMS.map(({ view, label }) => {
        const isActive = active === view
        return (
          <button
            key={view}
            type="button"
            aria-current={isActive ? 'page' : undefined}
            onClick={() => onNavigate?.(view)}
            className={`focus-visible:outline-accent cursor-pointer border-b-2 font-mono text-[13px] tracking-[.16em] whitespace-nowrap uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 ${
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
        className="text-muted-2 hover:text-ink focus-visible:outline-accent ml-auto cursor-pointer font-mono text-[13px] tracking-[.16em] whitespace-nowrap uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        sair
      </button>
    </nav>
  )
}
