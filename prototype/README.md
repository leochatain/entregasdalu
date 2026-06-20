# prototype/ — visual reference (do not ship)

A local mirror of the Claude Design project **"Entregasdalu writing tool"**
(`claude.ai/design/p/c61adf3e-6a40-47c8-b2cd-1380bf166f45`), the pixel-accurate visual
source of truth referenced throughout [frontend.md](../frontend.md).

- **`Entregasdalu.dc.html`** — all 9 prototype screens (markup + DCLogic component logic + pt-BR copy).
- **`Mosaic.dc.html`** — the mosaic reveal component (grid/slice math, seed ordering, frost animation).
- **`support.js`** — the DCLogic runtime that renders `.dc.html` in a browser (generated; do not edit).

## How to use it

This is **reference only — not application code.** `.dc.html` is DCLogic (a single-file React-ish
toy), **not** the production React/Vite SPA. Read it to match layout, spacing, copy, and motion;
**reimplement** in the real stack per [frontend.md](../frontend.md) and [design.md](../design.md).

Key production divergences are already enumerated in frontend.md §12 — most importantly: the Mosaic
renders the server's frozen `litTiles` verbatim (the prototype fakes the backend by hashing/ordering
client-side), validation is server-side (v1: word-count only), and only **7** of these 9 screens ship
in v1 (no Lockout / VoltaAmanhã — see CLAUDE.md "v1 scope").

## Provenance / fidelity

`Entregasdalu.dc.html` and `Mosaic.dc.html` were reconstructed from the design project's content
during planning. If anything looks off, the **canonical source is the Claude Design project** —
re-import via the `claude_design` MCP connector (`/design-login` for scopes; see frontend.md's top note).
The project also holds `photos/` (sample images) and `screenshots/` (rendered reference PNGs) not mirrored here.
