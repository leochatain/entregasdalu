import { useEffect, useState } from 'react'
import { useGallery, type FrozenEntry } from '../api/hooks'
import CtaButton from '../components/CtaButton'
import Eyebrow from '../components/Eyebrow'
import Mosaic from '../components/Mosaic'
import { formatShortDate, percentLabel } from '../lib/format'

/** Trophy wall: every frozen entry, click to enlarge. */
export default function Gallery() {
  const { data, isLoading } = useGallery()
  const [open, setOpen] = useState<FrozenEntry | null>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(null)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  const acervo =
    data && data.poolTotal > 0 ? data.photosCollected / data.poolTotal : 0

  return (
    <main className="mx-auto max-w-[1080px] px-6 py-14">
      <Eyebrow>diário de esforço</Eyebrow>
      <h1 className="text-screen-h1 text-ink mt-3 font-serif font-medium">
        Galeria
      </h1>
      {data && (
        <p className="text-muted mt-2 font-mono text-[15px]">
          {data.photosCollected} fotos · {percentLabel(acervo)} do acervo
        </p>
      )}

      {isLoading ? (
        <p className="text-muted-2 mt-10 font-mono text-[15px]">carregando…</p>
      ) : !data || data.items.length === 0 ? (
        <p className="text-muted-2 mt-10 font-serif text-[18px] italic">
          ainda nada por aqui. a primeira entrega começa a galeria.
        </p>
      ) : (
        <div className="mt-10 grid grid-cols-[repeat(auto-fill,minmax(188px,1fr))] gap-5">
          {data.items.map((entry) => (
            <button
              key={entry.date}
              type="button"
              onClick={() => setOpen(entry)}
              className="focus-visible:outline-accent flex cursor-pointer flex-col gap-2 transition-transform duration-200 hover:-translate-y-0.5 focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              <Mosaic
                photoUrl={entry.photoUrl}
                litTiles={entry.revealedTiles}
              />
              <div className="flex items-baseline justify-between">
                <span className="text-muted-2 font-mono text-[13px]">
                  {formatShortDate(entry.date)}
                </span>
                <span className="text-accent font-mono text-[13px]">
                  {percentLabel(entry.performancePct)}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && (
        <div
          role="dialog"
          aria-modal
          aria-label={`entrega de ${formatShortDate(open.date)}`}
          className="animate-edlrise fixed inset-0 z-[120] flex items-center justify-center p-10"
        >
          {/* Click-out: a real button so it's keyboard-reachable (Esc also closes). */}
          <button
            type="button"
            aria-label="fechar"
            onClick={() => setOpen(null)}
            className="absolute inset-0 cursor-default bg-[rgba(26,22,19,0.72)] backdrop-blur-[4px]"
          />
          <div className="relative z-10 w-[340px] max-w-full">
            <Mosaic photoUrl={open.photoUrl} litTiles={open.revealedTiles} />
            <p className="text-bg mt-4 text-center font-serif text-[20px]">
              {open.name} · {percentLabel(open.performancePct)}
            </p>
            <p className="mt-1 text-center font-mono text-[14px] text-[#c9c4bf]">
              {formatShortDate(open.date)} · {open.effectiveWordCount} palavras
            </p>
            <CtaButton
              onClick={() => setOpen(null)}
              className="bg-bg text-ink mt-5 w-full"
            >
              fechar
            </CtaButton>
          </div>
        </div>
      )}
    </main>
  )
}
