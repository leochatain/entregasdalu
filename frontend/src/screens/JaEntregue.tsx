import type { FrozenEntry } from '../api/hooks'
import EntryChips from '../components/EntryChips'
import Eyebrow from '../components/Eyebrow'
import Mosaic from '../components/Mosaic'

/** The persistent `submitted` resume screen — frozen mosaic, no animation. */
export default function JaEntregue({ entry }: { entry: FrozenEntry }) {
  return (
    <main className="mx-auto flex max-w-[560px] flex-col items-center gap-6 px-6 py-14 text-center">
      <Eyebrow className="tracking-[.3em]">resumo de hoje</Eyebrow>
      <h1 className="text-screen-h1 text-ink font-serif font-medium">
        Você já entregou hoje.
      </h1>

      <div className="w-[480px] max-w-full">
        <Mosaic photoUrl={entry.photoUrl} litTiles={entry.revealedTiles} />
      </div>

      <EntryChips entry={entry} />
    </main>
  )
}
