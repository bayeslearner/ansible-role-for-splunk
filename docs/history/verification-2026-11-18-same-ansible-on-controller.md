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

- The new version assert failing: no run with mismatched images was made.
- AlmaLinux nodes under the new controller Ansible (`small` is Ubuntu only).
- Base images, Gitea, go-task and the Python patch version are still unpinned (task 4.1).
