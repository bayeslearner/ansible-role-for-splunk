# Board orientation

The Board's "Where we are" panel, read by `docs/board/seed.py`. Redraw it when a spec closes, the direction changes or a big decision lands.

## Here

The lab has run for the first time, on the pre-production host with Podman, as the one-node `dms` topology; the multi-node topologies and the pve2 VM have not run yet.

- **Spec 05, the virtual lab as built: ACTIVE.** Reconstructed from the code on 2026-11-02. Its review (the "Review of spec 05" tab) awaits your sign-off. On 2026-11-10 and 11-11 infra, day0 converge (61 tasks, none failed) and day0 verify passed on the pre-production host (spec 05 Log; tasks 2.5, 3.10, 3.11 done).
- **Upstream merged.** `upstream/master` (`750c071`) is merged into `feature/virtual-lab`. Upstream changed nothing under `testing/`, so the Taskfile entry point and the controller-first design are unchanged.
- **Spec 10, day 2 operations: DRAFT.** It waits for spec 05.

## Goals

| Goal | Where it stands | Next |
| --- | --- | --- |
| **A virtual lab, not just a test runner**: log into a controller and operate a Splunk estate as in production | The controller, its `ansible.cfg` and web terminal are built; the `prod` topology installs Splunk but forms no clusters | Clusters and the git server (spec 05 tasks 2.1, 2.3) |
| **Stay current with upstream without its bash-first harness** | Upstream role merged; the lab's Taskfile design kept; `run-tests.sh` only forwards to `task` | Run the lab against the merged role (task 2.7) |
| **Run it on real lab hosts** | The `dms` topology runs on the pre-production host under root Podman; isolation work (3.3) is started, not finished | Finish isolation (3.3, 3.4, 3.6, 3.9); run the multi-node topologies; the pve2 VM (3.1, 3.2) |
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

The fork exists to turn the upstream role's Molecule harness into a virtual lab: a controller you log into and drive like production, with Molecule only building and tearing down the estate. The harness merged upstream in March and was refactored back to that intent on `feature/virtual-lab`, but never run on record. Spec 05 writes down what was built, so the next step is evidence, not new features.

## Next

- **Now, spec 05:**
    - Sign off the review (the "Review of spec 05" tab).
    - Write the pre-production runs up as verification records under `docs/history/` (tasks 1.1, 1.2).
    - Cheap correctness fixes: tasks 2.2, 2.6, 3.8.
- **Then:** record the pve2 VM's facts and run there (3.1, 3.2); isolation before the pre-production host (3.3, 3.4, 3.6, 3.9).
- **Then:** clusters and Gitea (2.1, 2.3), which spec 10 needs.
