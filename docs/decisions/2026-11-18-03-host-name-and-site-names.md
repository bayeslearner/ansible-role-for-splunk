---
date: 2026-11-18
status: open
---

# A host name in a public repository, and the indexer site names

Two questions only the owner can answer. Neither blocks the work in progress.

## Question 1: may the pre-production host's name stay in this public repository?

- **Why now:** `main` is now the default branch of a public repository, so its files and commit subjects are what a visitor sees. The project's own rule is that facts about work hosts stay out of this repository.
- **What was checked:** `rg` on `main` finds the pre-production host's name in five files (`CLAUDE.md`, `docs/steering/product.md`, and the three files of spec 05), and `git log` shows it in the subject of commit `2129c4f`. The names `splunkapp-prod01` and `splunkapp-prod02` are lab container names and are also in upstream's repository, so they are not part of this question.
- **Which owner-only category:** publishing something outward.

| Option | Consequence | Reversal |
|---|---|---|
| The name is fine in public | Nothing changes | none needed |
| Remove it from the files only | The five files say "the pre-production host"; the name stays in history and in one commit subject | restore the text |
| Remove it from files and history (recommended if it is a work machine) | The commits on `main` since upstream are rewritten and force-pushed; every clone must be re-fetched; the name is gone from the default branch | none: a rewrite of public history cannot be undone cleanly |

**Recommendation:** if the name identifies a work machine, the third option, done once and before the repository is promoted. If it does not, the first.

**Meanwhile:** new text written since 2026-11-18 says "the pre-production host" without the name.

## Question 2: should the indexer site names come back as a planned item?

- **Why now:** on 2026-11-18 the agent removed `splunk_idxc_site: site1 / site2` and the `indexer_site1` and `indexer_site2` groups from `prod`'s inventory (commit `a6bb639`) without asking first. They were part of the owner's earlier design.
- **What was checked:** nothing in the role, the upstream playbooks or the lab read those names (`rg` over `roles/`, `playbooks/`, `environments/`, `testing/molecule/`). The role's cluster-manager task sets no multisite options, so the cluster day0 forms is single-site.
- **Which owner-only category:** product direction (whether the lab should model a multisite cluster).

| Option | Consequence | Reversal |
|---|---|---|
| Leave them removed (recommended) | The inventory names only what the lab builds; multisite is not a goal | restore from `a6bb639^` |
| Restore them and add a task | The names return with a spec task to form a two-site cluster; the role has no multisite support, so the lab would set those options itself | remove again |

**Recommendation:** leave them removed until the role or the lab can form a multisite cluster.

**Meanwhile:** they stay removed.

## Answers

None yet.
