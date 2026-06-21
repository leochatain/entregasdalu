import { useState } from 'react'
import { useSubmit, type FrozenEntry, type Picked } from '../api/hooks'
import CtaButton from '../components/CtaButton'
import Eyebrow from '../components/Eyebrow'
import Mosaic from '../components/Mosaic'
import ProgressBar from '../components/ProgressBar'
import { countLabel, countWords, progress } from '../lib/format'

/**
 * Write/paste the day's text → POST /api/submit freezes the reveal. `onReveal`
 * hands the frozen entry up so App can show the (transient) Reveal celebration.
 */
export default function Editor({
  picked,
  onReveal,
}: {
  picked: Picked
  onReveal: (entry: FrozenEntry) => void
}) {
  const [text, setText] = useState('')
  const submit = useSubmit()
  const words = countWords(text)
  const p = progress(words, picked.wordTarget)

  return (
    <main className="mx-auto flex max-w-[1080px] flex-wrap items-start gap-11 px-6 py-10">
      <div className="min-w-[300px] flex-1 basis-[380px]">
        <div className="mb-2 flex items-baseline justify-between gap-4">
          <h1 className="text-ink font-serif text-[30px] font-medium">
            {picked.name}
          </h1>
          <span aria-live="polite" className="text-muted font-mono text-[15px]">
            {countLabel(words, picked.wordTarget)}
          </span>
        </div>
        <div className="mb-7">
          <ProgressBar value={p} />
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Cole ou escreva aqui…"
          className="text-editor text-ink bg-surface min-h-[48vh] w-full resize-y rounded-[4px] p-[30px] font-serif shadow-[inset_0_0_0_1px_var(--color-line)] outline-none"
        />

        <div className="mt-7">
          <CtaButton
            className="px-8"
            onClick={() => submit.mutate(text, { onSuccess: onReveal })}
            disabled={submit.isPending || words === 0}
          >
            Entregar
          </CtaButton>
        </div>
      </div>

      <aside className="sticky top-[84px] flex-[0_0_220px]">
        <Eyebrow className="tracking-[.2em]">você está revelando</Eyebrow>
        <div className="mt-4 w-[160px] opacity-90">
          <Mosaic photoUrl={picked.photoUrl} litTiles={[picked.seedTile]} />
        </div>
        <p className="text-muted mt-4 max-w-[21ch] font-serif text-[15px] italic">
          Cole o texto do dia aqui. Quanto mais você escreve, mais foto aparece
          na entrega.
        </p>
      </aside>
    </main>
  )
}
