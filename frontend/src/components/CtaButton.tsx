import type { ComponentPropsWithoutRef } from 'react'

/**
 * The filled action button (frontend.md §7) — signin / menu / entregar / reveal / …
 *
 * Ships the "Preto" palette by default (ink fill, bg text); the CTA color is a
 * single-token swap later (frontend.md §4). Sizing varies per screen, so callers
 * tweak padding/text via `className` — the base sets everything else.
 */
export default function CtaButton({
  className = '',
  type = 'button',
  ...props
}: ComponentPropsWithoutRef<'button'>) {
  return (
    <button
      type={type}
      className={`bg-ink text-bg focus-visible:outline-accent inline-flex cursor-pointer items-center justify-center gap-3 rounded-[3px] px-7 py-3.5 font-serif text-[18px] transition duration-200 hover:-translate-y-0.5 hover:brightness-[1.15] focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
      {...props}
    />
  )
}
