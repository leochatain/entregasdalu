# entregasdalu — Frontend Plan (v1)

Companion to [design.md](design.md) (architecture) and [spec.md](spec.md) (decisions). This doc is the **implementation-level plan for the frontend** — how we turn the approved visual prototype into the production React/Vite/TS SPA described in design.md §2.

> **Source of truth for visuals:** the Claude Design project **"Entregasdalu writing tool"**
> (`claude.ai/design/p/c61adf3e-6a40-47c8-b2cd-1380bf166f45`), files `Entregasdalu.dc.html`
> and `Mosaic.dc.html`. That prototype is a complete, working realization of all 9 screens.
> This document extracts its design tokens, component contracts, and copy, and specifies what
> changes when it becomes a real app talking to the Django-Ninja API.

> **How to access the prototype (implementing agent, do this first).** The prototype is **not** in
> this repo — it lives in the Claude Design project above, reachable via the **`claude_design` MCP
> connector** (`https://api.anthropic.com/v1/design/mcp`):
> 1. Ensure the connector is connected. If it needs authorization, run **`/design-login`** (grants
>    `user:design:read/write`). Read access depends on these scopes — a **headless/background agent
>    without them won't see the project**, so run this in an interactive session (or use the locally
>    materialized copy under `prototype/` if one was synced in).
> 2. Import the project (`projectId c61adf3e-6a40-47c8-b2cd-1380bf166f45`) with the `claude_design`
>    MCP tools. **Primary file: `Entregasdalu.dc.html`**; also pull `Mosaic.dc.html` and `support.js`.
> 3. The project also contains `photos/` (10 sample JPGs — fine as **dev placeholders**, distribute
>    across the `rascunho/ capitulo/ tese/` tier folders) and `screenshots/` (rendered reference PNGs:
>    `menu`, `rev`, `cal`, `frost*`, `0N-cta`).

> **Status:** first detailed pass. Where a decision is genuinely open it's marked **Decision (rec: …)**
> — sane default chosen, cheap to revisit.

> **⚠️ v1 scope reconciliation (read first).** This doc was written against the *full* spec §5 validation
> flow, but v1 has **no validation gate** (design.md §4.3): submit always succeeds. So the following are
> **deferred to a later version** and are NOT built in v1 — they return when validation does, alongside the
> `locked` status and `validationAttempts` field:
> - **Screens:** `Lockout.tsx` ("não é hoje") and `VoltaAmanha.tsx` ("hoje já foi").
> - **Editor fail state** (server validation message + "tentar de novo") and any attempt counting.
> - The `'locked' → VoltaAmanhã` resume branch; `useSubmit`'s fail/Lockout outcomes (→ Reveal only).
>
> **v1 ships 7 screens:** SignIn · Menu · Editor · Reveal · JáEntregue · Gallery · Stats. Everywhere below
> that mentions Lockout/VoltaAmanhã/fail, treat it as deferred. See design.md §2.1 for the reconciled set.

---

## Table of contents

