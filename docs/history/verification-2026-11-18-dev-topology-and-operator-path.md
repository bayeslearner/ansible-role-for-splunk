# Verification: the `dev` topology, the operator path, and a regression caught

- **Date:** 2026-11-18
- **Code:** the working tree on top of `234c8aa` (`main`), committed with this record.
- **Host and runner:** as in `verification-2026-11-18-small-topology.md`.
- **Raw output:** `testing/.runs/2026-11-18-dev/` on the machine that ran it (not committed).

All commands run from `testing/`.

## Regression in `234c8aa`, fixed here

The first `MOLECULE_ENV=dev task workflow:quick` after `234c8aa` failed at day0 converge. `dev`, `small` and `dms` each have an `indexer` group for a standalone indexer and no `clustermanager`, so the new "Join the indexers to the cluster as peers" play tried to join a manager that does not exist and failed after six tries. The peer play and the search-head play now also require a `clustermanager` group. After the fix:

| Command | Result |
|---|---|
| `MOLECULE_ENV=small task workflow:full` | exit 0 (`small-after-clusters.log`) |
| `MOLECULE_ENV=dev task workflow:quick` | exit 0; `[day0 > converge]` and `[day0 > verify]` "Executed: Successful" (`dev-quick.log`) |
| `MOLECULE_ENV=dev task day1:test` | exit 0 (`dev-day1.log`) |

`dms` was not rerun; it has the same shape as `dev`.

## Setup run twice (task 1.1)

A second `task setup` on the host that had already run it: exit 0, with `setup:secrets`, `setup:images` and `network:create` reported "up to date", the download play `changed=0`, and "Molecule runner already running" (`setup-second.log`). The first run is in the `small` record. Neither ran on a host that had never seen the lab; this Mac had old Splunk packages in `testing/software/` and existing secrets.

## From the controller, no flags (task 1.4)

On the `dev` lab, as `ansible` in an interactive shell on `ansible-controller`:

- `ansible all -m ping -o`: `splunk-dev` and `ansible-controller` answered `pong`.
- `ansible-playbook /workspace/testing/molecule/day0/verify.yml`: `failed=0` on `splunk-dev` and `localhost`.

## Web terminal login (task 1.5)

`curl` against `http://localhost:3000/ttyd/`: HTTP 200 with the generated password, 401 with a wrong password, 401 with none. `/ttyd` without the trailing slash answers 301 to `/ttyd/`.

## Diagnostic targets (task 5.3)

| Target | Lab state | Exit |
|---|---|---|
| `task diag:ssh` | healthy | 0 |
| `task diag:ssh` | `sshd` stopped on `splunk-dev` | 201 |
| `task diag:terminal` | healthy | 0 |
| `task diag:terminal` | `ttyd` stopped | 201 ("Expected 401 from the password prompt, got 502") |

## Download default (task 2.6)

`MOLECULE_ENV= task download:splunk` (the variable set but empty): `failed=0`.

## Memory, one reading after day1

`splunk-dev` 763 MiB, `ansible-controller` 82 MiB.
