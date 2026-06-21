import { useEffect, useState } from 'react'

/**
 * The Mosaic — the highest-correctness component (frontend.md §8, spec §3.2/§4).
 *
 * One contract serves all three modes; the client renders the server's frozen
 * tile list **verbatim** and keeps ZERO hashing/ordering logic. The order math
 * (central seed → Chebyshev → tie-break) lives server-side and is persisted at
 * submit, so `litTiles` already arrives in reveal order:
 *
 *  - Teaser   (Menu/Editor):     litTiles=[seedTile]
 *  - Reveal   (Reveal screen):   litTiles=revealedTiles, animate
 *  - Frozen   (Gallery/JáEntregue): litTiles=revealedTiles, static
 *
 * Grid is an app-wide FROZEN constant: 8 rows × 6 cols = 48, row-major,
 * idx = row*6 + col. Never change its meaning — past entries are read against it.
 */

export const MOSAIC_COLS = 6
export const MOSAIC_ROWS = 8
export const MOSAIC_TILES = MOSAIC_COLS * MOSAIC_ROWS // 48

/** Per-tile pop-in stagger (prototype's `step`). */
const STAGGER_MS = 17

export interface MosaicProps {
  photoUrl: string
  /** Tile indices (0..47) to show un-frosted, in reveal order. */
  litTiles: number[]
  /** Pop the tiles in one-by-one (Reveal screen only). */
  animate?: boolean
  /** Padding/gap between tiles, px. */
  gap?: number
  /** Container corner radius, px. */
  radius?: number
}

export default function Mosaic({
  photoUrl,
  litTiles,
  animate = false,
  gap = 0,
  radius = 6,
}: MosaicProps) {
  const reduced = usePrefersReducedMotion()
  const shouldAnimate = animate && !reduced

  // `started` gates the frost fade. Static renders start "done" (no transition);
  // animated renders flip to started after a double-rAF so the frosted state
  // paints first, then the tiles pop in.
  const [started, setStarted] = useState(!shouldAnimate)
  const litKey = litTiles.join(',')
  useEffect(() => {
    if (!shouldAnimate) return
    // Re-frost then reveal after the next paint, so the animation (re)plays when
    // the photo or tile set changes. setState lives in the rAF callbacks (not the
    // effect body), and the first render already paints frosted (started=false).
    let raf2 = 0
    const raf1 = requestAnimationFrame(() => {
      setStarted(false)
      raf2 = requestAnimationFrame(() => setStarted(true))
    })
    return () => {
      cancelAnimationFrame(raf1)
      cancelAnimationFrame(raf2)
    }
  }, [shouldAnimate, photoUrl, litKey])

  // idx → rank in reveal order (drives the stagger; absence === frosted).
  const rankByIdx = new Map<number, number>()
  litTiles.forEach((idx, rank) => rankByIdx.set(idx, rank))

  const pct = Math.round((litTiles.length / MOSAIC_TILES) * 100)

  return (
    <div
      role="img"
      aria-label={`foto revelada ${pct}%`}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${MOSAIC_COLS}, 1fr)`,
        gridTemplateRows: `repeat(${MOSAIC_ROWS}, 1fr)`,
        gap: `${gap}px`,
        padding: `${gap}px`,
        aspectRatio: `${MOSAIC_COLS} / ${MOSAIC_ROWS}`,
        width: '100%',
        backgroundColor: '#e2e5e9',
        borderRadius: `${radius}px`,
        overflow: 'hidden',
        boxSizing: 'border-box',
      }}
    >
      {Array.from({ length: MOSAIC_TILES }, (_, idx) => {
        const r = Math.floor(idx / MOSAIC_COLS)
        const c = idx % MOSAIC_COLS
        const rank = rankByIdx.get(idx)
        const lit = rank !== undefined
        const posX = (c / (MOSAIC_COLS - 1)) * 100
        const posY = (r / (MOSAIC_ROWS - 1)) * 100
        const delay = shouldAnimate && lit ? rank * STAGGER_MS : 0
        const revealed = lit && started
        return (
          <div
            key={idx}
            aria-hidden
            style={{
              position: 'relative',
              backgroundColor: '#e9ebee',
              backgroundImage: `url("${photoUrl}")`,
              backgroundSize: `${MOSAIC_COLS * 100}% ${MOSAIC_ROWS * 100}%`,
              backgroundPosition: `${posX}% ${posY}%`,
              border: '1px solid rgba(45,55,70,0.2)',
              overflow: 'hidden',
              boxSizing: 'border-box',
            }}
          >
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'rgba(239,241,245,0.965)',
                backdropFilter: 'blur(9px) saturate(0.5)',
                WebkitBackdropFilter: 'blur(9px) saturate(0.5)',
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.55)',
                opacity: revealed ? 0 : 1,
                transform: revealed ? 'scale(1.1)' : 'scale(1)',
                transition: lit
                  ? 'opacity 320ms ease, transform 380ms ease'
                  : 'none',
                transitionDelay: `${delay}ms`,
                pointerEvents: 'none',
                willChange: 'opacity, transform',
              }}
            />
          </div>
        )
      })}
    </div>
  )
}

/** True when the user asked the OS to reduce motion. */
function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return reduced
}
