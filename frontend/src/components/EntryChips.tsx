import type { FrozenEntry } from '../api/hooks'
import { formatShortDate } from '../lib/format'
import Chip from './Chip'

/** The date / tier / words chip row shared by Reveal, JáEntregue, and the gallery modal. */
export default function EntryChips({ entry }: { entry: FrozenEntry }) {
  return (
    <div className="flex flex-wrap justify-center gap-3">
      <Chip>{formatShortDate(entry.date)}</Chip>
      <Chip>{entry.name}</Chip>
      <Chip>{entry.effectiveWordCount} palavras</Chip>
    </div>
  )
}
