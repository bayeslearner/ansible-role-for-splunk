# Product: ansible-role-for-splunk fork and its virtual lab

## What This Repository Is

A fork of `splunk/ansible-role-for-splunk`, the Ansible role that installs, configures and upgrades Splunk Enterprise and Universal Forwarders. The fork lives at `bayeslearner/ansible-role-for-splunk` (formerly `kundeng/ansible-role-for-splunk`; GitHub redirects the old name). `upstream` is the Splunk repository.

The fork carries one product of its own: the **virtual lab** under `testing/`, a Docker and Molecule harness that stands up a multi-node Splunk topology from systemd containers and deploys it with this role over SSH, the way production is deployed. Its first version merged upstream as PR #252 (`555beec`); `feature/virtual-lab` continues it.

## Audience

- Kun, a Splunk administrator who runs the role against real Splunk estates and uses the lab to rehearse changes before they reach them.
- The upstream maintainers, who receive changes that are general enough to merge.

## Purpose Of The Virtual Lab

- **A lab first, a test runner second.** The `ansible-controller` container is a realistic deployment box: SSH in, run playbooks as in production, iterate and debug. Molecule creates and destroys the infrastructure and stays invisible from inside the controller.
- Repeatable integration testing of role changes across topologies (`small`, `prod`, `dev`, selected with `MOLECULE_ENV`).
- Scenarios follow the operating lifecycle: `infra` (containers and SSH), `day0` (install and cluster formation), `day1` (initial operations), and later day 2 (`docs/specs/10-day-2-operations`).

## Where The Lab Runs

Stated by Kun on 2026-11-02:

1. **First on a VM in pve2** (a Proxmox host in Kun's environment), where the lab is tested and run.
2. **Then on `splunkapp-preprod01`**, a shared pre-production host at work.

This repository is public. Facts about the work host (its network, users, DNS, other services) stay in Kun's private work notes; this file and the specs describe only what the lab requires of a host.

Consequence for the design: the lab must run on a Linux x86_64 Docker host, not only on a Mac under OrbStack where it was built. Host OS, Docker version, egress (Splunk downloads, image pulls) and the user the lab runs as on either host are not yet checked; each is checked before the lab is moved there.

## Invariants

- The role's own behaviour does not change to suit the lab; the lab drives the role as a user would (`splunk_download_local`, `deployment_task`, inventories).
- Converge playbooks and inventories are readable and runnable from inside the controller without knowing Molecule.
- `testing/Taskfile.yml` is the single entry point; `run-tests.sh` only forwards to `task`.
- Secrets are generated per checkout into `testing/.secrets/` and never committed.
- Changes meant for upstream stay separable from fork-only work.

## Pillars

| Pillar | Healthy when |
|---|---|
| Lab delivery | `task workflow:full` completes on each topology on each host the lab runs on, with evidence recorded |
| Role fidelity | Lab scenarios deploy through the role's real entry points, and upstream role changes are tested in the lab before they are relied on |
| Portability | The lab runs unchanged on macOS (OrbStack), the pve2 VM and `splunkapp-preprod01` |
| Documentation | `testing/README.md`, the specs and the feature matrix match the code |
| Upstream alignment | The fork's divergence from `upstream/master` is known and each difference is deliberate |
