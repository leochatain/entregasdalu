# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**entregasdalu** is a single-user web app that helps one person ("Lu") build a daily academic-writing habit. She picks a daily difficulty tier tied to a curated sentimental photo; her word count proportionally reveals tiles of that photo, which then **freezes** permanently into a gallery — an honest diary of effort.

**Current state: backend scaffolded and working; frontend in progress.** `backend/` implements the full v1 domain logic + API (offer, reveal, submit/freeze, auth, dev-login) with a green test suite — see "Backend commands" below. `frontend/` is a separate workstream. Read all three docs before building — they record *decisions already made and why* (including rejected alternatives), so the build doesn't re-open settled questions:

- **`spec.md`** — the what/why. Decisions + rejected alternatives + cross-cutting principles.
- **`design.md`** — architecture and the frontend↔backend contract. The authoritative source for data model, API surface, and domain logic.
- **`frontend.md`** — implementation-level FE plan: design tokens, CSS, per-screen pt-BR copy, component contracts. Its top note says **how to access/import the prototype**.
- **`prototype/`** — local mirror of the Claude Design prototype (DCLogic `.dc.html` — *reference only, not React*; see `prototype/README.md`). Treat it as a high-fidelity visual **guide, not a pixel-perfect spec**: aim for looks-good + well-coded, deviate where it yields cleaner code or better responsiveness; reuse the pt-BR **copy verbatim**. **`photos/{rascunho,capitulo,tese}/`** — tier folders with placeholder images (real curation = drop JPG/PNGs in).

When a doc conflict appears: **design.md's v1 simplifications win** over spec.md/frontend.md (which were written against the fuller spec). See "v1 scope" below.

## Guiding principles (from spec.md §1 — honor these; don't "harden" against them)

1. **The adversary is procrastination, not attackers.** One trusted user. Security/validation are intentionally light; mechanics are *positive-only* — no punishment, lockouts, or shame.
2. **Low-energy days still pay off.** The easy tier is trivially clearable and the reveal front-loads the meaningful (central) part of the photo.
3. **Photos freeze.** Once revealed to its earned %, a day's photo is locked there forever. This makes deterministic reveal (persisted tile list) a *hard requirement*.
4. **Daily offers are deterministic** — seeded by date so a refresh can't reroll the menu.
5. **It's a toy.** Prefer the simple option. Don't add infrastructure the scale (1 user, ~1 write/day) doesn't need.

## Planned stack

- **Backend:** Django, API-only (JSON) via **Django-Ninja** (emits OpenAPI → TS codegen). gunicorn.
- **Frontend:** TS React + **Vite** static build. **Tailwind v4**, driven by the design tokens via `@theme` (frontend.md §4) — bespoke look via token-mapped utilities, *not* Tailwind defaults; computed styles (Mosaic tiles, calendar tint) stay inline. **TanStack Query** for the ~5 endpoints.
- **DB:** SQLite — one table (`DailyEntry`), keyed by São Paulo calendar date.
- **Photos:** instance filesystem, three tier folders. A photo's identity *is its path*; no `Photo` table, no admin UI — curation = drop a JPG in a folder.
- **Auth:** django-allauth (Google), single-email allowlist. DEBUG-gated dev-login bypass so local dev needs no Google.
- **Infra:** AWS Lightsail + Caddy (auto-HTTPS; serves SPA, serves `/photos/*`, proxies `/api` + `/accounts`), docker-compose.

### Canonical repo layout (decided)

```text
entregasdalu/
├─ spec.md  design.md  frontend.md  CLAUDE.md
├─ prototype/                          # DCLogic visual reference (not shipped)
├─ photos/{rascunho,capitulo,tese}/    # PHOTOS_ROOT; bind-mounted :ro into web + caddy
├─ data/                               # SQLite app.db (gitignored + .gitkeep); bind-mounted
├─ backend/                            # Django (uv) = compose "web" service
│  ├─ pyproject.toml  uv.lock  manage.py  Dockerfile  .python-version
│  └─ <config project + DailyEntry app>
├─ frontend/                           # Vite SPA (see frontend.md §2 for src/ tree)
├─ caddy/                              # Caddyfile + Dockerfile (multi-stage: builds frontend → bakes into caddy image)
├─ docker-compose.yml                  # web: context ./backend · caddy: context . , dockerfile caddy/Dockerfile
└─ .env.example  .gitignore  .pre-commit-config.yaml  Makefile
```

