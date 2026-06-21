import { type CSSProperties, useEffect, useState } from 'react'

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
 *
 * Rendering: ONE <img> behind a grid of 48 lightweight frost overlays. The photo
 * decodes and paints once; only the cheap opacity overlays vary per tile. (The
 * old build painted the full image into 48 background layers and ran a
 * backdrop-filter blur on each — ~100 MB decoded bitmaps and 48 blur layers per
 * mosaic, which the gallery multiplied by every submitted day. This is that fix.)
 */

export const MOSAIC_COLS = 6
export const MOSAIC_ROWS = 8
export const MOSAIC_TILES = MOSAIC_COLS * MOSAIC_ROWS // 48

/** Per-tile pop-in stagger (prototype's `step`). */
const STAGGER_MS = 17

/** Near-opaque frost. Solid enough to hide the sharp photo without a (costly)
 * backdrop-filter blur — the old overlay was already 96.5% opaque, so this reads
 * essentially the same while removing the single most expensive effect. */
const FROST = 'rgba(241,243,246,0.985)'

/** Shared positioning for the two 6×8 overlay grids (frost + grid lines). */
const gridLayer: CSSProperties = {
  position: 'absolute',
  inset: 0,
  display: 'grid',
  gridTemplateColumns: `repeat(${MOSAIC_COLS}, 1fr)`,
  gridTemplateRows: `repeat(${MOSAIC_ROWS}, 1fr)`,
}

export interface MosaicProps {
  photoUrl: string
  /** Tile indices (0..47) to show un-frosted, in reveal order. */
  litTiles: number[]
  /** Pop the tiles in one-by-one (Reveal screen only). */
  animate?: boolean
  /** Container corner radius, px. */
  radius?: number
}

export default function Mosaic({
  photoUrl,
  litTiles,
  animate = false,
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
        position: 'relative',
        aspectRatio: `${MOSAIC_COLS} / ${MOSAIC_ROWS}`,
        width: '100%',
        backgroundColor: '#e2e5e9',
        borderRadius: `${radius}px`,
        overflow: 'hidden',
      }}
    >
      {/* Single decode, single paint. lazy/async keeps offscreen gallery tiles cheap. */}
      <img
        src={photoUrl}
        alt=""
        aria-hidden
        loading="lazy"
        decoding="async"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: 'block',
        }}
      />
      {/* Fading frost: one cell per tile, hides the photo until its tile is lit. */}
      <div style={gridLayer}>
        {Array.from({ length: MOSAIC_TILES }, (_, idx) => {
          const rank = rankByIdx.get(idx)
          const lit = rank !== undefined
          const delay = shouldAnimate && lit ? rank * STAGGER_MS : 0
          const revealed = lit && started
          return (
            <div
              key={idx}
              aria-hidden
              style={{
                background: FROST,
                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.55)',
                opacity: revealed ? 0 : 1,
                transform: revealed ? 'scale(1.1)' : 'scale(1)',
                // Delay folded into the shorthand — don't mix `transition` with
                // the `transitionDelay` longhand (React warns on re-render).
                transition: lit
                  ? `opacity 320ms ease ${delay}ms, transform 380ms ease ${delay}ms`
                  : 'none',
                pointerEvents: 'none',
                willChange: 'opacity, transform',
              }}
            />
          )
        })}
      </div>
      {/* Static grid lines: always visible over both revealed and frosted tiles,
          so the mosaic reads as tiled even where the photo shows through. */}
      <div style={gridLayer} aria-hidden>
        {Array.from({ length: MOSAIC_TILES }, (_, idx) => (
          <div
            key={idx}
            style={{
              border: '1px solid rgba(45,55,70,0.2)',
              boxSizing: 'border-box',
            }}
          />
        ))}
      </div>
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