1. [Relationship to the prototype](#1-relationship-to-the-prototype)
2. [Stack & project structure](#2-stack--project-structure)
3. [Design tokens (extracted from the prototype)](#3-design-tokens)
4. [Styling approach](#4-styling-approach)
5. [Routing & the app state machine](#5-routing--the-app-state-machine)
6. [Data layer & generated types](#6-data-layer--generated-types)
7. [Component inventory](#7-component-inventory)
8. [The Mosaic component — production spec](#8-the-mosaic-component--production-spec)
9. [Screen-by-screen build notes](#9-screen-by-screen-build-notes)
10. [Auth in the SPA](#10-auth-in-the-spa)
11. [Responsiveness & accessibility](#11-responsiveness--accessibility)
12. [Prototype → production divergences](#12-prototype--production-divergences)
13. [Build order](#13-build-order)
14. [Open frontend questions](#14-open-frontend-questions)

---

## 1. Relationship to the prototype

The prototype is **pixel-accurate and interaction-complete** — treat it as the spec for look, copy, and motion. But it is a single-file `DCLogic` toy: all state is local, "navigation" is a flat demo bar that jumps between every screen, the mosaic recomputes its reveal client-side from a `count`, and validation runs in the browser. Production inverts most of that:

| Prototype (DCLogic) | Production (React SPA) |
|---|---|
| Local `state.screen`, flat nav of all 9 screens | Real route + resume logic driven by `GET /api/today`; nav is just Hoje / Galeria / Calendário (+ sign-out) |
| Mosaic recomputes order from `count` + client hash | Server computes & **freezes** `revealedTiles`; client renders the stored list verbatim (spec §4) |
| `isGibberish()` in the browser | `POST /api/submit` validates server-side; client only renders pass/fail UI |
| Hard-coded tier/gallery/calendar data | `GET /api/today` · `/api/gallery` · `/api/stats` |
| Inline `style={{…}}` objects | Design tokens + CSS Modules (see §4) |
| `dc-import name="Mosaic"` | `<Mosaic/>` React component (see §8) |

What carries over **unchanged**: every color, font, size, radius, the editorial layout of each screen, all Portuguese copy, and the mosaic's frosted-tile reveal feel.

---

## 2. Stack & project structure

Per design.md §7: **TS React + Vite**, static build served by Caddy, API under `/api`.

```
frontend/
  index.html
  vite.config.ts
  package.json
  src/
    main.tsx                # mount, font preconnect, global CSS
    App.tsx                 # resume routing (state machine, §5)
    api/
      client.ts             # fetch wrapper (base /api, credentials, error shape)
      generated.ts          # OpenAPI → TS types (do not edit; see §6)
      hooks.ts              # useToday / usePick / useSubmit / useGallery / useStats
    state/
      session.ts            # auth/“who am I” + today-state cache
    styles/
      tokens.css            # CSS custom properties (the §3 table)
      global.css            # reset, body bg, ::selection, scrollbar, @keyframes
    components/
      Mosaic/               # the shared component (§8)
      NavBar.tsx
      CtaButton.tsx         # the shared filled button (signin/menu/entregar/…)
      Chip.tsx              # the courier-mono pill (date/tier/words)
    screens/
      SignIn.tsx
      Menu.tsx
      Editor.tsx
      Reveal.tsx
      Lockout.tsx           # “não é hoje” (attempt cap)
      VoltaAmanha.tsx       # day already spent
      JaEntregue.tsx        # resume of a submitted day
      Gallery.tsx           # grid + enlarge modal
      Stats.tsx             # calendar + stat cards
    lib/
      format.ts             # pt-BR dates, “sex · 20 jun”, pct, word count display
```

**Build/deploy:** `vite build` → static `dist/`, mounted by Caddy at `/` (design.md §7). No SSR.

---

## 3. Design tokens

Extracted verbatim from the prototype. These become `src/styles/tokens.css` custom properties.

### Color

| Token | Value | Used for |
|---|---|---|
| `--bg` | `#fafafa` | page background |
| `--surface` | `#ffffff` | cards, editor textarea, selected tier card |
| `--ink` | `#1a1a1a` | primary text, default CTA fill |
| `--ink-2` | `#3a3a38` / `#2a2a28` | secondary text in panels |
| `--muted` | `#5a5a58` | body/secondary copy |
| `--muted-2` | `#8a8a86` | captions, italic asides |
| `--faint` | `#b5b5b0` / `#bdbdb8` | weekday labels, disabled day numbers |
| `--accent` | `#d11f1f` | the red — logo, active nav, %, progress fill, selection |
| `--chip-bg` | `#f0f0ed` | courier pill background |
| `--panel` | `#f4f4f2` | fail message panel |
| `--line` | `#e6e6e4` | hairline borders / progress track |
| `--line-warm` | `#e3d9c7` / `#e4e4e0` | nav border, signin divider |
| `--tag-warm` | `#bcae98` | unselected tier tag |

### Type

- **Serif (display & body):** `Newsreader`, fallback `Georgia, serif`. Weights 300–600, italic used heavily for voice. Optical sizing `opsz 6..72`.
- **Mono (labels/eyebrows/chips):** `Courier Prime`, fallback `monospace`. Used uppercase with wide letter-spacing (`.06em`–`.34em`) for eyebrows, nav, chips, calendar.
- Load via the prototype's Google Fonts link (preconnect + the combined `css2` URL). Add `font-display: swap`. Consider self-hosting later for offline/perf — not v1-blocking.

Representative sizes (clamps preserve the prototype's responsive scale):
- Hero `h1`: `clamp(48px, 8.4vw, 128px)`, line-height ~1.0, `letter-spacing:-0.02em`
- Screen `h1`: `clamp(34px, 5vw, 58px)`
- Body lead: `18–19px`, italic for asides
- Editor text: `19px`, line-height `1.75`
- Eyebrow/mono: `11–12px` uppercase

### Spacing, radius, motion

- Content max-widths: `1020px` (menu), `1080px` (editor/gallery), `920px` (stats).
- Radii: cards `5–6px`, buttons `3px`, chips `99px`, mosaic `5–8px` (by context).
- Hover (all CTAs): `transform: translateY(-2px); filter: brightness(1.15)`, `transition: transform .2s, filter .2s`.
- Tier card select: `translateY(-5px)` + red border + soft shadow `0 16px 34px -18px rgba(43,38,34,.5)`.
- `@keyframes edlrise`: `opacity 0→1, translateY(10px→0)`, `.25–.35s ease` — used for fail panel and modal entry.
- Nav: fixed, 46px tall, `rgba(250,250,250,.9)` + `backdrop-filter: blur(8px)`, bottom border `--line-warm`.

---

## 4. Styling approach

**Decision (rec: CSS Modules + token custom properties).** The aesthetic is bespoke editorial, not utility-grid; Tailwind would fight the `clamp()`-heavy type and the italic-serif voice. Plan:

- `tokens.css` (`:root` custom properties from §3) + `global.css` (reset, body, `::selection{background:var(--accent);color:var(--bg)}`, scrollbar, `edlrise`).
- One `*.module.css` per screen/component; reference `var(--…)`.
- Shared primitives (`CtaButton`, `Chip`, eyebrow label) absorb the repeated inline patterns so each screen stays declarative.
- The CTA color enum in the prototype (`Preto`/`Vermelho`/`Verde`) is a design knob — ship **Preto** (`--ink` fill) as the default; keep it a single token swap if Lu wants red/green later.

Not chosen: Tailwind (bespoke design, low reuse payoff), CSS-in-JS runtime (unneeded for a static toy). Revisit only if component count balloons.

---

## 5. Routing & the app state machine

The app is **resume-first**, not URL-first: on load, `GET /api/today` returns the day's state and the client routes to the matching screen (design.md §2.1, spec §9). Read-only screens (Gallery, Stats) are reachable any time via nav.

```
GET /api/today  →  status?
  (no entry)   → Menu        (today's 3-tier offer)
  'picked'     → Editor      (resume; photoPath + wordTarget pinned)
  'submitted'  → JáEntregue  (frozen mosaic + the day’s stats)
  'locked'     → VoltaAmanhã (day spent, no photo)
not signed in  → SignIn
```

Transient screens **Reveal** (just after a passing submit) and **Lockout** (just after hitting the cap) are *client-side outcomes of an action*, not resume targets — on a hard reload they collapse to `JáEntregue` and `VoltaAmanhã` respectively (the persistent equivalents). The prototype shows all four as separate nav items only because it's a demo.

**Decision (rec: minimal routing).** A single resolved-state switch in `App.tsx` plus nav state for Gallery/Stats overlays is enough for v1 — no react-router needed. Add real routes only if deep-linking the gallery becomes desirable. Nav items in production: **Hoje · Galeria · Calendário** + sign-out (collapse the prototype's 9-item demo bar).

State held by `App`: `todayState` (from API), `view` (`'today' | 'gallery' | 'stats'`), and ephemeral action results (`revealResult`, `failState`). Editor draft text is local to `Editor` (not persisted server-side per spec — the text is never stored).

---

## 6. Data layer & generated types

- **Types are generated from the backend OpenAPI** (Django-Ninja emits it) into `src/api/generated.ts` — single source of truth, no hand-kept duplicates (design.md §2.5). Wire an `openapi-typescript` (or `orval`) step into `package.json` (`npm run gen:api`), committed output, regenerated when the API changes.
- `api/client.ts`: thin `fetch` wrapper — base `/api`, `credentials: 'include'` (session cookie, §10), JSON in/out, a normalized error type, and a 401 → SignIn signal.
- `api/hooks.ts`: **Decision (rec: TanStack Query)** for `useToday`/`useGallery`/`useStats` (cache, refetch-on-focus, mutation invalidation) — small, well-suited to ~5 endpoints. Acceptable fallback: hand-rolled `useEffect` fetchers given the toy scale; pick Query for the free cache-invalidation on submit. `usePick`/`useSubmit` are mutations that invalidate `today`.

Endpoint → screen mapping (contracts owned by the API detail dive; design.md §5):

| Hook | Endpoint | Feeds |
|---|---|---|
| `useToday` | `GET /api/today` | resume routing + Menu offer |
| `usePick` | `POST /api/pick` | Menu → Editor (pins photoPath) |
| `useSubmit` | `POST /api/submit` | Editor → Reveal / fail / Lockout |
| `useGallery` | `GET /api/gallery` | Gallery grid + modal |
| `useStats` | `GET /api/stats` | Stats calendar + cards |

**Payload note the FE needs from the API:** the offer in `today` must include, per tier slot, `{ tier, name, wordTarget, photoUrl, seedTile }` (seedTile = the central teaser tile, computed server-side so the client never re-derives the hash). `gallery`/`today(submitted)` items must include `revealedTiles` (the frozen ordered list). See §8 for why.

---

## 7. Component inventory

| Component | Role | Notes |
|---|---|---|
| `NavBar` | fixed top nav | logo `e/dl`, Hoje/Galeria/Calendário, sign-out; active = red underline |
| `CtaButton` | the filled action button | variant via token; hover lift; used on signin/menu/editor/reveal/amanhã/modal |
| `Chip` | courier-mono pill | date / tier / words metadata rows |
| `Eyebrow` | uppercase mono caption | the `.24em` letter-spaced labels above headings |
| `Mosaic` | **the** shared photo component | teaser / animated reveal / frozen — see §8 |
| `TierCard` | menu tier square | wraps a teaser Mosaic + name/tag/target; selected styling |
| `ProgressBar` | editor word-count fill | red fill, `width %`, `.35s` ease |
| `GalleryGrid` + `GalleryModal` | trophy wall + enlarge | modal uses `edlrise`, dim backdrop, stop-propagation |
| `Calendar` | month heatmap | tinted day cells + legend; **real weekday offset** (see §9 Stats) |
| `StatCards` | the 5 aggregate tiles | streak / longest / words / deliveries / photos |

---

## 8. The Mosaic component — production spec

This is the highest-correctness component and the biggest prototype→production change. **The mosaic must render the server's frozen tile list verbatim and never recompute a frozen reveal** (spec §3.2, §4 — "the stored tiles *are* the truth").

### Props contract (production)

```ts
interface MosaicProps {
  photoUrl: string;
  litTiles: number[];   // tile indices (0..47) to show un-frosted, in reveal order
  animate?: boolean;    // pop-in litTiles one-by-one (Reveal screen only)
  gap?: number;         // px, default 0
  radius?: number;      // px, default 6
}
```

Single contract for all three modes — the *order math lives server-side*, the client just lights `litTiles`:

- **Teaser** (Menu / Editor aside): `litTiles = [seedTile]` from the offer payload (1 central tile ≈ 2%).
- **Animated reveal** (Reveal screen): `litTiles = revealedTiles` from the submit response, `animate`. Pop them in *in array order* (that order is the server's tie-break order, so the animation is organic and matches the freeze).
- **Frozen** (Gallery, JáEntregue, modal): `litTiles = revealedTiles`, no animate. Render directly.

> Why not pass `count` and recompute (as the prototype does)? Because the freeze must be immune to any later change in grid/seed/algorithm. The client must light exactly the stored indices. Passing `count` would re-derive order in the browser and could drift from what was frozen. The prototype recomputes only because it has no server.

### Grid & slice math (unchanged from prototype/spec)

- Grid: **8 rows × 6 cols = 48** (`cols=6, rows=8`), `aspect-ratio: 6 / 8`, vertical photos.
- Each tile shows its slice via `background-image: url(photoUrl)`, `background-size: 600% 800%`, `background-position: (c/5*100)% (r/7*100)%` where `idx = r*6 + c`.
- Frosted (un-lit) overlay per tile: absolutely-positioned div, `background: rgba(239,241,245,.965)`, `backdrop-filter: blur(9px) saturate(.5)`, inset highlight `inset 0 1px 0 rgba(255,255,255,.55)`. Lit tile = overlay `opacity:0; transform:scale(1.1)`.
- Tile base: `background-color:#e9ebee`, `1px solid rgba(45,55,70,.2)`; container `background:#e2e5e9` with `gap`-px padding.

### Animation

- Stagger `~17ms × rank` (prototype's `step`), `opacity 320ms ease, transform 380ms ease` on the frost overlay, kicked after a double-`requestAnimationFrame` so the initial frosted state paints first. Honor `prefers-reduced-motion`: skip the stagger, render final state.
- Only the **Reveal** screen animates. Frozen renders are static (no layout thrash in the gallery grid).

### Seed/order ownership

The Chebyshev ordering, central-seed selection, and tie-break (`hash(date+photoId)` → seed; `chebyshev→center-distance→hash`) are computed **once, server-side at submit** and persisted (spec §4, §9). The client's only ordering responsibility is the **teaser seed**, which the API provides as `seedTile`. We keep *no* hashing/ordering logic in the client — this is a deliberate divergence from `Mosaic.dc.html`, which does it all locally to fake the backend.

---

## 9. Screen-by-screen build notes

Copy is Portuguese (pt-BR), lifted from the prototype; keep the warm, low-pressure voice (spec §1, principle #1). Dates render via `lib/format.ts` (America/São_Paulo).

**SignIn** — split hero: oversized italic-serif headline ("Oi, boa noite, será que vai ter **entrega** da Lu hoje?") + a Google button with a circular `G` badge and the aside "só a Lu entra aqui. (oi, Lu.)". Button → real OAuth start (§10), not a local `goMenu`. Warm left-divider on the right column.

**Menu / Hoje** — eyebrow date · "Escolha o desafio do dia" · italic explainer. 3-col grid of `TierCard`s, each = teaser Mosaic (`litTiles=[seedTile]`) + name + tag (`leve` / `o de sempre` / `corajosa`) + "meta: N palavras". Soft-select on click (red border + lift). "Escolher este desafio →" commits via `POST /api/pick` and routes to Editor. The pick is soft until commit (design.md §2.3); on reshuffle (folder changed) the offer can differ until pinned — that's expected.

**Editor** — two-column: left = heading (tier name) + `countLabel` ("N / target palavras") + red `ProgressBar` + the clean white `textarea` (paste-friendly, `19px/1.75`, inset hairline). Right aside (sticky) = small teaser Mosaic ("você está revelando") + helper italic. "Entregar" → `POST /api/submit`. The prototype's "demo: texto real / rabisco" toggles are **dropped** in production. Fail state (below textarea, `edlrise`): `✺` + playful server message + "tentar de novo". Validation, attempt counting, and the escalating copy all come from the server response, not the client.

**Reveal** — centered: eyebrow "entrega feita" · "Entrega de hoje" · animated Mosaic (`litTiles=revealedTiles`, `animate`) · big "NN% revelado" · chips (date / tier / words) · "— congelado, pra sempre. é seu. —" · "Ver na galeria →". This is the post-submit celebration; reload → JáEntregue.

**Lockout ("não é hoje")** — eyebrow "sem foto hoje · sem drama" · big italic "Tá. Claramente *não é hoje*." · reassuring paragraph · ghost button "Olhar a galeria enquanto isso". Shown only right after the attempt cap; reload → VoltaAmanhã.

**VoltaAmanhã** — eyebrow with live countdown "próximo cardápio em Xh Ymin" (compute from São Paulo midnight) · "Hoje já foi." · italic encouragement · "Rever a galeria". This is the persistent `locked` resume screen.

**JáEntregue** — eyebrow "resumo de hoje" · "Você já entregou hoje. *Bem aí.*" · frozen Mosaic + chips. The persistent `submitted` resume screen (no animation).

**Gallery** — header eyebrow "diário de esforço" + "Galeria" + "N fotos · X% do acervo". Responsive grid (`minmax(148px,1fr)`), each cell = frozen Mosaic (`litTiles=revealedTiles`) + date + red `pct%`, hover lift. Click → modal (`edlrise`, dim+blur backdrop, click-out to close): enlarged frozen Mosaic + tier + pct + "date · words palavras" + "fechar". `acervo %` = unlocked ÷ total pool, from `/api/stats`.

**Stats / Calendário** — eyebrow "o ano de 2026" + month name. 5 `StatCards` (sequência atual / maior sequência / palavras escritas / entregas / fotos coletadas). 7-col calendar, weekday header (`seg…dom`), day cells tinted by reveal % (`rgba(26,26,26, .10 + pct/100*.80)`, light text when pct>50), today ringed, future faint, missed dashed. **Production fix:** offset the first cell to the real weekday of day 1 (the prototype naively starts at column 1) and use the real month length — drive both from `/api/stats`, don't hard-code 30 days. Legend row "menos → mais revelado".

---

## 10. Auth in the SPA

Google sign-in via django-allauth, single allowlisted email (design.md §6, spec §8).

- **Decision (rec: session cookie).** SPA uses `credentials: 'include'`; the SignIn button hits the allauth Google start URL (full-page redirect, not `fetch`). After callback, the server sets the session cookie and redirects back to `/`; `GET /api/today` then resolves normally.
- "Not signed in" detection: any API `401` (or `today` indicating no session) → render **SignIn**. No tokens in JS, no localStorage.
- Sign-out: POST to the allauth logout, then route to SignIn.
- The `email != LU_EMAIL → 403` check is server-side; the client treats `403` as "this isn't Lu" (rare; show the SignIn aside copy).

---

## 11. Responsiveness & accessibility

- **Responsive:** the prototype is already fluid (`clamp()` type, `flex-wrap`, `auto-fill` grids). Verify the three breakpoints implied: tier grid 3→1 col, editor two-col → stacked, gallery `minmax` reflow. Nav scrolls horizontally on narrow screens (`overflow-x:auto`).
- **A11y:** real `<button>`/`<textarea>` (prototype already uses them) — keep semantics. Add: focus-visible rings (don't rely on hover-only affordances), `aria-label` on icon-only/`G`-badge controls, modal focus trap + `Esc` to close + restore focus, `aria-live="polite"` on the editor word count and the fail message, `prefers-reduced-motion` honored in Mosaic and `edlrise`. Ensure tinted calendar cells meet contrast (light text only above the pct>50 threshold, as the prototype does).
- **Mosaic semantics:** decorative tiles `aria-hidden`; give the Mosaic a meaningful `role="img"` + `aria-label` (e.g. "foto revelada 62%").

---

## 12. Prototype → production divergences

The explicit list of "do **not** copy the prototype here":

1. **Mosaic renders `litTiles` (stored), never recomputes from `count`.** Frozen truth comes from the server (§8). The client keeps zero hashing/ordering logic.
2. **Validation is server-side.** Drop `isGibberish()`; the fail message, attempt count, and lockout transition come from `POST /api/submit`.
3. **Nav collapses** from 9 demo items to Hoje / Galeria / Calendário + sign-out.
4. **Reveal & Lockout are action outcomes, not routes** — reload resolves to JáEntregue / VoltaAmanhã.
5. **Drop the editor "demo: texto real / rabisco" toggles.**
6. **Calendar uses real weekday offset + real month length** from `/api/stats`, not a fixed 1→30 grid.
7. **Teaser seed comes from the API** (`seedTile`), not a client hash.
8. **Auth is real OAuth** (full-page redirect), not a local `goMenu` jump.
9. **Demo data → API.** Tiers, gallery, stats, today-state all fetched; nothing hard-coded except UI constants (grid 8×6, tier names/targets if mirrored, CTA color).
10. **Countdown on VoltaAmanhã is computed** from São Paulo midnight, not a static "11h 42min".

---

## 13. Build order

Suggested FE milestones (independent of backend readiness — mock the 5 endpoints first):

1. **Foundation** — Vite+TS scaffold, fonts, `tokens.css`/`global.css`, `CtaButton`/`Chip`/`Eyebrow`, NavBar shell.
2. **Mosaic** — the production component (teaser + frozen + animated), tested against the spec's slice/seed math with a fixed `litTiles` fixture. This unblocks 4 screens.
3. **API layer** — `client.ts`, OpenAPI codegen, hooks, with a mock server returning the prototype's demo data shaped to the real contracts.
4. **Core loop** — Menu → Editor → Reveal, wired to `pick`/`submit`; fail + Lockout states.
5. **Resume + persistent states** — `App` state machine, JáEntregue, VoltaAmanhã, SignIn gate.
6. **Diary** — Gallery (grid + modal), Stats (calendar + cards) with real weekday offset.
7. **Polish** — reduced-motion, focus/keyboard, responsive verification, contrast, empty states (no photos in a pool → "sem foto hoje").
8. **Wire to real backend** — swap mock for live API, OAuth, deploy build behind Caddy.

---

## 14. Open frontend questions

- **Data-fetching lib:** TanStack Query (rec) vs hand-rolled — confirm before §13 step 3.
- **Self-host fonts** vs Google CDN — CDN for v1; self-host if offline/perf matters.
- **Gallery deep-linking** — needed? If yes, add react-router and a `/galeria/:date` route (otherwise the §5 minimal switch stands).
- **Empty-pool teaser** — exact "sem foto hoje" tier-card treatment (spec §9 allows a `None` slot) — design it when the offer payload lands.
- **Reveal-animation timing** — keep the prototype's `17ms`/`320–380ms`, or slow it for drama? (spec §11 open, cosmetic.)
- Carries from spec §11: final tier display names, exact editor styling, attempt-cap value & escalating copy — all server/UI copy, non-blocking.
