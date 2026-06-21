import type { FrozenEntry } from '../api/hooks'
import CtaButton from '../components/CtaButton'
import EntryChips from '../components/EntryChips'
import Eyebrow from '../components/Eyebrow'
import Mosaic from '../components/Mosaic'
import { percentLabel } from '../lib/format'

/**
 * Post-submit celebration (transient). Animates the frozen tile list in reveal
 * order. A reload resolves to JáEntregue instead (App drops `reveal`).
 */
export default function Reveal({
  entry,
  onDone,
}: {
  entry: FrozenEntry
  onDone: () => void
}) {
  return (
    <main className="mx-auto flex max-w-[560px] flex-col items-center gap-6 px-6 py-14 text-center">
      <Eyebrow className="tracking-[.3em]">entrega feita</Eyebrow>
      <h1 className="text-screen-h1 text-ink font-serif font-medium">
        Entrega de hoje
      </h1>

      <div className="w-[480px] max-w-full">
        <Mosaic
          photoUrl={entry.photoUrl}
          litTiles={entry.revealedTiles}
          animate
        />
      </div>

      <p className="text-accent font-serif text-[34px] font-medium">
        {percentLabel(entry.performancePct)} revelado
      </p>

      <EntryChips entry={entry} />

      <CtaButton onClick={onDone}>Ver na galeria →</CtaButton>
    </main>
  )
}
