# entregasdalu — frontend

TS React + Vite SPA. Tailwind v4 (driven by `@theme` design tokens in
`src/index.css`, **not** Tailwind defaults), TanStack Query over the ~5 API
endpoints. See `../frontend.md` for the full implementation plan and
`../CLAUDE.md` for architecture.

**Current state:** tooling scaffold only — no screens/components/API yet.
`src/App.tsx` renders a single token-styled placeholder.

## Commands

```sh
npm install        # first time
npm run dev        # Vite dev server (proxies /api, /accounts, /photos → :8000)
npm run build      # tsc -b + vite build → dist/
npm run preview    # serve the production build
npm run lint       # ESLint (flat config: typescript-eslint + react-hooks + jsx-a11y)
npm run format     # Prettier (+ prettier-plugin-tailwindcss class sorting)
npm run typecheck  # tsc -b --noEmit
npm run gen:api    # regenerate src/api/generated.ts from the backend OpenAPI (needs backend on :8000)
```

## Layout

`src/` follows frontend.md §2: `api/` (client, hooks, generated types),
`state/`, `components/` (incl. `Mosaic/`), `screens/`, `lib/`. Most are empty
placeholders for now.

## Note on `package.json` → `overrides`

Everything is on its latest version. Two packages just haven't widened their
declared **peer ranges** to the brand-new eslint 10 / TS 6 yet, though both work:
`eslint-plugin-jsx-a11y@6.10` (declares eslint ≤9) and `openapi-typescript@7`
(declares typescript ^5). The scoped `overrides` block pins each to our installed
version (`$eslint` / `$typescript`) so `npm install` resolves **strictly** — no
`legacy-peer-deps`, no global leniency. Remove an entry once its package widens
its range upstream.

`npm audit` reports 2 moderate vulns: a transitive `js-yaml` DoS pulled in by
`openapi-typescript`'s OpenAPI parser. It's a dev-only codegen tool that reads
our own backend schema (trusted input) and ships nothing to the browser, so it's
left until `openapi-typescript` bumps its dependency.
