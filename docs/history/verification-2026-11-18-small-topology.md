# Verification: the `small` topology and the new checks

- **Date:** 2026-11-18
- **Code:** the working tree on top of `6e13f84` (`main`), committed with this record.
- **Topology:** `MOLECULE_ENV=small`: `splunk-license`, `splunkapp-prod01`, `ansible-controller`. Splunk Enterprise 9.4.2.
- **Host:** macOS 27.2 on arm64, Docker engine 29.8.2 (OrbStack), 15.66 GiB given to the engine. The Splunk images are amd64 and run emulated.
- **Runner:** `molecule-runner:latest` built the same day: Molecule 25.12.0, ansible-core 2.21.6, Python 3.12.
- **Raw output:** `testing/.runs/2026-11-18-small/` on the machine that ran it. The logs print the lab's generated SSH public keys, so they are not committed; `*.log` and `.runs/` are ignored.

All commands run from `testing/`.

## Runs that must pass

| Command | Result | Evidence |
|---|---|---|
| `task setup` | exit 0 | `setup.log`: images built, Splunk 9.4.2 packages present, network and runner created |
| `MOLECULE_ENV=small task infra:test` | exit 0 | `infra-small.log`: prepare `failed=0` on all three containers; verify printed "The controller reached every node over SSH as ansible" |
| `MOLECULE_ENV=small task workflow:quick` | exit 0 | `quick-small.log`: day0 converge `failed=0`; `[day0 > verify] Executed: Successful` |
| `MOLECULE_ENV=small task day1:test` | exit 0 | `day1-small.log`: restart, status and "Accept the Splunk licence" `ok` on both nodes; `[day1 > verify] Executed: Successful` |
| `MOLECULE_ENV=small task workflow:full`, twice in a row | exit 0 both times | `full-small.log`, `full-small-second.log`: 10 Molecule steps each, all "Executed: Successful"; no lab container or node volume left afterwards |

## Runs that must fail

Each new check was given the fault it exists to catch, with the lab up.

| Fault | Command | Result |
|---|---|---|
| `.secrets/ansible_password` moved aside | `molecule prepare -s infra --force` in the runner | exit 2 at the first task: "Missing lab secrets: /workspace/testing/.secrets/ansible_password. Create them with: task setup (run from testing/)" |
| `systemctl stop sshd` on `splunkapp-prod01` | `molecule verify -s infra` in the runner | exit 2: "The controller could not reach every node over SSH as ansible: splunkapp-prod01 UNREACHABLE … port 22: Connection refused"; `splunk-license` answered |
| `systemctl stop Splunkd` on `splunkapp-prod01` | `task day0:verify` | exit 201: "Splunkd is inactive on splunkapp-prod01" |
| the same stopped node | `task day1:verify` | exit 201: diagnostics printed for that node only (no splunkd process, the last `splunkd.log` errors, the unit `inactive (dead)`), then "Splunkd not active on splunkapp-prod01 (status=inactive)" |

After each fault the service or file was restored, and `molecule verify -s infra` passed again.

`task infra:setup` cannot show the missing-secret message, because its dependencies regenerate the secrets first. The check protects a direct `molecule prepare`, such as one typed in `task runner:shell`.

## Found by the first full run

The first `task workflow:full` after the runs above failed at day0 converge (`full-small-stale-volume.log`): the role stopped with "Misconfiguration detected … splunk boot-start is not enabled on this host". Each node keeps `/opt` in a named volume (`ansible-splunk-test-<host>-data`), and `infra/destroy.yml` removed the containers but left the volumes, so the new containers found Splunk installed with no systemd unit. `destroy.yml` now removes each node's data volume with the node (the Git server's volume is kept), and the two consecutive full runs in the table above passed after that change.

## Memory, right after day0

`docker stats --no-stream`, one reading, taken right after day0 while both Splunk nodes were still busy (about 96% of one core each):

| Container | Memory |
|---|---|
| `splunk-license` | 620.9 MiB |
| `splunkapp-prod01` | 518.8 MiB |
| `ansible-controller` | 56.6 MiB |

One reading is not a requirement figure; task 5.5 owns that.

## Against task 1.2's wording

Task 1.2 asks for the full log plus `docker ps` before the destroy. The logs are kept locally as stated above. No `docker ps` was captured before the destroy in the full runs; the containers that were up are shown by the `docker stats` reading taken after `workflow:quick` (the three names in the memory table) and by each scenario's play recap, which lists every host it reached.

## What this does not cover

- `dev` and `prod` were not run. `dms` has its own record in the spec Log from the pre-production host.
- The web terminal login (task 1.5) and commands typed on the controller (task 1.4) were not exercised by hand; infra verify ran `ansible … -m ping` on the controller as `ansible`.
- Docker on Linux, and Podman, were not part of this run.
