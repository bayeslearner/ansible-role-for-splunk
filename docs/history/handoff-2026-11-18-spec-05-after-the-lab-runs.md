# Handoff: spec 05 after the lab's full runs

Written 2026-11-18 at the end of a long session, for whoever picks the lab up next. Status lives in the spec and the feature matrix; this file says what to read, what is open and what not to repeat.

## Objective

Close spec 05 (the virtual lab as built), then start spec 10 (day 2 operations).

## State on `main`

- All four topologies have a full recorded run; `prod` forms a two-peer indexer cluster and a two-member search head cluster. Every stage's check has been shown to fail on its fault.
- A lab can be named (`LAB_NAME`, `LAB_PORT_OFFSET`), so several share one engine. The Taskfile sets the amd64 platform itself. CI runs lint, the spec lint and a Taskfile dry-run.
- Records of the day, each with its commands and results: `docs/history/verification-2026-11-18-*.md`. Decisions the agent made: `docs/decisions/2026-11-18-02-lab-behaviour-changes.md` (nine items).

## Open

| Item | Waits on |
|---|---|
| Tasks 3.1, 3.2: facts of, and a run on, the pve2 VM | the VM existing; a request with the lab's measured needs was left with the session that owns that hardware |
| Task 3.9: `small` in full on the pre-production host with today's code | the owner asking for it; it changes state on a shared host. It will need `podman` as the build command and probably `LAB_RUNNER_ARGS='--security-opt label=disable'` (`verification-2026-11-18-lab-on-podman.md`) |
| Task 5.1 | whatever those two runs change in `testing/README.md` |
| Two owner questions | `docs/decisions/2026-11-18-03-host-name-and-site-names.md` |
| Sign-off on the review of spec 05 | the owner, on the Board |

## Do not repeat

- **Never install Splunk on a machine whose container disk is shared with other work.** It filled such a disk on 2026-11-18 and took another project's database down. Image builds under emulation also take about 10 GB while they run. Check free disk first and tell whoever else depends on that machine.
- **Never run `image prune -a` or `system prune` on an engine you did not create.** Remove what you made by name.
- **Regenerate the Board files once per reseed pass**, and commit the applied hashes in `docs/board/doc-tabs.json` afterwards.
- **After changing a file the Board's two teaching tabs quote** (`Taskfile.yml`, the infra playbooks, the Dockerfiles), check those tabs against the code.
- **A checkout shared through a file sync shares its `.secrets/`** and loses file modes; `task setup:secrets` repairs the mode, and separate secrets per machine need a `git clone`.

## Known limits, recorded and not fixed

- Two labs running day0 at the same moment has not been tried.
- On an ARM machine under Podman the infra prepare step fails: the amd64 Docker client in the runner crashes under emulation. It works on x86_64 Podman.
- day0's Git server report is informational by decision; infra verify asserts the repositories.

## Next action

When the owner answers: act on the two questions, then either run 3.9 or record that the pve2 step is dropped, close spec 05 through `/spec-review`, and activate spec 10.
