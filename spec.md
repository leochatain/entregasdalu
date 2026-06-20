# entregasdalu — v1 Spec & Decision Log

A single-user web app that helps **Lu** study and ship her masters *entregas* (deliverables). She picks a daily goal tied to a curated, sentimental photo; her writing output proportionally reveals tiles of that photo, which freezes into a gallery.

> This document records **decisions already made and why**, including rejected alternatives, so the build doesn't re-open settled questions. Where something is intentionally deferred or cosmetic, it's marked as such — treat those as non-blocking.

---

## 1. Cross-cutting design principles

These shaped most decisions below. Honor them; don't violate them for "robustness."

1. **The adversary is procrastination, not attackers.** One trusted user. Keep security light, validation light, and mechanics *positive-only* — no punishment, no lockouts, no shame. Validation exists to make the unlock feel *earned*, not to police.
2. **Low-energy days must still pay off.** The easy tier is genuinely easy, and the reveal front-loads the meaningful part of the photo, so showing up always produces something satisfying.
3. **Photos freeze.** Once a day's photo is revealed to its earned %, it's locked there forever. The gallery is therefore an honest *diary of effort*. This makes deterministic reveal (persisted seed + tile count) a hard requirement.
4. **Daily offers are deterministic.** Seeded by date so a refresh can't reroll the menu.
5. **It's a toy.** Prefer the simple option. Don't add infrastructure the scale doesn't need.

---

## 2. Core loop

1. Lu opens the app (Google sign-in, only her email allowed).
2. She sees **today's menu**: 3 squares, one per difficulty tier, each a *different curated photo* shown as a teaser (one central tile revealed). Each square is labeled with its word target.
3. She **picks one tier/photo** — the one she wants to unlock today. (Pick is soft until she starts writing, then committed.)
4. She pastes the day's writing into a clean editor with a live word-count progress bar toward the chosen target.
5. On **submit**: local validation gates the text (is it real writing?). If it passes, performance `p = effective_words / target` (capped at 1) determines how many photo tiles reveal, expanding outward from a central seed. The photo **freezes** at that %.
6. Streak updates; the day **locks** until tomorrow (one submission per day).

