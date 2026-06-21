import type { ComponentPropsWithoutRef } from 'react'

/**
 * The courier-mono pill (frontend.md §7) — date / tier / words metadata rows.
 */
export default function Chip({
  className = '',
  ...props
}: ComponentPropsWithoutRef<'span'>) {
  return (
    <span
      className={`bg-chip-bg text-muted inline-block rounded-full px-[15px] py-[7px] font-mono text-[12px] tracking-[.06em] ${className}`}
      {...props}
    />
  )
}