- **Infra lives at root** (simplest build contexts for a toy — the caddy multi-stage must reach `frontend/`). The `Dockerfile` for the *web* service lives in `backend/`; "web" is only the compose service name (not a `web/` dir).
- **`data/` and `photos/` at root** so the same paths serve local dev (`DATABASE_PATH`/`PHOTOS_ROOT`) *and* the compose bind-mounts.
- Types flow backend OpenAPI → `frontend/src/api/generated.ts` (generated, do not hand-edit).

## Dev environment & tooling (backend installed; frontend per its own setup)

A clean, modern toolchain is a deliberate goal from the start. These choices are settled (backend pieces are installed and configured in `backend/pyproject.toml`):

- **Python: `uv`** for everything — dependency management, lockfile, and virtualenv. Deps live in `backend/pyproject.toml` with a committed `uv.lock`; no `requirements.txt`, no manual `venv`/`pip`. Run tools via `uv run …`.
- **Python lint + format: `ruff`** (both linter and formatter — don't add Black/isort/flake8). Config in `[tool.ruff]` in `pyproject.toml`.
- **Python types: `pyright`** in strict-ish mode (Django needs `django-stubs`). Config in `pyproject.toml` or `pyrightconfig.json`.
- **CSS: Tailwind v4** via `@tailwindcss/vite`, driven by `@theme` tokens (frontend.md §3–4). No CSS Modules.
- **TS lint: ESLint (flat config, `eslint.config.js`)** with `typescript-eslint`, `eslint-plugin-react-hooks`, and `eslint-plugin-jsx-a11y` (a11y matters per frontend.md §11). **TS format: Prettier** (`.prettierrc`) + `prettier-plugin-tailwindcss` (class sorting). Keep ESLint/Prettier in separate lanes — `eslint-config-prettier` to disable formatting rules in ESLint.
- **Git hooks: `pre-commit`** running ruff (lint + format), pyright, ESLint, and Prettier on staged files so nothing unformatted/untyped lands.
- **Tests:** `pytest` + `pytest-django` (backend); Vitest (frontend). Determinism tests are the priority (see "Testing priorities").

Decision log: `uv` over Poetry/pip-tools (fastest, modern, lockfile built in). ESLint+Prettier over Biome (chosen for the mature plugin ecosystem — react-hooks + jsx-a11y rules — over Biome's single-binary speed).

## Backend commands (scaffolded — these are real)

The backend lives in `backend/` (Django project `config`, single app `diary`) and is driven by `uv`. Run everything via `uv run …`. There is a repo-root `Makefile` with one-word targets (`make help` lists them); the underlying commands:

```bash
# from backend/  (or use `make <target>` from the repo root)
uv sync                                   # install deps + venv from uv.lock        (make install)
uv run python manage.py migrate           # apply migrations                         (make migrate)
uv run python manage.py makemigrations diary   # after a model change                (make makemigrations)
uv run pytest                             # full test suite (60 tests)               (make test)
uv run pytest diary/tests/test_reveal.py::test_seed_sorts_first   # a single test
uv run pytest -k offer                    # tests matching a keyword
uv run ruff check . && uv run ruff format .    # lint + format                       (make lint / make format)
uv run pyright                            # typecheck (strict-ish, basic mode)        (make typecheck)

# Run the app locally end-to-end (no Google, no secrets): DEBUG + dev-login bypass.
# `make dev` wraps this; or copy .env.example → .env (its dev block is ready to run).
DEBUG=True DEV_LOGIN_ENABLED=True ALLOWED_EMAILS=leochatain@gmail.com \
  DEV_LOGIN_EMAIL=leochatain@gmail.com uv run python manage.py runserver
# then: GET /api/config → POST /api/dev/login → /api/today → /api/pick → /api/submit → /api/gallery → /api/stats
# In DEBUG, Django also serves /photos/* so the loop works without Caddy.
```

- **Tests run under `config.test_settings`** (sets `DEBUG=True` + dev-login before importing base settings; pytest config sets `django_debug_mode=true` so the DEBUG-gated dev-login route is exercised). Determinism tests are the priority and live in `diary/tests/` (`test_hashing`, `test_reveal`, `test_offer`, plus `test_nfc` for raw-bytes/NFC).
- **OpenAPI** (FE codegen source): `make openapi` prints the schema; it's served at `/api/openapi.json` and `/api/docs`.
- **Pyright** is configured in basic ("strict-ish") mode — Django's dynamic ORM makes full strict impractical for a toy; basic + `reportUnnecessaryTypeIgnoreComment` keeps real signal.

### Backend layout (real)

```text
backend/
├─ pyproject.toml  uv.lock  manage.py  .python-version
├─ config/        settings.py · test_settings.py · urls.py · wsgi.py · asgi.py
└─ diary/         models.py (DailyEntry) · constants.py (frozen contracts + tiers) ·
                  hashing.py · offer.py · reveal.py · photos.py · timeutils.py ·
                  services.py (orchestration) · schemas.py (camelCase aliasing) ·
                  api.py (Ninja routes + auth) · adapters.py (allauth allowlist) ·
                  migrations/ · tests/
```

### Still to do (not backend)

- **`frontend/`** — Vite SPA (separate workstream): Tailwind v4 `@theme` tokens, ESLint/Prettier, TanStack Query, OpenAPI → `src/api/generated.ts` codegen.
- **Infra (later)** — docker-compose (caddy + gunicorn web), `backend/Dockerfile`, `caddy/Dockerfile` + Caddyfile, prod env. Deferred. (Root `.env.example`, `.gitignore`, `.pre-commit-config.yaml`, `Makefile` already exist.)

## Architecture: the core mental model

The backend is **mostly pure functions over the date and the filesystem**, plus one tiny table that freezes outcomes. Most complexity lives in the frontend interaction; the backend is deliberately thin.

- **`DailyEntry` is the only table** (design.md §3.1). No `Photo` table (identity = path), no offer table (pure function of date), no stats table (all aggregates derived). The SQLite `.db` is the **irreplaceable artifact** (the photos are reproducible from originals; the diary/streaks/earned tiles are not). v1 ships with **no backups** by deliberate decision.
- **The daily offer** is computed live from `(date, folder contents)` — recomputed only ever for *today*; past days are captured by their `DailyEntry`, so changing folder contents can never alter history.
- **The reveal is computed once at submit and persisted** as `revealed_tiles` (ordered `list[int]`, ≤48). The gallery renders that stored list verbatim and **never recomputes**. The stored tiles *are* the frozen truth — immune to any later change in the algorithm, grid, or seed logic.

### Frozen contracts — these must never change meaning

Past `DailyEntry` rows are interpreted against these constants. Changing them silently corrupts history.

- **Grid:** 8 rows × 6 cols = 48 tiles, row-major, `idx = row*6 + col`. App-wide constant.
- **Determinism substrate (design.md §4.0):** never use Python's builtin `hash()` (per-process salted). Use a stable SHA-256-based `stable_hash(s)` with **NFC normalization applied only to the hash input** — never to stored/served paths (raw filesystem bytes are the identity; this matters for macOS-NFD vs Linux-NFC). Canonical pipe-delimited hash inputs: offer slot `"{date}|{tier_id}"`, reveal seed `"{date}|{photo_path}"`, tile tie-break `"{tile_index}|{seed_tile}"`.
- **Seed tile:** one of the inner 2×2 `[20,21,26,27]`, chosen by `stable_hash("{date}|{photo_path}") % 4`. The *same* function (`seed_for`) produces both the Menu teaser tile and the reveal center — computed server-side and sent as `seedTile` so the **client never hashes**.
- **Reveal order:** sort all 48 tiles by `(chebyshev_to_seed, chebyshev_to_center, stable_hash("{tile}|{seed}"))`, take first `N = max(1, round(p*48))` where `p = min(1, effective_words / word_target)`. Nearest-first from a central seed → always a connected, centered blob.
- **Casing boundary:** DB + Python are `snake_case`; the Django-Ninja API layer aliases to `camelCase` for FE types. One clean translation point.

## v1 scope (important — design.md §4.3 narrows spec.md §5)

**v1 has NO validation gate.** Submit always succeeds: `word_count = len(text.split())`, `p = min(1, word_count / word_target)` → reveal → `status='submitted'`. There is no fail path.

Consequently these are **deferred / inert in v1** (the schema leaves room so re-adding is additive, not a migration):
- No `locked` status, no `validation_attempts`, no attempt cap, no retry loop.
- No LLM validation, no gzip/wordlist/dedup heuristics, no on-topic checks.
- **Frontend:** no `Lockout`/`VoltaAmanha` screens, no Editor fail state. **v1 ships 7 screens:** SignIn · Menu · Editor · Reveal · JáEntregue · Gallery · Stats. (frontend.md lists 9 from the prototype — ignore the two deferred ones.)

Submit is idempotent: an already-`submitted` day returns its existing result unchanged (the freeze happens exactly once — protects against double-click/reload re-POST).

## API surface (design.md §5)

All endpoints require auth except `GET /api/config` (public capability flags) and the DEBUG-only `POST /api/dev/login`.

| Endpoint | Purpose |
|---|---|
| `GET /api/today` | Day state for resume routing; folds in today's offer if no entry yet |
| `POST /api/pick` | `{ tier }` → recompute offer, pin `photo_path`+`word_target`, create `picked` entry (idempotent) |
| `POST /api/submit` | `{ text }` → count words, compute reveal, freeze (idempotent) |
| `GET /api/gallery` | All `submitted` entries with frozen `revealedTiles` |
| `GET /api/stats` | Derived streaks/totals + current-month calendar tinting |

`/api/pick` takes `{ tier }`, **never a client-supplied photo path** — the server is authoritative about which photo a tier maps to today. The app is **resume-first**: `GET /api/today` returns a discriminated state and the client routes to the matching screen (no react-router in v1 — a single state switch in `App.tsx`).

## Frontend↔backend seam: the Mosaic

The Mosaic is the highest-correctness component. Its one contract serves three modes — and **the client renders the server's tile list verbatim, keeping zero hashing/ordering logic** (the biggest divergence from the prototype, which fakes the backend locally):

```ts
interface MosaicProps { photoUrl: string; litTiles: number[]; animate?: boolean; }
```
- **Teaser** (Menu/Editor): `litTiles=[seedTile]`.
- **Animated reveal** (Reveal screen only): `litTiles=revealedTiles`, animated in array order.
- **Frozen** (Gallery/JáEntregue): `litTiles=revealedTiles`, static.

"Frost" is a CSS overlay over the *full* image, so the complete photo reaches the browser by design — acceptable per principle #1 (gaming only cheats herself). Photos are therefore plain static files under `/photos/*`, no auth/signed URLs.

## Time, dates, and operational caveats

- All "today"/streak logic is **America/São_Paulo**; `date` (`YYYY-MM-DD`) is the PK, fixed at *pick* time. A `picked` row that never submits before midnight simply dangles (resume only queries today; its photo returns to the pool). No cleanup needed.
- **Never delete or rename a *won* photo** — its `DailyEntry` pins the path; removing the file 404s that gallery image. Curation is add-only for anything already in the gallery.

## Testing priorities (design.md §9)

Highest-value first: **determinism** (same date → same offer; same inputs → same `revealedTiles`; frozen entries unaffected by later algorithm changes), then word-count/`p` math, reveal math (`N` boundaries, Chebyshev ordering, tie-breaks, connectedness/centrality), then resume routing (each `status` → correct screen).
