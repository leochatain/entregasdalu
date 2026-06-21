import { formatNumber } from '../lib/format'
import Mosaic from './Mosaic'

/**
 * Menu tier square (frontend.md §7, §9): a teaser Mosaic + name + tag + word target.
 * Soft-select on click (red border + lift). All data comes from the server's offer
 * slot, so this is purely presentational — it takes props, never fetches.
 */
interface TierCardProps {
  name: string
  /** "leve" / "o de sempre" / "corajosa" */
  tag: string
  wordTarget: number
  photoUrl: string
  /** Central teaser tile from the offer (server-computed; the client never hashes). */
  seedTile: number
  selected?: boolean
  onSelect?: () => void
}

export default function TierCard({
  name,
  tag,
  wordTarget,
  photoUrl,
  seedTile,
  selected = false,
  onSelect,
}: TierCardProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      className={`focus-visible:outline-accent flex cursor-pointer flex-col gap-[13px] rounded-[5px] border-[1.5px] p-[15px] text-left transition-all duration-[250ms] focus-visible:outline-2 focus-visible:outline-offset-2 ${
        selected
          ? 'border-accent bg-surface -translate-y-[5px] shadow-[0_16px_34px_-18px_rgba(43,38,34,0.5)]'
          : 'border-line bg-transparent'
      }`}
    >
      <div className="w-full">
        <Mosaic photoUrl={photoUrl} litTiles={[seedTile]} />
      </div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-ink text-[26px] font-medium">{name}</span>
        <span
          className={`font-mono text-[12px] tracking-[.1em] uppercase ${
            selected ? 'text-accent' : 'text-tag-warm'
          }`}
        >
          {tag}
        </span>
      </div>
      <div className="text-muted-2 font-mono text-[14px] tracking-[.08em]">
        meta: {formatNumber(wordTarget)} palavras
      </div>
    </button>
  )
}
