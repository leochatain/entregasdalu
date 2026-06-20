# entregasdalu — Design Doc & Implementation Plan (v1)

Companion to [spec.md](spec.md) (decisions + rejected alternatives — the **what/why**) and [frontend.md](frontend.md) (the implementation-level FE plan keyed to the Claude Design prototype — design tokens, CSS, per-screen copy). This doc records the **architecture** and the **frontend↔backend contract**; it points to frontend.md for pixel-level detail rather than duplicating it.

> **Status:** first pass — high level. Each top-level section is intended to be expanded into a detail dive later. Where this doc would re-derive a settled decision, it links back to the spec instead.

> **Scope note:** This is an architecture document, not a phased roadmap. It describes the shape of each part of the system; build order is left to the implementer.

---

## Table of contents

1. [System overview](#1-system-overview) — the one-paragraph mental model + diagram
2. [UI](#2-ui) — pages, flow, state machine, Mosaic, FE↔BE contract (detail in [frontend.md](frontend.md))
3. [Storage](#3-storage) — the single table, the filesystem, backups
4. [Backend / domain logic](#4-backend--domain-logic) — offer, reveal, validation modules
5. [API surface](#5-api-surface) — endpoint list (contracts deferred)
6. [Auth](#6-auth) — Google sign-in + single-email allowlist
7. [Stack & infra](#7-stack--infra) — host, proxy, deploy, backup
8. [Cross-cutting concerns](#8-cross-cutting-concerns) — time/dates, determinism, config, errors
9. [Testing strategy](#9-testing-strategy)
10. [Open questions for this doc](#10-open-questions-for-this-doc)

---

## 1. System overview

A single-user app. A React SPA talks to an API-only Django backend over `/api`; Caddy serves the static build and reverse-proxies the API. State of record is one SQLite table (`DailyEntry`) plus a folder of curated photos on the instance filesystem. No object storage, no secrets, no second user.

```
                  ┌─────────────────────────────────────────┐
   Browser ──TLS──┤ Caddy                                    │
                  │   /         → React static build (Vite)  │
                  │   /api/*    → gunicorn → Django-Ninja     │
                  └───────────────┬──────────────────────────┘
                                  │
                      ┌───────────┴───────────┐
                      │ Django backend         │
                      │   offer / reveal /     │
                      │   validation modules   │
                      └─────┬──────────────┬───┘
                            │              │
                     SQLite (DailyEntry)   photos/ (tier folders)
                       ← the artifact        ← reproducible
```

**Mental model:** the backend is mostly *pure functions over the date and the filesystem* (the daily offer, the reveal tile set) plus one tiny table that freezes outcomes. Most complexity is in the frontend interaction; the backend is deliberately thin.

---

## 2. UI

The interesting half of the app. Real interactivity (mosaic reveal, editor, gallery) is why we chose React (spec §7). The **visual source of truth** is the Claude Design prototype ("Entregasdalu writing tool") — pixel-accurate and interaction-complete. [frontend.md](frontend.md) extracts its tokens, CSS, component contracts, and pt-BR copy. This section captures only the **architecture** and the **frontend↔backend seam**; tokens/CSS/per-screen copy live in frontend.md.

### 2.1 Screen set & resume routing

The app is **resume-first**, not URL-first: on load, `GET /api/today` returns the day's state and the client routes to the matching screen (spec §9). Read-only screens (Gallery, Stats) are reachable any time via nav (**Hoje · Galeria · Calendário** + sign-out).

| Condition | Screen | Kind |
|---|---|---|
| not signed in | **SignIn** | gate |
| no entry today | **Menu** (3-tier offer) | resume target |
| `status='picked'` | **Editor** (resume; `photoPath`+`wordTarget` pinned) | resume target |
| `status='submitted'` | **JáEntregue** (frozen mosaic + day's stats) | resume target |
| — just submitted — | **Reveal** (animated pop-in + celebration) | transient outcome |
| Gallery / Stats | **Gallery**, **Stats** | nav, any time |

**Reveal is a transient action outcome, not a resume target:** it plays once right after a passing submit; a hard reload collapses to **JáEntregue** (the persistent equivalent). So v1 has **7 screens**.

> **v1 reconciliation with the simplified backend (§4.3):** the prototype/frontend.md also describe **Lockout** ("não é hoje"), **VoltaAmanhã** ("hoje já foi"), and an Editor **fail state** (server validation message + retry). v1 has **no validation gate**, so none of these can occur — they are **deferred** and return alongside validation (with the `locked` status, §3). The prototype's 9 demo screens → 7 in v1.

### 2.2 Pages (v1)

1. **SignIn** — Google OAuth start (full-page redirect, §6), single-email aside ("só a Lu entra aqui").
2. **Menu / Hoje** — 3 `TierCard`s, each a teaser Mosaic (`litTiles=[seedTile]`) + name + tag + "meta: N palavras". Soft-select; "Escolher este desafio →" commits via `POST /api/pick` → Editor. (spec §2–3)
3. **Editor** — tier heading + live word-count `ProgressBar` + clean paste-in `textarea` + sticky teaser Mosaic aside. "Entregar" → `POST /api/submit`. Submit always succeeds (v1, §4.3). (spec §2)
4. **Reveal** — animated Mosaic (`litTiles=revealedTiles`, `animate`), "NN% revelado", chips (date/tier/words), "Ver na galeria →". Transient. (spec §4)
5. **JáEntregue** — persistent `submitted` resume: frozen Mosaic + chips, no animation.
6. **Gallery** — trophy grid of frozen Mosaics + date + `pct%`; click → enlarge modal. "N fotos · X% do acervo". (spec §6)
7. **Stats / Calendário** — 5 stat cards + month calendar tinted by reveal %, **real weekday offset + month length** from `/api/stats` (not a fixed 1→30 grid). (spec §6)

### 2.3 Routing & app state machine

**Minimal routing, no react-router** for v1: a single resolved-state switch in `App.tsx` + nav state for the Gallery/Stats views. Add real routes only if gallery deep-linking becomes desirable. `App` holds: `todayState` (API), `view` (`'today'|'gallery'|'stats'`), and the ephemeral `revealResult`. Editor draft text is **local to the Editor** — never persisted server-side (spec: text is never stored).

### 2.4 Pick → commit state machine

Pick is **soft** (can change mind, offer may reshuffle if the folder changes) until "Escolher este desafio" → `POST /api/pick`, which creates the `picked` entry and **pins** `photoPath`+`wordTarget`. After that the offer is fixed for the day. (Note: this commits on the explicit choose action, not on first keystroke as an earlier draft implied — `pick` precedes the Editor.) Mid-pick reload (before commit) → back to Menu; the offer is recomputed (deterministic for today, §4.1).

### 2.5 Mosaic component — the FE↔BE seam

The highest-correctness component and the biggest prototype→production change. **The client renders the server's frozen tile list verbatim and never recomputes a reveal** (spec §3.2, §4 — "the stored tiles *are* the truth"). All the seed/Chebyshev/tie-break math lives server-side (§4.2); the client keeps **zero** hashing/ordering logic.

```ts
interface MosaicProps {
  photoUrl: string;
  litTiles: number[];   // tile indices 0..47 to show un-frosted, in reveal order
  animate?: boolean;    // pop-in one-by-one — Reveal screen only
}
```

One contract, three modes:
- **Teaser** (Menu/Editor): `litTiles=[seedTile]` from the offer payload.
- **Animated reveal** (Reveal): `litTiles=revealedTiles` from the submit response, animated in array order (= the server's tie-break order).
- **Frozen** (Gallery/JáEntregue/modal): `litTiles=revealedTiles`, static.

Grid/slice math (frozen contract, matches §4.2): 8 rows × 6 cols, `aspect-ratio:6/8`; tile `idx=r*6+c` shows its slice via `background-size:600% 800%`, `background-position:(c/5·100)% (r/7·100)%`. Un-lit tiles wear a frosted CSS overlay (blur); lit tiles fade the overlay out.

> **Accepted property — the full photo reaches the browser.** "Frost" is a CSS overlay over the complete image, so a determined peek in devtools sees the un-revealed photo. This is fine per principle #1 ("the adversary is procrastination… gaming only cheats herself"). It also means **photos need a serving route** — Caddy static under e.g. `/photos/*` (or a Django passthrough). Decided in §7; the offer/gallery payloads carry a ready-to-use `photoUrl`.

Animation/easing timing is cosmetic (spec §11) — see frontend.md §8; honor `prefers-reduced-motion`.

### 2.6 Data layer & generated types

- **Types generated from the backend OpenAPI** (Django-Ninja emits it) into `src/api/generated.ts` — single source of truth, no hand-kept duplicates. A `gen:api` step (`openapi-typescript`/`orval`) regenerates on API change.
- `api/client.ts`: thin `fetch` wrapper — base `/api`, `credentials:'include'` (session cookie, §6), normalized error type, `401 → SignIn`.
- **Data-fetching: TanStack Query** (rec) for `useToday`/`useGallery`/`useStats` (cache + mutation invalidation); `usePick`/`useSubmit` are mutations that invalidate `today`. (Hand-rolled `useEffect` is an acceptable fallback at this scale.)

| Hook | Endpoint | Feeds |
|---|---|---|
| `useToday` | `GET /api/today` | resume routing + Menu offer |
| `usePick` | `POST /api/pick` | Menu → Editor (pins `photoPath`) |
| `useSubmit` | `POST /api/submit` | Editor → Reveal |
| `useGallery` | `GET /api/gallery` | Gallery grid + modal |
| `useStats` | `GET /api/stats` | Stats calendar + cards |

The concrete payload shapes the FE depends on (offer slot fields, `revealedTiles`, `seedTile`) are specified in **§5**.

### 2.7 Styling, responsiveness, a11y (pointers)

Bespoke editorial aesthetic → **CSS Modules + token custom properties** (not Tailwind). Fluid `clamp()` type; three breakpoints (tier grid 3→1, editor two-col→stacked, gallery reflow). A11y: real `<button>`/`<textarea>`, focus-visible rings, modal focus-trap + `Esc`, `aria-live` on word count, Mosaic `role="img"` + `aria-label` ("foto revelada 62%"), `prefers-reduced-motion`. Full token table, CSS specs, and per-screen copy: **[frontend.md](frontend.md) §3–4, §9, §11**.

---

## 3. Storage

The whole model is **one SQLite table + the photo filesystem** (spec §9). No `Photo` table (identity is the path), no `DailyOffer` table (it's a pure function of the date, §4.1), no stats table (derived).

### 3.1 The `DailyEntry` model

One row per day, keyed by the São Paulo calendar `date`. Concrete Django:

```python
class DailyEntry(models.Model):
    date                 = models.DateField(primary_key=True)   # São Paulo calendar date (no time/tz)
    photo_path           = models.CharField(max_length=255)     # relative to the photos root
    word_target          = models.PositiveIntegerField()        # denormalized on purpose (see below)
    status               = models.CharField(max_length=12, default='picked',
                              choices=[('picked', 'picked'), ('submitted', 'submitted')])
    effective_word_count = models.PositiveIntegerField(null=True)  # = raw word count in v1 (§4.3)
    performance_pct      = models.FloatField(null=True)           # p in [0,1]
    revealed_tiles       = models.JSONField(null=True)            # list[int] ≤48 — the frozen truth
    picked_at            = models.DateTimeField()                 # tz-aware (UTC)
    submitted_at         = models.DateTimeField(null=True)
```

- **`date` is the primary key** (`DateField`, naturally unique, one row/day) — no auto `id`. The date is a *calendar date*, not a moment; "what day is it" is computed in São Paulo at the app layer (§8).
- **Submit-time fields are nullable** (`effective_word_count`, `performance_pct`, `revealed_tiles`, `submitted_at`) — null while `status='picked'`, set atomically on submit (§4.4).
- **`word_target` is denormalized** (derivable from tier): freezing it means retuning a tier later won't silently rewrite the bar past days were judged against (spec §9).
- **`performance_pct` is kept** even though derivable (`min(1, effective_word_count/word_target)`) — computed once at submit so gallery/stats reads need no math. It's the canonical **"% revealed"** the UI shows (calendar tint, gallery `pct`); the lit tiles `N` are its quantized visual (`N=round(p·48)`, so `N/48` ≈ `p`, may differ by one tile — `p` is the truth).
- **`revealed_tiles` = `JSONField`** holding `list[int]`. We only ever read the whole list (never query into it), so JSON beats a join table or CSV-in-text. Its integrity (≤48 unique valid indices, in reveal order) is **guaranteed by the reveal module (§4.2), not DB-enforced** — no check constraint needed.
- **Casing boundary:** DB + Python are `snake_case` (Django convention); the API layer (Django-Ninja schemas) aliases to `camelCase` for the FE-generated types (§2.6). One clean translation point.

> **Trimmed from spec §9 for v1:** `validationAttempts` and the `locked` status are dropped — with no validation gate (§4.3) nothing can fail. Both are **additive** later: add the field (default 0) and a `locked` choice. No migration of existing rows.

### 3.2 Not stored / derived

- **Not stored:** the submitted text, `tier_id` (derive from `photo_path`), `seed_tile` and `N`. `N = len(revealed_tiles)`; the seed is `revealed_tiles[0]` for submitted entries (it has Chebyshev distance 0 so it always sorts first) and `seed_for(date, photo_path)` for the live teaser (§4.1).
- **Unlocked set:** `SELECT photo_path WHERE status='submitted'`.
- **Daily offer:** pure function of `date` + folder contents (§4.1) — nothing stored.
- **Stats & gallery:** all aggregates derived from `DailyEntry` — no stats table.
- **Indexes:** the `date` PK is enough; the table is ~365 rows/year and the `status='submitted'` scans (unlocked set, gallery) are trivial. No extra indexes (don't add ceremony).

### 3.3 Photos on the filesystem

Three tier folders (`rascunho/ capitulo/ tese/`) under a configured **photos root**. A photo's identity **is its path** (relative to that root, e.g. `capitulo/manhã-no-arpoador.jpg`); tier = `dirname`. Curation = drop a JPG in a folder. No `Photo` table, no scan/sync, no admin UI. (spec §7, §9)

`photo_url = "/photos/" + quote(photo_path, safe="/")` — `urllib.parse.quote` with `safe="/"` so accents/spaces in each segment are percent-encoded **but the `/` separators survive** (a plain `urlencode`/`quote` without `safe` would emit `%2F` and break Caddy's path routing). The encoded path is built from the **raw** `photo_path` bytes (§4.0), so it matches the file on disk exactly.

> **Operational caveat — don't delete or rename a *won* photo.** Its `DailyEntry` pins the path; removing the file breaks that gallery image (the frozen tiles still render, but the source 404s). Curation is add-only for anything already in the gallery — worth stating, since "just drop/move files in folders" invites casual reorganizing.

### 3.4 The artifact, and the v1 backup decision

The SQLite `.db` is the **irreplaceable artifact** — and unlike the photos (reproducible from Leo's originals) and the code, the diary/streaks/earned tiles are **not reproducible** from anything else.

**v1 decision: no backups.** This is a toy (principle #5); we consciously accept that a disk loss loses Lu's history. Recorded as a deliberate omission, not an oversight.

> **Cheapest re-add when it's worth it:** turn on Lightsail automatic snapshots (whole-disk, zero script), or a nightly cron `sqlite3 app.db ".backup '…'"` shipped off-box via `rclone`. The artifact is tiny (KB–low MB). Pair with `PRAGMA journal_mode=WAL` if doing live online backups.

### 3.5 Schema mechanics

- **Migrations are the schema source of truth** — standard Django migrations; the §3.1 model is the canonical definition.
- **Settings (not tables):** the DB file path and the photos root are config/settings. Tier config (`name`, `word_target`, folder) lives in code constants (§8), not the DB.

---

## 4. Backend / domain logic

Mostly-pure functions over the date and the filesystem, plus one small write path (submit). This is where the spec's "hard requirements" (determinism, freeze) live. All numeric/grid constants below are **frozen contracts** — past `DailyEntry` rows are interpreted against them, so they must never change meaning.

### 4.0 Determinism substrate

Offer and reveal both derive from a stable hash. Python's builtin `hash()` is per-process salted and **must not** be used — it would make offers/seeds non-reproducible across restarts, breaking spec §1.4.

```python
import hashlib, unicodedata

def stable_hash(s: str) -> int:
    b = unicodedata.normalize("NFC", s).encode("utf-8")
    return int.from_bytes(hashlib.sha256(b).digest()[:8], "big")  # unsigned 64-bit
```

- **NFC normalization** before encoding, so accented filenames (`manhã`) hash identically regardless of how the filesystem hands us the bytes.
- **Canonical hash inputs** — pipe-delimited, fixed field order. Collision-safe because the first field is always a fixed-format date or an integer (neither can contain `|`), so the field boundary is unambiguous even if a filename contains `|`:
  - offer slot: `f"{date}|{tier_id}"` → `"2026-06-20|capitulo"`
  - reveal seed: `f"{date}|{photo_path}"` → `"2026-06-20|capitulo/manhã-no-arpoador.jpg"`
  - tile tie-break: `f"{tile_index}|{seed_tile}"` → `"27|21"`
- **`photoId` = the full relative `photoPath`** (tier folder included). It's already the photo's identity (§3.3).
- **Raw bytes are the identity; NFC is hash-only.** The `photo_path` stored on `DailyEntry`, the offer set-difference (`listdir − unlocked`, §4.1), and the served URL all use the **raw filesystem bytes** from `listdir` verbatim. NFC normalization is applied **only to a derived copy** inside `stable_hash` (and the B1 sort key) — never stored, never served, never compared. Why this split: macOS stores filenames NFD, Linux typically NFC; normalizing the *stored/served* path would (a) 404 the static lookup when disk bytes differ from the re-encoded URL, and (b) break the set-difference so an already-won photo could re-appear in the menu. Normalizing only the *hash input* keeps offer/seed/sort stable across OS differences (and across test machines) without touching identity. **Caveat:** this assumes `photo_path` is always stored from the same box that serves it (true — picks/submits happen on prod); don't copy a dev DB whose paths came from a differently-normalized disk onto prod.

### 4.1 Offer module

`computeOffer(date)` → 3 slots, one per tier. Deterministic per spec §1.4; recomputed only for today (past days are captured by their `DailyEntry`).

```text
unlocked = { photoPath : DailyEntry where status='submitted' }
for tier in [rascunho, capitulo, tese]:
    pool = [valid photo files in tier/] − unlocked        # see rules below
    pool = sorted(pool, key=NFC-normalized relative path)  # B1: stable order
    photoPath = pool[ stable_hash(f"{date}|{tier}") % len(pool) ]  if pool else None
    slot = None if photoPath is None else {
        tier, name, wordTarget,                 # tier config (§3 constants)
        photoUrl  = url_for(photoPath),         # FE-ready (§7 photo route)
        seedTile  = seed_for(date, photoPath),  # teaser tile — SAME seed fn as reveal (§4.2)
    }
return 3 slots
```

**Shared seed function (FE↔BE seam):** the teaser tile shown on the Menu and the reveal's seed are the *same* value — `seed_for(date, photoPath) = [20,21,26,27][ stable_hash(f"{date}|{photo_path}") % 4 ]` (§4.2 step 1). It's computed **server-side at offer time** and returned as `seedTile` so the client never hashes. Because it's a pure function of `(date, photoPath)`, the teaser tile and the eventual reveal's center always agree.

- **B1 — Pool ordering:** sort by NFC-normalized relative path ascending *before* the modulo, so the index is deterministic given fixed folder contents. (Adding a photo resorts the pool → the spec's "menu may reshuffle when you add a file" before pick.)
- **B2 — Valid photo file:** extension in `.jpg/.jpeg/.png` (case-insensitive); ignore dotfiles, subdirectories, and anything else (keeps `.DS_Store` etc. out).
- **B3 — Empty pool → `None`** ("sem foto hoje"). If *all three* slots are `None` (everything unlocked), the Menu shows a "collected everything" end state rather than an empty menu. Rare but defined.
- **B4 — In-progress pick is a no-op for the offer:** unlocked is `submitted`-only, and a `picked` day routes to the editor (never the menu), so the offer never needs to exclude today's own pick.

### 4.2 Reveal module

Computed **once** at submit; persisted as `revealedTiles`; the gallery never recomputes. The stored list *is* the frozen truth — immune to any later change in this algorithm, the grid, or the seed logic (a key correctness property to preserve and test). (spec §4, §9)

**Grid contract (frozen):** index `0–47`, row-major. `row = i // 6`, `col = i % 6`. 8 rows × 6 cols.

```text
 0  1  2  3  4  5
 6  7  8  9 10 11
12 13 14 15 16 17
18 19 [20][21]22 23     ← seed candidates = the inner 2×2:
24 25 [26][27]28 29        rows {3,4} × cols {2,3} = {20, 21, 26, 27}
30 31 32 33 34 35
36 37 38 39 40 41
42 43 44 45 46 47
```

1. **Seed** (C2): `seed = [20,21,26,27][ stable_hash(f"{date}|{photo_path}") % 4 ]`. Shown as the 1-tile teaser at pickup.
2. **Order all 48 tiles** (C3) by the tuple:
   1. `chebyshev(tile, seed)` = `max(|row−seed_row|, |col−seed_col|)` — nearest-first from a single seed ⇒ always a connected blob.
   2. `chebyshev_to_center` = `max(|row−3.5|, |col−2.5|)` — the geometric center sits *between* tiles (8 and 6 are both even), so the `.5` is just "the line between the two middle tiles." Pulls equidistant ties symmetrically inward so the blob stays centered.
   3. `stable_hash(f"{tile_index}|{seed}")` — final organic tie-break.
3. **Count** (C4): `N = max(1, round(p × 48))`, `p = min(1, effectiveWordCount / wordTarget)`. Uses Python's built-in `round()` (banker's / half-to-even) — deterministic, zero custom code; the half-to-even case only triggers at an exact `.5` and is cosmetically irrelevant (±1 tile ≈ 2%).
4. **Persist** (C6): `revealedTiles` = the first `N` tiles **in sorted order**. The Reveal screen replays that order as the one-time pop-in; the Gallery renders the same list statically. Order is part of the frozen truth (so `N = len(revealedTiles)`; neither `N` nor `seed` is stored separately).

### 4.3 Validation module (v1: word count only)

**Decision (v1 simplification, narrows spec §5):** no gate. Submission is just a **word count**.

- `wordCount = len(text.split())` — whitespace-separated tokens. Dead simple, matches the human notion of "number of words." No dedup, no gzip, no wordlist, no lorem check.
- `effectiveWordCount = wordCount` (the two concepts merge in v1 — there's no padding-neutralization step).
- Submit **always succeeds**: `p = min(1, wordCount / wordTarget)` → reveal → `status='submitted'`. There is no fail path.

**Consequences — these features are inert in v1:**
- No `locked` status (nothing can fail), no `validationAttempts`, no attempt cap, no retry loop.
- No failure/lockout copy, no "volta amanhã (no photo)" screen.

All of spec §5's heuristics (effective-count dedup, gzip ratio, pt-BR wordlist, lorem check) and the LLM check are **deferred**. The schema keeps room for them (see §3 ripple note) so re-introducing a gate later is additive, not a migration.

### 4.4 Submit orchestration (`POST /api/submit`)

Ties the modules together. Wrapped in a single DB transaction.

1. **Idempotency guard:** if today's entry is already `submitted`, return the existing result unchanged — never recompute or re-freeze. The freeze happens exactly once (protects the artifact against double-click / reload re-POST).
2. Otherwise: `wordCount` (§4.3) → `effectiveWordCount = wordCount` → `p = min(1, effectiveWordCount / entry.wordTarget)` (uses the **denormalized** `wordTarget` on the entry, §3) → reveal (§4.2) → store `revealedTiles`, `performancePct`, `effectiveWordCount`, `submittedAt` → `status='submitted'`.

No fail branch in v1.

---

## 5. API surface

API-only JSON via Django-Ninja (FastAPI-style, Pydantic, emits OpenAPI → TS codegen). Endpoint list only here; full request/response contracts, status codes, and error payloads are deferred to the API detail dive.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/config` | **Auth-exempt.** Public capability flags for the unauthenticated SPA (e.g. `{ devLogin: bool }`, §6.4). |
| `GET /api/today` | Current-day state for resume routing + today's offer if no entry yet. (Offer is folded in here — no separate offer endpoint.) |
| `POST /api/pick` | `{ tier }` → recompute today's offer, pin that slot's `photoPath` + `wordTarget`, create the `picked` entry. Idempotent (§5.1). |
| `POST /api/submit` | Submit text → count words → compute reveal & freeze (`status='submitted'`). Idempotent: already-submitted → returns existing result (§4.4). |
| `GET /api/gallery` | All `submitted` entries with their frozen `revealedTiles` for the trophy grid. |
| `GET /api/stats` | Derived aggregates: streaks, totals, current-month calendar tinting data. |

Auth (§6) applies to every endpoint **except `GET /api/config` and the DEBUG-only `POST /api/dev/login`** (§6.4), which must be reachable before sign-in.

### 5.1 Payload contract the frontend depends on

Full schemas are owned by the API detail dive, but these fields are **load-bearing for the FE** (§2.5–2.6) and constrain the backend, so they're fixed here:

- **`GET /api/today`** returns a discriminated state:
  - `none` → `offer`: 3 slots, each `{ tier, name, wordTarget, photoUrl, seedTile }` (or `null` for an empty pool → "sem foto hoje"). `seedTile` is server-computed (§4.1); the client never hashes.
  - `picked` → `{ photoPath, photoUrl, tier, name, wordTarget, seedTile }` to resume the Editor (teaser aside + progress target).
  - `submitted` → the frozen entry (below) to render **JáEntregue**.
- **`POST /api/pick`** `{ tier }` → the server **recomputes today's deterministic offer** (§4.1), takes that tier's slot, and pins its `photoPath`+`wordTarget` onto a new `picked` entry; returns the `picked` shape. Input is `{ tier }`, **not** a client-supplied `photoPath` (never trust the client to assert which photo — it could be stale or forged; the server is authoritative). **Guards:** if that tier's slot is `None` (empty pool), reject (the empty-pool TierCard is non-pickable). **Idempotency** (mirrors §4.4): if today already has a `picked` entry, return it unchanged (the pin is final — a different requested tier is rejected, not re-pinned); if already `submitted`, reject (day done).
- **`POST /api/submit`** `{ text }` → returns the frozen entry: `{ date, tier, name, wordTarget, effectiveWordCount, performancePct, photoUrl, revealedTiles }`. The Reveal screen animates `revealedTiles`.
- **`GET /api/gallery`** → list of frozen entries `{ date, tier, photoUrl, performancePct, effectiveWordCount, revealedTiles }`, plus `{ photosCollected, poolTotal }` for "N fotos · X% do acervo".
- **`GET /api/stats`** → `{ currentStreak, longestStreak, totalWords, daysDelivered, photosCollected, poolUnlockedPct }` + calendar data: per-day `{ date, performancePct }` and enough month metadata for the **real weekday offset + month length** (FE must not hard-code a 1→30 grid). **v1: the current month only** — no month navigation (frontend.md §9 shows a single static month; the "o ano de 2026" eyebrow is cosmetic).

**Invariant:** any payload that renders a Mosaic carries `photoUrl` + the tile list to light (`[seedTile]` for teasers, `revealedTiles` for reveals/frozen). The client renders those verbatim — no client-side hashing or reveal recomputation (spec §4).

---

## 6. Auth

Google sign-in via **django-allauth** (Google provider), no hand-rolled auth, no custom users table beyond allauth (spec §8). The design splits cleanly between a **production** path (real Google OAuth, locked to an email allowlist) and an **easy local-dev** path (no Google round-trip).

### 6.1 Provider & flow (production)

- The SignIn button is a **full-page redirect** to allauth's Google start URL (not `fetch`). After the Google callback, allauth sets the **session cookie** and redirects to `/`; `GET /api/today` then resolves the screen.
- Google emails arrive `email_verified` — trusted, no separate verification step.
- Logout → POST allauth logout → SignIn.

### 6.2 Allowlist — two layers, env-driven

`ALLOWED_EMAILS` is a setting read from env (comma-separated), shipping with **Lu's email + `leochatain@gmail.com`** (Leo, for testing). Same mechanism everywhere; prod just sets the env var. This replaces spec §8's single-email `if user.email != LU_EMAIL` with an allowlist membership check.

1. **Reject at login** — a custom allauth `SocialAccountAdapter.pre_social_login` blocks any non-allowlisted Google account *before* a Django user/session is created, so unauthorized accounts never come into existence.
2. **Guard every endpoint** — a Django-Ninja global auth callable: anonymous → **401**, authenticated-but-not-allowlisted → **403**. Defense in depth, and gives the SPA clean signals (`401 → SignIn`, `403 → "this isn't Lu"` copy, §2.1/§2.6). The only exemptions are the public `GET /api/config` and the DEBUG-only `POST /api/dev/login` (§5, §6.4).

### 6.3 Session transport & CSRF

- **Session cookie** (resolves the §10 transport question; matches frontend.md §10). SPA sends `credentials:'include'`. Same-origin (Caddy serves the SPA and proxies `/api`, §7), so cookies work with no CORS complications. No tokens in JS, no localStorage.
- **CSRF kept on** (Django default; cheap). Cookie-based sessions need it for `POST /api/pick|submit`: the client reads the `csrftoken` cookie and sends it back as `X-CSRFToken` (handled once in `api/client.ts`, §2.6). *(Per principle #1 we could exempt the API since there's one trusted user — decided to keep it; the plumbing is trivial.)*

### 6.4 Dev ergonomics — a DEBUG-gated bypass

The easy-dev answer: **don't require Google locally.**

- `POST /api/dev/login` is registered **only when `DEBUG and DEV_LOGIN_ENABLED`**, and logs in as a configured dev email from the allowlist — one click, no Google client, no OAuth secret needed locally.
- The SPA SignIn surfaces a "dev login" button only when that capability is advertised via the **auth-exempt** `GET /api/config` → `{ devLogin: true }` (§5). Both `GET /api/config` and `POST /api/dev/login` must be **excluded from the §6.2 global auth callable** — otherwise the unauthenticated SPA can't discover or use the bypass.
- **Hard prod guard:** the route is never registered unless `DEBUG` is true; additionally, refuse to boot if `DEV_LOGIN_ENABLED` is set while `DEBUG=False`. It cannot ship.
- Full Google OAuth still works in dev if desired (point a dev OAuth client at `localhost`), but it's not needed day-to-day.

### 6.5 Secrets (narrows spec §7)

Spec §7 says "no secrets in v1," but auth introduces real ones: **Google OAuth client ID + secret**, plus Django's **`DJANGO_SECRET_KEY`** (session/CSRF signing). All env-provided, never in the repo (full list in §7.4). Dev needs neither, thanks to §6.4. Recorded here since it's a departure from "none."

---

## 7. Stack & infra

Per spec §7. Summary:

| Concern | Decision |
|---------|----------|
| Host | AWS Lightsail, smallest instance |
| TLS / proxy | Caddy (auto HTTPS; serves SPA build, serves `/photos/*`, proxies `/api` + `/accounts`) |
| Backend | Django, API-only via Django-Ninja, gunicorn |
| Frontend | TS React + Vite (static build, baked into the Caddy image) |
| DB | SQLite, host bind-mount `./data/app.db` |
| Photos | Host `./photos`, bind-mounted read-only into both services |
| Secrets | `DJANGO_SECRET_KEY` + Google OAuth client ID/secret (env) — see §7.4 |
| Deploy | docker-compose: `caddy` + `web` (gunicorn). One command. |

### 7.1 Topology & deploy

**docker-compose** (over systemd) — `docker compose up -d --build` is the entire deploy; reproducibility is the only goal. Two services, no DB/redis/celery:
- **`caddy`** — auto-HTTPS; serves the SPA build, serves `/photos/*` static, reverse-proxies the dynamic prefixes to `web`.
- **`web`** — Django + gunicorn; runs `manage.py migrate` on start, then gunicorn (**2 workers** — ample for one user).

### 7.2 Caddy routing

Three dynamic prefixes go to Django, not just `/api` — **allauth lives at `/accounts/*`** (Google login/callback/logout). Everything else is the SPA, with an `index.html` fallback.

```caddyfile
{$DOMAIN} {
    encode gzip
    handle /api/*      { reverse_proxy web:8000 }
    handle /accounts/* { reverse_proxy web:8000 }   # allauth
    handle /photos/*   { root * /srv/photos; uri strip_prefix /photos; file_server }
    handle             { root * /srv/www; try_files {path} /index.html; file_server }
}
```

**Photo serving (FE↔BE seam):** the FE renders Mosaics from `photoUrl` (§5.1), and "frost" is a CSS overlay over the *full* image (§2.5) — the whole file is delivered to the browser. So `/photos/*` is plain static: `photo_url = "/photos/" + quote(photo_path, safe="/")` (§3.3) → `/photos/capitulo/manh%C3%A3-no-arpoador.jpg`, resolving to the raw on-disk path (§4.0). No signed URLs, no auth on the route — acceptable per principle #1 (the full image is exposed by design; gaming only cheats herself).

### 7.3 Images, mounts & persistence

- **`web/Dockerfile`** — Python + deps; entrypoint `migrate` then `gunicorn`. Django serves its own minimal static (allauth error pages) via **whitenoise** — no `/static/` Caddy mapping needed.
- **`caddy/Dockerfile`** — multi-stage: a `node` builder runs `vite build`, then `COPY --from=build dist → /srv/www` into the official `caddy` image. **SPA baked into the image** → one-command deploy, no Node on the server, no stale-build drift. (Chosen over bind-mounting `dist/`: the slower image build is irrelevant at toy deploy frequency; avoiding the manual "remember to rebuild" step is worth more.)
- **SQLite — host bind-mount `./data:/data`**, DB at `/data/app.db`. Bind-mount (not a named volume) so the irreplaceable artifact is a plain visible file: `cp ./data/app.db …` is your zero-effort manual rescue, which partly offsets having no backup job (§3.4). One-time `chown`/compose `user:` if host/container UIDs mismatch.
- **Photos — host `./photos`, bind-mounted read-only** into *both* services: `web` needs it for `listdir` at offer time (§4.1), `caddy` to serve it. `./photos:/srv/photos:ro`.
- Caddy's own `caddy_data`/`caddy_config` (certs) are named volumes.

### 7.4 Env & secrets

Env-provided (non-committed `.env`):
- **Secrets:** `DJANGO_SECRET_KEY` (session/CSRF signing) **and** Google OAuth client ID + secret. (This corrects §6.5's "one secret" — there are two secret categories; both via env, neither in the repo. Dev needs neither, thanks to §6.4.)
- **Config:** `ALLOWED_EMAILS` (§6.2), `DOMAIN`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS=https://{domain}`, `DATABASE_PATH`, `PHOTOS_ROOT`, `DEBUG=False`.
- **Behind-proxy settings:** `SECURE_PROXY_SSL_HEADER` (trust Caddy's `X-Forwarded-Proto`), `SESSION_COOKIE_SECURE=True`. SQLite `OPTIONS={'timeout': 20}` + WAL so a rare overlapping request never throws "database is locked."

### 7.5 Same-origin everywhere (no CORS)

- **Prod:** Caddy serves SPA + proxies the API on one domain → no CORS, cookies just work.
- **Dev:** the **Vite dev server proxies `/api` and `/accounts` to Django** (`localhost:8000`), so the SPA and API are same-origin in dev too. This is what lets the session cookie and the `/api/dev/login` bypass (§6.4) work locally without CORS/cookie pain. Dev = `runserver` + `vite dev` with `DEBUG=True`, `DEV_LOGIN_ENABLED=True`, local SQLite + a local `photos/` — no Docker, no Google.

### 7.6 Host setup (Lightsail)

DNS A record → Lightsail static IP; open ports 80/443 in the Lightsail firewall; Caddy provisions TLS via Let's Encrypt automatically. (No backup job in v1 — §3.4.)

---

## 8. Cross-cutting concerns

Collected here so each is decided once, not per-feature.

- **Time & dates:** all "today"/streak logic in America/São_Paulo; date is the `YYYY-MM-DD` PK. Single source for "what day is it" on the server. The entry's `date` is fixed at **pick** time. **Cross-midnight edge:** pick at 23:59 then submit at 00:01 keeps the entry on the *pick* day's date (the row is updated in place) — benign. If instead she picks but never submits before midnight, that prior-day `picked` row simply dangles: resume only ever queries *today*, and a `picked` (non-`submitted`) entry never consumed its photo (§3.2), so the photo just returns to the pool. No cleanup needed in v1.
- **Determinism:** offer and seed are `hash(date + …)`. Pin the hash function (stable across deploys) — a detail-dive decision with correctness implications.
- **Config vs. data:** tiers, grid (8×6), pool folder names are config constants, not tables (spec §3/§9).
- **Positive-only mechanics:** no punishment/lockout/shame; showing up always produces a reveal. v1 has no failure path at all (§4.3). (spec §1)
- **Error handling & copy:** API errors stay minimal given the single trusted user.

---

## 9. Testing strategy

High-level intent (expand later):

- **Determinism tests** (highest value): same `date` → same offer; same inputs → same `revealedTiles`; frozen entries unaffected by algorithm changes.
- **Word-count / `p` tests:** `wordCount = len(text.split())`; `p = min(1, wordCount/wordTarget)`; short entry → small-but-nonzero reveal; at/over target → full.
- **Reveal math tests:** `N` boundaries, Chebyshev ordering, tie-breaks, connectedness/centrality.
- **Resume routing tests:** each `status` → correct screen.

---

## 10. Open questions for this doc

Carried from spec §11 (cosmetic, pick sane defaults) plus a few architectural ones surfaced above, to resolve during detail dives:

*All architectural questions surfaced so far are resolved; what remains are the cosmetic spec §11 items (tier display names, editor styling, reveal-animation timing) — pick sane defaults, non-blocking.*

*(Resolved: backend dive — hash/determinism substrate, offer pool ordering, reveal seed/sort/tie-break, v1 word-count validation (§4). UI dive — pick commits on the explicit "Escolher" action (§2.4), offer folds into `GET /api/today` (§5.1). Storage dive — `revealedTiles` is a `JSONField`, no backups in v1 (§3). Auth dive — session cookie + CSRF, two-layer email allowlist, DEBUG-gated dev login (§6).)*
