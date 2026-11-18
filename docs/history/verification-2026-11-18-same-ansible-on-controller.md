# Verification: the controller runs the runner's Ansible

- **Date:** 2026-11-18
- **Code:** the working tree on top of `2a7a3cd` (`main`), committed with this record.
- **Host:** macOS 27.2 on arm64, Docker engine 29.8.2 (OrbStack). Topology `small`, Splunk Enterprise 9.4.2.
- **Raw output:** `testing/.runs/2026-11-18-pins/` on the machine that ran it (not committed).

## Before

| Image | Ansible | How it was installed |
|---|---|---|
| `molecule-runner` | ansible-core 2.21.6 | `pip install` with no version, so whatever was newest on the build day |
| `splunk-ansible-controller` | ansible 2.10.8 | Ubuntu 22.04's `apt` package |

A playbook run by Molecule and the same playbook typed on the controller ran on Ansible releases eleven minor versions apart.

## After

Both Dockerfiles name `ansible-core==2.21.6` and the collections `ansible.posix:2.2.2`, `community.crypto:3.5.1`, `community.general:14.0.1`, `community.docker:5.4.0`. The runner also pins `ansible-dev-tools==26.1.0`, `molecule-plugins==26.11.0`, `ansible-lint==26.11.0` and `requests==2.34.2` (Molecule was already 25.12.0). These are the versions the unpinned runner had resolved to, so the runner's behaviour is unchanged. Ubuntu 22.04's Python 3.10 is too old for this ansible-core, so the controller gets Python 3.12 in a virtualenv from `uv` 0.8.22.

| Step | Result |
|---|---|
| `docker build` of both images | exit 0 (`pin-runner-build.log`) |
| controller image: `ansible --version`, `ansible-galaxy collection list` | `ansible [core 2.21.6]` and the four collections at the versions above |
| `MOLECULE_ENV=small task workflow:quick` with the rebuilt images | exit 0 (`pin-small-quick.log`) |
| `molecule verify -s infra` | exit 0; "Runner and controller both run ansible-core 2.21.6"; "The controller reached every node over SSH as ansible" (`pin-infra-verify.log`) |
| on the controller as `ansible`: `ansible all -m ping`, then the day0 verify, day1 converge and day1 verify playbooks | all three hosts `pong`; `failed=0` in each playbook (day1 converge: `ok=29` per node) |

## Not covered

- AlmaLinux nodes under the new controller Ansible (`small` is Ubuntu only).
- Operating-system packages installed with `apt` and `dnf` inside the images are not pinned.

## Remaining pins, later the same day (task 4.1)

On the tree at `b6c49c8`, every base image is named by tag and digest, and the last three unpinned tools got versions:

| Image or tool | Was | Now |
|---|---|---|
| runner base | `python:3.12-slim` | `python:3.12.16-slim@sha256:5e2bdb1b…` |
| node and controller-builder base | `ubuntu:22.04` | `ubuntu:22.04@sha256:9abcaffc…` (22.04.5) |
| AlmaLinux node base | `almalinux:9` | `almalinux:9@sha256:02df0571…` (9.9) |
| Git server | `gitea/gitea:latest` | `gitea/gitea:28.4.0@sha256:aa90e8f0…` |
| `uv` in the controller | `0.8.22` | `0.8.22@sha256:9874eb7a…` |
| go-task in the runner | the install script's newest | `v3.54.0` |
| controller Python | `3.12` | `3.12.11` |

Each "now" value is what the unpinned build had resolved to, so behaviour is unchanged.

| Step | Result |
|---|---|
| `task setup:rebuild` (all five images) | exit 0 (`pin2-rebuild.log`) |
| versions read from the rebuilt images | runner: go-task 3.54.0, Python 3.12.16, ansible-core 2.21.6; controller Python 3.12.11; Gitea 28.4.0 |
| `MOLECULE_ENV=small task workflow:full` on the rebuilt images | exit 0; 9 Molecule steps "Executed: Successful", none failed (`pin2-small-full.log`) |
| `MOLECULE_ENV=prod task infra:test` on the rebuilt images | exit 0; 6 steps "Executed: Successful"; the version match and the SSH check to all nine nodes pass; no "Missing playbook" warning (`pin2-prod-infra-test.log`) |

The `prod` infra run is what exercises the rebuilt AlmaLinux and Git server images.

## The version check failing

On the tree at `b38171c`, on the `dev` lab's infrastructure: the controller's `ansible` command was replaced by a script that prints `ansible [core 2.10.8]`, then `molecule verify -s infra` was run.

| Controller reports | Result |
|---|---|
| `ansible [core 2.10.8]` | exit 2: "Runner runs ansible-core 2.21.6; the controller reports: ansible [core 2.10.8]" (`ver-neg.log`) |
| the real command restored | exit 0 (`ver-ok.log`) |

