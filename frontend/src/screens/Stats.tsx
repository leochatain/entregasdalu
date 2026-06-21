import { useStats } from '../api/hooks'
import Eyebrow from '../components/Eyebrow'
import { formatMonthName, formatNumber } from '../lib/format'

const WEEKDAYS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']

/** Calendar heatmap + the aggregate stat cards. */
export default function Stats() {
  const { data } = useStats()

  if (!data) {
    return (
      <main className="mx-auto max-w-[920px] px-6 py-14">
        <p className="text-muted-2 font-mono text-[15px]">carregando…</p>
      </main>
    )
  }

  const cards = [
    { num: formatNumber(data.currentStreak), label: 'sequência atual' },
    { num: formatNumber(data.longestStreak), label: 'maior sequência' },
    { num: formatNumber(data.totalWords), label: 'palavras escritas' },
    { num: formatNumber(data.daysDelivered), label: 'entregas' },
    { num: formatNumber(data.photosCollected), label: 'fotos coletadas' },
  ]

  const pctByDate = new Map(
    data.calendar.map((d) => [d.date, d.performancePct]),
  )
  const today = data.today
  const pad = (n: number) => String(n).padStart(2, '0')

  return (
    <main className="mx-auto max-w-[920px] px-6 py-14">
      <Eyebrow>o ano de {data.year}</Eyebrow>
      <h1 className="text-screen-h1 text-ink mt-3 font-serif font-medium capitalize">
        {formatMonthName(data.year, data.month)}
      </h1>

      <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-5">
        {cards.map((c) => (
          <div
            key={c.label}
            className="border-line flex flex-col items-center gap-2 rounded-[6px] border p-5 text-center"
          >
            <span className="text-ink font-serif text-[32px] font-medium">
              {c.num}
            </span>
            <span className="text-muted-2 font-mono text-[13px] tracking-[.08em] uppercase">
              {c.label}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-12 grid grid-cols-7 gap-2">
        {WEEKDAYS.map((w) => (
          <div
            key={w}
            className="text-faint text-center font-mono text-[12px] tracking-[.1em] uppercase"
          >
            {w}
          </div>
        ))}

        {Array.from({ length: data.firstWeekday }, (_, i) => (
          <div key={`blank-${i}`} />
        ))}

        {Array.from({ length: data.daysInMonth }, (_, i) => {
          const day = i + 1
          const iso = `${data.year}-${pad(data.month)}-${pad(day)}`
          const pct = pctByDate.get(iso)
          const isToday = iso === today
          const future = iso > today

          let style: React.CSSProperties
          if (pct !== undefined && pct > 0) {
            style = {
              background: `rgba(26,26,26,${(0.1 + pct * 0.8).toFixed(3)})`,
              color: pct > 0.5 ? '#fafafa' : '#2a2a28',
            }
          } else if (future) {
            style = { color: '#a6a6a0', border: '1px solid #e4e4e0' }
          } else {
            style = { color: '#909089', border: '1px dashed #d2d2cc' }
          }
          if (isToday) style.boxShadow = '0 0 0 2px #1a1a1a'

          return (
            <div
              key={iso}
              style={style}
              className="flex aspect-square items-start justify-end rounded-[4px] p-1.5 font-mono text-[13px]"
            >
              {day}
            </div>
          )
        })}
      </div>

      <div className="text-muted-2 mt-6 flex items-center gap-2 font-mono text-[13px]">
        menos
        <span className="bg-line h-3 w-3 rounded-[3px]" />
        <span className="h-3 w-3 rounded-[3px] bg-[rgba(26,26,26,0.4)]" />
        <span className="h-3 w-3 rounded-[3px] bg-[rgba(26,26,26,0.9)]" />
        mais revelado
      </div>
    </main>
  )
}