Unpicked photos stay in their pools and may resurface another day (they're simply never recorded). The picked photo is now in a submitted `DailyEntry`, so it's excluded from future offers and lives in the gallery at its frozen %.

---

## 3. Difficulty tiers

**Decision:** 3 tiers (down from an earlier 4–5). Each tier has **its own curated photo pool**.

**Word targets — "Forgiving" set chosen. Names: Rascunho · Capítulo · Tese** (the photo lives in the folder named by `tier id`):

| tier id (= folder) | display name | word target |
|---------|-------------|-------------|
| `rascunho` | Rascunho | 150 |
| `capitulo` | Capítulo | 400 |
| `tese`     | Tese     | 800 |

- **Why this set:** the floor must be trivially clearable. Proportional reveal + principle #2 mean even a 150-word day must yield real photo. A floor she can't hit on a bad day kills the habit. Easy to raise later once her pace is known.
- **Rejected:** *Standard* (250/600/1200) and *Demanding* (500/1000/1800) — kept as future presets, too high to start.
- **Names** (draft → chapter → thesis) mirror her actual journey; *Tese* is the thing she's working toward. Still trivially changeable, but this is the chosen default.
- **Whether harder tiers hold "better" photos is pure curation**, not enforced by the app. The app treats all pools equally.

---

## 4. Reveal mechanic

**Decision:** discrete **mosaic fill**, expanding from a central seed, no partial tiles.

- **Grid:** vertical photos, **8 rows × 6 cols = 48 tiles** (app-wide constant, not per-photo).
- **Seed tile:** randomly chosen from the **central tiles** (the inner 2×2 block), seeded by `hash(date + photoId)` so it's stable. Shown as the teaser at pickup (1 tile ≈ 2%).
- **Tiles to reveal:** `N = max(1, round(p × 48))`, where `p = min(1, effective_words / target)`.
- **Which tiles:** sort all 48 tiles by distance from the seed; reveal the **nearest N**. Nearest-first from a single seed is always a connected blob, and a central seed keeps it central.
  - Distance metric: **Chebyshev** (square-ish "expanding crop"). *Rejected:* Manhattan (diamond/vignette) — fine but less crop-like; growing circle — prettier but raggy on a grid and more math.
  - Tie-break order (for stable freeze + organic animation): Chebyshev distance to seed → distance to grid center → `hash(tileIndex + seed)`.
- **No partial tiles.** Purely shown/hidden. ~2% granularity is smooth enough and removes all canvas masking.
- **Animation:** tiles pop in one-by-one up to N, in the tie-break order above.

**Persistence (the freeze):** at submit, compute the ordered reveal once (seed → nearest `N`), then **store the resulting ordered list of lit tile indices** (`revealedTiles`, ≤48) on the `DailyEntry`. The gallery renders that list directly — no recompute. This makes the frozen photo immune to any later change in the reveal algorithm, grid, or seed logic: the stored tiles *are* the truth. (`seedTile`/`N` don't need persisting — `N = len(revealedTiles)`.)

**Implementation note:** a CSS grid of 48 elements, each showing its slice of the full image via `background-position`; toggle visibility per tile. No canvas needed.

---

## 5. Validation (v1: local only, no LLM)

**Decision:** ship local heuristics; defer the Anthropic LLM check.

Gate the submission (binary: is this real writing?) on:

1. **Effective word count** — dedup repeated sentences/paragraphs *first*, so padding can't inflate the count. The dedup ratio (unique ÷ total sentences) is itself a padding signal. The effective count drives `p`.
2. **gzip/zlib compression ratio** — repeated filler and `asdf asdf asdf` compress to almost nothing; real Portuguese prose lands in a normal band. Flag if too compressible.
3. **Real-word fraction** vs a small bundled **pt-BR wordlist**, lenient threshold (~60%) so jargon, citations, author names, and English terms don't trip it; catches keyboard mashing.
4. **Literal lorem-ipsum** token check.

If the gate passes → compute `p` → reveal, `status='submitted'`. If it fails → `validationAttempts += 1`, show a playful message, let her retry.

**Attempt cap:** default **3 failed attempts/day**. On the cap, the day goes `locked` (no photo, no delivery, breaks the streak) with a lighthearted "clearly not today" message. Safe to be this blunt because — per the gate logic above — a *genuine* entry never fails (short ≠ gibberish; it just earns fewer tiles), so the cap only ever catches deliberate junk. The cap value is config; the escalating copy is UI (see §11).

**Explicitly NOT in v1 (don't add, don't ask):**
- **AI-generated-text detection** — unreliable, false-positive-prone on real prose. And gaming it only cheats herself out of an earned reveal.
- **On-topic / thesis-relevance check** — deferred; adds friction and false negatives. (Future option: she sets a thesis topic once and an LLM checks plausibility.)
- **Anthropic LLM validation** — deferred. When added, it would also generate a warm encouraging line; key stays **server-side only**.

All of the above is Python stdlib-ish (`zlib` + a wordlist file). **No server secrets in v1.**

---

## 6. Gallery & stats

**Decision:** trophy grid primary, calendar as the stats screen.

- **Gallery — trophy grid:** dense wall of frozen mosaics (each at its earned %). Tap to enlarge and see that day's date / tier / word count. Because photos freeze, this *is* the effort diary. *Rejected as primary:* pure chronological timeline (kept as the tap-expand detail), tier-shelves view.
- **Stats — calendar:** month grid, each day tinted by its reveal %; doubles as a streak heatmap.
- **Stat values** (all derived from `DailyEntry`, no separate table): current/longest **streak**, total words written, days delivered, photos collected (count + % of total pool unlocked).
- **Streak rule (v1):** consecutive calendar days (America/São_Paulo) with a submitted entry; a missed day resets to 0. Simplest; revisit later if demotivating.

---

## 7. Stack

| Concern | Decision | Why / tradeoff |
|--------|----------|----------------|
| Host | **AWS Lightsail**, smallest instance ($5–7/mo) | Flat pricing, full control; wildly overkill-comfortable for 1 user. |
| TLS / proxy | **Caddy** | Automatic HTTPS, near-zero config. Serves the React static build **and** reverse-proxies `/api` to Django. |
| Backend | **Django**, API-only (JSON) via **Django-Ninja** | FastAPI-style, Pydantic, emits OpenAPI → codegen TS types for the client. *Rejected:* DRF (more boilerplate for this size). |
| Frontend | **TS React**, built with **Vite** | Real interactivity (mosaic reveal, editor, gallery) justifies React. |
| DB | **SQLite** | 1 user, ~1 write/day. Postgres is pure ceremony here. Lives on the box; back up the `.db` nightly (`sqlite3 .backup`) off-box. |
| Photos | **Instance filesystem**, 3 tier folders (`tier1/ tier2/ tier3/`) | Toy-scale. Originals live on Leo's machine → reproducible, so they're *not* the irreplaceable artifact. *Rejected for v1:* S3/object storage + signed URLs (unnecessary). |
| Secrets | **None in v1** | No LLM key; auth via allauth. |
| Deploy | docker-compose (Caddy + gunicorn Django + SQLite volume) or systemd | Either; reproducibility is the only goal. |

**The irreplaceable artifact is the SQLite `.db`** (her diary, streaks, earned tiles). Back that up; the photo files are reproducible from Leo's originals.

**Curation workflow:** drop a JPG into the right tier folder — that's the entire registration step. No `Photo` table, no scan, no admin UI. The app reads the folder at offer-time; unlock state is derived from `DailyEntry`.

---

## 8. Auth

**Decision:** Google sign-in via **django-allauth** (Google provider). Single allowlisted email — every protected view checks `if user.email != LU_EMAIL: 403`. No users table needed beyond what allauth provides. Don't hand-roll. (Justified by principle #1.)

---

## 9. Data model

**The whole model is ONE table + the filesystem.** No `Photo` table (identity is the path), no `DailyOffer` table (it's a pure function of the date).

Constants (config, not tables): tiers `[{id, name, wordTarget}]` (see §3); grid `rows=8, cols=6`; pool folders `rascunho/ capitulo/ tese/`.

Photos: just files. A photo's identity is its **path** — `capitulo/manhã-no-arpoador.jpg`. Tier = `dirname(path)`. No DB rows; no scan/sync step.

```
DailyEntry          # the ONLY table; one row per day once she picks
  date              # PRIMARY KEY, UNIQUE, America/São_Paulo (YYYY-MM-DD)
  photoPath         # identity of the chosen photo; tier = dirname(photoPath)
  wordTarget        # DENORMALIZED on purpose (see note) — not derived at read time
  status            # 'picked' | 'submitted' | 'locked'
  validationAttempts  # int; +1 per FAILED submit. At the cap (default 3) → status 'locked'
  effectiveWordCount  # set on a passing submit
  performancePct    # p = min(1, effectiveWordCount / wordTarget)
  revealedTiles     # ordered list of lit tile indices (≤48) — the frozen truth,
                    #   computed once at submit (seed → nearest N), then never recomputed
  pickedAt
  submittedAt       # null unless status='submitted'

# status: picked = in progress · submitted = delivered (consumes the photo)
#         locked  = hit the attempt cap, day spent, NO photo consumed
# Unlocked set:  SELECT photoPath FROM DailyEntry WHERE status='submitted'
#   → a 'locked' day's photo was never won, so it stays available for future offers
# We deliberately DON'T store: the submitted text, or per-failure reasons.
# Stats & gallery: derived from DailyEntry. No stats table.
# No users table (single allowlisted Google account).
```

- **Why `wordTarget` is stored, not derived:** it's derivable from the tier, but denormalizing it means retuning a tier's target later won't silently rewrite the bar past days were judged against.
- **`tierId` is intentionally absent:** derive it from `photoPath` when needed.

**Offer (computed live, nothing stored):**
```
computeOffer(date):
  unlocked = { photoPath : submitted DailyEntries }
  for tier in [rascunho, capitulo, tese]:
    pool = listdir(tier/) − unlocked
    slot = pool[ hash(date + tier) % len(pool) ]  if pool else None  # None → "sem foto hoje"
  return 3 slots
```
- Recomputed only ever for **today** — past days are captured by their `DailyEntry`, so changing folder contents can never alter history.
- Before she picks, the menu may reshuffle if the folder changes (e.g. you add a photo) — that's fine, it just shows a different nice photo. Once she picks, `photoPath` is pinned on the entry and stays fixed.
- Resume logic on load: today's entry `submitted` → reveal/locked screen; `locked` → "volta amanhã" screen (no photo); `picked` → resume writing for `photoPath`; no entry → show the computed menu.

**Reveal computation (once, at submit):** sort the 48 tiles by `(chebyshev(tile, seed), chebyshev(tile, center), hash(tile+seed))`, take the first `N = max(1, round(p*48))`, and save that ordered list as `revealedTiles`. The gallery never recomputes — it just lights the stored tiles.

---

## 10. Deferred / explicitly out of scope for v1

So the build doesn't add or ask about these:

- **Pomodoro / time-tracking mode** — cut from v1 (was in the original idea).
- **LLM validation** + encouraging-message generation — deferred (§5).
- **On-topic / thesis-relevance** checking — deferred.
- **Overflow-carry / completing a partial photo later** — NO. Photos freeze permanently at the earned %. (Future "more functionality.")
- **Object storage / signed URLs** — FS only for v1.
- **Admin UI for photos** — none; curation is dropping files in folders.
- **Multi-user anything** — single user, hard-coded allowlist.

## 11. Still open (cosmetic / non-blocking — pick a sane default, don't stall)

- Tier display names (default Leve/Firme/Cheio).
- Exact "pretty editor" styling and reveal-animation timing/easing.
- The failed-attempt cap value (default 3) and the escalating playful copy shown on each failure / on lockout.