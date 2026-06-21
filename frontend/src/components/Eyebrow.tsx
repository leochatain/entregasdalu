import type { ComponentPropsWithoutRef } from 'react'

/**
 * The uppercase mono caption above headings (frontend.md §7). The `--text-eyebrow`
 * token carries the 11px size + `.24em` tracking; screens that want a wider track
 * (the prototype ranges .2–.34em) override via `className`.
 */
export default function Eyebrow({
  className = '',
  ...props
}: ComponentPropsWithoutRef<'p'>) {
  return (
    <p
      className={`text-eyebrow text-muted-2 font-mono uppercase ${className}`}
      {...props}
    />
  )
}
