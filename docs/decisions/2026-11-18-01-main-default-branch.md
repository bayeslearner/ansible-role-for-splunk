---
date: 2026-11-18
status: decided
decided_by: Kun
---

# Rename the lab branch to `main` and make it the default

## Context

The fork's GitHub default branch was `master`, which only mirrors `upstream/master`, so visitors saw upstream's role and none of the lab. The lab lived on `feature/virtual-lab`, 12 commits ahead of `upstream/master` and 0 behind.

## Decision

`feature/virtual-lab` is renamed to `main` on GitHub (the rename API, so links to the old name redirect) and `main` is the default branch. `master` stays equal to upstream so it remains a clean base for any upstream pull request. Merging the lab into `master` was rejected: it would break the mirror and gain nothing.

## Consequences and reversal

Other checkouts need `git branch -m feature/virtual-lab main && git fetch origin && git branch -u origin/main main`. Older log entries and decisions that name `feature/virtual-lab` are history and stay as written. Reversible with the same rename API and `gh repo edit --default-branch`.

The open question of work-host names in spec 05 and commit `2129c4f` is now more visible, since `main` is what visitors land on; it is tracked in the portfolio plan.
