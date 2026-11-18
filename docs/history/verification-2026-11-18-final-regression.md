# Verification: one regression on the day's final state

- **Date:** 2026-11-18
- **Code:** `7d3d91a` on `main`, unmodified.
- **Host:** macOS 27.2 on arm64, Docker engine 29.8.2 (OrbStack). Images rebuilt the same day from the pinned Dockerfiles. Runner: Molecule 25.12.0, ansible-core 2.21.6.
- **Why:** each task closed today was verified when it landed, and later commits changed the same playbooks and images. This run repeats the checks on the last commit, in one pass.
- **Raw output:** `testing/.runs/2026-11-18-final-regression/` on the machine that ran it (not committed); `results.txt` has one line per step.

All commands run from `testing/`.

## Runs that must pass

| Step | Command | Exit |
|---|---|---|
| `prod`, infra only (eleven containers, the Git server) | `MOLECULE_ENV=prod task infra:test` | 0 |
| `small`, everything | `MOLECULE_ENV=small task workflow:full` | 0 |
| `dms`, everything (Splunk 10.6.1.1) | `MOLECULE_ENV=dms task workflow:full` | 0 |
| `dev`, infra and day0, lab kept | `MOLECULE_ENV=dev task workflow:quick` | 0 |
| infra verify on the `dev` lab | `molecule verify -s infra` in the runner | 0 |
| diagnostics | `task diag:ssh`, `task diag:terminal` | 0, 0 |
| operator path, as `ansible` on the controller | `ansible all -m ping -o && ansible-playbook …/day0/verify.yml` | 0 |
| day1 on `dev`, after the faults below were undone | `task day1:test` | 0 |
| teardown | `task infra:destroy` | 0; no lab container left; only the Git server's volume remains |

## Runs that must fail

Each on the `dev` lab, with the fault undone afterwards.

| Fault | Command | Exit | Message |
|---|---|---|---|
| `systemctl stop Splunkd` on the node | `task day0:verify` | 201 | "Splunkd is inactive on splunk-dev" |
| the same | `task day1:verify` | 201 | "Splunkd not active on splunk-dev (status=inactive)" |
| `systemctl stop sshd` on the node | `molecule verify -s infra` | 2 | "The controller could not reach every node over SSH as ansible: splunk-dev UNREACHABLE … Connection refused" |
| the same | `task diag:ssh` | 201 | "splunk-dev UNREACHABLE" |
| `.secrets/ansible_password` moved aside | `molecule prepare -s infra --force` | 2 | "Missing lab secrets: /workspace/testing/.secrets/ansible_password" |

## Not in this run

Shown earlier the same day and not repeated here: a failed day0 leaving the lab up, the Git repository check failing on a deleted repository, the Ansible version check failing on a mismatch, the name-collision refusal, the offload unit across a restart, and the cluster halves. Their records are the other `verification-2026-11-18-*.md` files. Day 0 on `prod` has still not run.
