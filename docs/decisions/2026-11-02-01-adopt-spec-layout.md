---
date: 2026-11-02
status: decided
decided_by: the agent; the owner may reverse
---

# Adopt the spec-driven layout and reconnect git

## Context

On 2026-11-02 the Dropbox checkout `~/Dropbox/Projects/ansible-role-for-splunk` had no `.git`, no `CLAUDE.md` and no `docs/`. Its only spec was an uncommitted Kiro requirements file, `.kiro/specs/day-2-operations/requirements.md`. Kun asked to adopt the current skills and Project Board and to study the Molecule harness after the fact.

## What was checked

- The tree matched `origin/feature/virtual-lab` at `55426a6` except `.gitignore` (two added lines) and the Kiro file (compared with a temporary index, no files changed).
- The fork reports a move from `kundeng/` to `bayeslearner/ansible-role-for-splunk`.
- `upstream/master` is 24 commits ahead of the harness merge `555beec` (role changes #261–#268).

## Decision

1. Git metadata lives at `~/.local/share/project-git/ansible-role-for-splunk.git` with a `.git` pointer file in the tree, the layout every project on this Mac uses (`house-facts`, Dropbox and git). Branch `feature/virtual-lab` tracks the fork; `upstream` points at `splunk/ansible-role-for-splunk`.
2. Specs live in `docs/specs/`. The harness as built becomes a reconstructed, CLOSED spec `05-molecule-virtual-lab`; the Kiro file becomes `10-day-2-operations` (DRAFT), content unchanged.
3. Steering in `docs/steering/product.md`, decisions here, the feature matrix in `docs/design/feature-matrix.md`.

## Consequences and reversal

All reversible by moving files back; nothing on the remote changed except commit `6ff020f` (`.gitignore`). `origin`'s URL still names `kundeng/`; updating it to `bayeslearner/` was refused by the session's permission check and is left to Kun.
