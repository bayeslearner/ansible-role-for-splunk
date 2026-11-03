# CLAUDE.md — ansible-role-for-splunk (fork) and its virtual lab

## Project

A fork of `splunk/ansible-role-for-splunk` plus the virtual lab under `testing/`: a Docker and Molecule harness that builds multi-node Splunk topologies and deploys them with this role over SSH. Development mode: maintain code, specs, tasks, the feature matrix and verification evidence. Purpose, audience, where the lab runs, invariants and pillars: `docs/steering/product.md`.

specs_root: docs/specs

## Skills

Load at session start (also listed in `.claude/required-skills`): `house-rules`, `work-discipline`, `spec-driven-dev`. Load `house-facts` before touching a host (the pve2 VM, `splunkapp-preprod01`, Docker) and `splunk-platform` for Splunk configuration questions.

## The board

- Board: https://claude.ai/artifact/WCbneMKxdKJJuiWAfcXAo2 (kit config in `docs/board/`; reseed with `python3 docs/board/seed.py --out .build/board`, republish the page with `python3 docs/board/seed.py page --out board/board.html`)
- Notes Viewer (ansible-role-for-splunk): https://claude.ai/artifact/LES4pcfC7J9giupJGLE6D2
- Spec 05 review and Molecule teaching doc (Claude Doc): https://claude.ai/artifact/EbJy948pCFVvGPkZHtQBoP

## Required reading on session start

1. This file, then `docs/steering/product.md`.
2. `docs/design/feature-matrix.md` — what the lab does, per component, and how it was verified.
3. The ACTIVE spec under `docs/specs/` (lowest-numbered non-CLOSED spec when none is ACTIVE).
4. `docs/decisions/` — the decision timeline.
5. `testing/README.md` — how the lab is operated.
6. `git log --oneline -10` on `feature/virtual-lab`, and `git log --oneline origin/feature/virtual-lab..upstream/master` for upstream role changes not yet tested in the lab.

## Git

- Work branch: `feature/virtual-lab`. `master` mirrors `upstream/master`. `archive/docker-molecule-testing-v1` is frozen history; never rewrite it.
- Git metadata lives outside Dropbox at `~/.local/share/project-git/ansible-role-for-splunk.git` (this checkout's `.git` is a pointer file). Other machines need their own.
- Remotes: `origin` = the fork, `upstream` = `splunk/ansible-role-for-splunk`.
- Commit trailers: `Spec:`, `Task:`, `Issue:`, `Evidence:` (`spec-driven-dev`, Evidence Anchors).

## Commands

Run from `testing/`; `task --list` shows all.

```bash
task setup                         # secrets, images, Splunk downloads, network, runner
task workflow:full                 # infra + day0 + day1 + destroy
task workflow:quick                # infra + day0, keeps containers
MOLECULE_ENV=prod task infra:test  # pick a topology: small (default), prod, dev
task shell -- ansible-controller   # operate the lab from the controller
task reset                         # remove containers, test volumes and network
```

Lint (repo root): `pre-commit run --all-files` (yamllint, ansible-lint on `roles/ playbooks/ environments/`). Spec lint: `python3 scripts/spec_lint.py`.

## Layout

- `roles/splunk/` — the role (upstream-owned; changes here go upstream when general).
- `playbooks/`, `environments/` — upstream examples.
- `testing/` — the virtual lab: `Taskfile.yml`, `docker-images/`, `molecule/{infra,day0,day1,environments}`, `software/` (downloaded tarballs, ignored), `.secrets/` (generated, ignored).
- `docs/` — map in `docs/README.md`.

## What to maintain

- Spec task marks and Logs as work lands; `docs/design/feature-matrix.md` in the same commit as any change to a lab capability.
- `testing/README.md` when a Taskfile target, topology or controller workflow changes.
- A decision file in `docs/decisions/` for every decision; owner questions go there and on the Board.
- Findings: tasks in the ACTIVE spec. The fork has GitHub Issues disabled.
- 🚨 The fork is a public repository. Facts about work hosts (FQDNs, networks, users, internal paths, security posture of a named host) go in the private work notes, never in this repo.

## Not in this file

Status, task tables, handoffs and run logs belong in the specs, `docs/history/` and the Board.
