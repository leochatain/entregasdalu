import { clamp01 } from '../lib/format'

/**
 * Editor word-count fill (frontend.md §7): red fill over a hairline track, width %,
 * `.35s` ease. `value` is the 0..1 progress (use `progress(words, target)`).
 */
interface ProgressBarProps {
  value: number
}

export default function ProgressBar({ value }: ProgressBarProps) {
  const pct = Math.round(clamp01(value) * 100)
  // Floor a non-zero amount to 3% so the slightest progress still reads.
  const width = pct === 0 ? '0%' : `${Math.max(3, pct)}%`
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      className="bg-line h-1.5 overflow-hidden rounded-full"
    >
      <div
        className="bg-accent h-full rounded-full transition-[width] duration-[350ms] ease-out"
        style={{ width }}
      />
    </div>
  )
}
