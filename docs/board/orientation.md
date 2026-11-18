# Board orientation

The Board's "Where we are" panel, read by `docs/board/seed.py`. Redraw it when a spec closes, the direction changes or a big decision lands.

## Here

The lab runs and checks itself on all four topologies. `prod`, the largest, ran end to end on 2026-11-18 on a second Mac with its own container engine: eleven containers, a two-peer indexer cluster and a two-member search head cluster formed in one lab, day1, and a clean teardown. It took 35 GB of engine disk and about 6.5 GiB of memory with no data. The work Mac's shared disk filled during earlier attempts, so no Splunk installs run there.

- **Spec 05, the virtual lab as built: ACTIVE.** Reconstructed from the code on 2026-11-02. Its review (the "Review of spec 05" tab) awaits your sign-off. It first ran on 2026-11-10 and 11-11, on the pre-production host, as the one-node `dms` topology.
- **Upstream merged.** `upstream/master` (`750c071`) is merged into the lab branch, now `main` and the fork's default branch. Upstream changed nothing under `testing/`, so the Taskfile entry point and the controller-first design are unchanged.
- **2026-11-18.** `small`, `dev` and `dms` pass full workflows on the work Mac, and every stage's check was shown to fail on its fault. `prod` passes its full workflow on a second Mac; that run found two faults, both fixed (the AlmaLinux image had no `ps`, which Splunk's command line needs; a synced checkout lost the lab key's file mode). 8 of spec 05's tasks remain open, all needing a lab host, a design choice or an answer from you. Records: `docs/history/verification-2026-11-18-*.md`; the day's decisions: `docs/decisions/2026-11-18-02-lab-behaviour-changes.md`.
- **Spec 10, day 2 operations: DRAFT.** It waits for spec 05.

## Goals

| Goal | Where it stands | Next |
| --- | --- | --- |
| **A virtual lab, not just a test runner**: log into a controller and operate a Splunk estate as in production | The controller works with no flags and runs the runner's Ansible; all four topologies have full recorded runs, and every stage's check was shown to fail on its fault; `prod` forms a two-peer indexer cluster and a two-member search head cluster, with a Git server that holds its app repositories | Memory and CPU figures for every topology on one host (5.5); a clean-host setup run (1.1) |
| **Stay current with upstream without its bash-first harness** | Upstream role merged and run in the lab on all four topologies, its cluster tasks included; the Taskfile design kept; `run-tests.sh` only forwards to `task`; the lint hook, which crashed upstream too, works again | Exercise the role's app deployment from the Git server (spec 10) |
| **Run it on real lab hosts** | `dms` ran on the pre-production host under root Podman. For a shared host: ports bind to loopback, the Git server refuses sign-up, the controller has no Docker socket, SSH takes keys only, lab names that already resolve are refused, images use names Podman resolves, and day0 checks free disk first | The pve2 VM's facts and a run there (3.1, 3.2); the lab on Podman with the new image names (3.12); the pre-production host (3.9); two labs on one engine (3.7) |
| **Teach Molecule** | The "Learn Molecule through the lab" tab in this doc | Lesson 1 in progress |

## Roadmap

```mermaid
flowchart LR
  A["Harness merged upstream<br/>PR #252 (2026-03-20)"] --> B["Virtual lab refactor<br/>Taskfile entry, controller ansible.cfg<br/>(2026-03-30)"]
  B --> C["Spec 05: lab as built<br/>reconstructed, reviewed, upstream merged<br/>(2026-11-02)"]
  C --> D["Spec 05: first runs<br/>pre-production host, dms topology<br/>(2026-11-10)"]:::here
  D --> E["Spec 05: isolation, clusters, git server<br/>multi-node runs, the pve2 VM"]
  E --> F["Spec 10: day 2 operations"]
  classDef here fill:#e7eefb,stroke:#1f5fd1,stroke-width:2px
```

## Why

The fork exists to turn the upstream role's Molecule harness into a virtual lab: a controller you log into and drive like production, with Molecule only building and tearing down the estate. The harness merged upstream in March and was refactored back to that intent on `feature/virtual-lab`, but had no run on record until November 2026. Spec 05 writes down what was built and collects that evidence before new features: by 2026-11-18 every topology has a recorded full run.

## Next

- **Needs you:** two questions (the Needs you panel above, `docs/decisions/2026-11-18-03-host-name-and-site-names.md`) and the sign-off on the review (the "Review of spec 05" tab).
- **Done since the last redraw:** `prod` end to end (2.1, 1.3) and a whole day0 behind the disk check (6.7). Still owed from that machine: memory and CPU for the other three topologies (5.5).
- **Then, on the lab hosts:** the pve2 VM's facts and a run there (3.1, 3.2); the lab on Podman with the new image names (3.12); the pre-production host (3.9).
- **Design work with no run needed:** two labs on one engine (3.7).
- **After spec 05:** spec 10, day 2 operations, which can now use the Git server's repositories.
