/**
 * pt-BR formatting helpers (frontend.md §2). Pure functions over primitives — no
 * backend dependency. Calendar dates are `YYYY-MM-DD` strings (the DailyEntry PK)
 * and render in America/São_Paulo.
 */

const TZ = 'America/Sao_Paulo'

export function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n))
}

/**
 * Word count for the live editor counter. Mirrors the backend's `len(text.split())`
 * (split on any whitespace, drop empties). The authoritative count still comes from
 * the server at submit — this only drives the in-progress display.
 */
export function countWords(text: string): number {
  const trimmed = text.trim()
  return trimmed ? trimmed.split(/\s+/).length : 0
}

/** Fraction revealed, 0..1 — `p = min(1, words / target)`. */
export function progress(words: number, target: number): number {
  return target > 0 ? clamp01(words / target) : 0
}

/** pt-BR integer with thousands separators: 9480 → "9.480". */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat('pt-BR').format(n)
}

/** Editor counter: "240 / 400 palavras". */
export function countLabel(words: number, target: number): string {
  return `${formatNumber(words)} / ${formatNumber(target)} palavras`
}

/** A 0..1 fraction as a rounded percent label: 0.62 → "62%". */
export function percentLabel(fraction: number): string {
  return `${Math.round(clamp01(fraction) * 100)}%`
}

function parseCalendarDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  // Noon UTC so São Paulo formatting can never roll to an adjacent calendar day.
  return new Date(Date.UTC(y, m - 1, d, 12))
}

// pt-BR Intl returns trailing dots on short forms ("sex.", "jun.") — strip them.
function trimDot(s: string): string {
  return s.replace(/\.$/, '')
}

function part(date: Date, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat('pt-BR', { ...options, timeZone: TZ }).format(
    date,
  )
}

/** Chip / short form: "sex · 20 jun". */
export function formatShortDate(iso: string): string {
  const date = parseCalendarDate(iso)
  const weekday = trimDot(part(date, { weekday: 'short' }))
  const day = part(date, { day: 'numeric' })
  const month = trimDot(part(date, { month: 'short' }))
  return `${weekday} · ${day} ${month}`
}

/** Menu eyebrow / long form: "sexta · 20 de junho". */
export function formatLongDate(iso: string): string {
  const date = parseCalendarDate(iso)
  const weekday = part(date, { weekday: 'long' }).replace(/-feira$/, '')
  const day = part(date, { day: 'numeric' })
  const month = part(date, { month: 'long' })
  return `${weekday} · ${day} de ${month}`
}

/** Today's São Paulo calendar date as YYYY-MM-DD (en-CA renders ISO order). */
export function todayISO(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

/** Month name for a year + 1-based month: (2026, 6) → "junho". */
export function formatMonthName(year: number, month: number): string {
  return part(new Date(Date.UTC(year, month - 1, 1, 12)), { month: 'long' })
}
