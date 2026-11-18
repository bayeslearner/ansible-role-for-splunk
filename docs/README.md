# Documentation map

| Location | Holds |
|---|---|
| `docs/steering/` | Stable intent: `product.md` (purpose, where the lab runs, invariants, pillars) |
| `docs/specs/` | Ordered sprints, numbered in gaps of 5: `05-molecule-virtual-lab` (the harness as built, reconstructed), `10-day-2-operations` |
| `docs/design/` | Accepted cross-cutting design; `feature-matrix.md` is the living map of lab capabilities |
| `docs/decisions/` | Every decision file, dated; `README.md` indexes them |
| `docs/history/` | Dated reviews, research, verification records and handoffs (`<kind>-<YYYY-MM-DD>-<topic>`) |
| `docs/diagrams/` | Diagram sketches: each `<name>.jsx` module is the source and `<name>.svg` is rendered from it (`bun ~/.claude/skills/diagram-sketches/scripts/widget_svgs.tsx docs/diagrams`); never edit the `.svg` by hand |
| `docs/board/` | The Board's configuration and seed (`board.json`, `orientation.md`, `seed.py`); the Board itself is a Claude Doc generated from the repo |
| `docs/guides/` | Operator guides beyond `testing/README.md`, when needed |
| `testing/README.md` | How to run and operate the virtual lab |
| `README.md` (root) | Opens with what the fork is (the role plus the lab), the lab map and the quick start; below that, upstream's role documentation as upstream ships it |
