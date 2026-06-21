import { useState } from 'react'
import { usePick, type OfferSlot } from '../api/hooks'
import CtaButton from '../components/CtaButton'
import Eyebrow from '../components/Eyebrow'
import TierCard from '../components/TierCard'
import { formatLongDate, todayISO } from '../lib/format'

/** Tier tag per tier id (not in the offer payload; a UI constant). */
const TAGS: Record<string, string> = {
  rascunho: 'leve',
  capitulo: 'o de sempre',
  tese: 'corajosa',
}

/** Today's offer → pick a tier → pin it (POST /api/pick) → resume routes to Editor. */
export default function Menu({ offer }: { offer: (OfferSlot | null)[] }) {
  const slots = offer.filter((s): s is OfferSlot => s != null)
  const pick = usePick()
  const [selected, setSelected] = useState<string | null>(
    slots[0]?.tier ?? null,
  )

  return (
    <main className="mx-auto flex max-w-[1020px] flex-col px-7 py-14">
      <Eyebrow>{formatLongDate(todayISO())}</Eyebrow>
      <h1 className="text-screen-h1 text-ink mt-3 mb-2 font-serif font-medium">
        Escolha o desafio do dia
      </h1>
      <p className="text-muted mb-11 max-w-[50ch] font-serif text-[18px] italic">
        Escreva o número de palavras do desafio e a foto se revela inteira.
        Escreveu menos? Você fica com o pedaço que conquistou.
      </p>

      {slots.length === 0 ? (
        <p className="text-muted-2 font-serif text-[18px] italic">
          sem foto hoje — volte amanhã.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-[22px] sm:grid-cols-3">
            {slots.map((slot) => (
              <TierCard
                key={slot.tier}
                name={slot.name}
                tag={TAGS[slot.tier] ?? ''}
                wordTarget={slot.wordTarget}
                photoUrl={slot.photoUrl}
                seedTile={slot.seedTile}
                selected={slot.tier === selected}
                onSelect={() => setSelected(slot.tier)}
              />
            ))}
          </div>

          <div className="mt-11 flex flex-wrap items-center gap-6">
            <CtaButton
              onClick={() => selected && pick.mutate(selected)}
              disabled={!selected || pick.isPending}
            >
              Escolher este desafio →
            </CtaButton>
            <span className="text-muted-2 font-serif text-[15px] italic">
              a foto fica em segredo até você entregar.
            </span>
          </div>
        </>
      )}
    </main>
  )
}
