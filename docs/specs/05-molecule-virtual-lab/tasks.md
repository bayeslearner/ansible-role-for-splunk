# Tasks: Molecule virtual lab

## Status Marks
[ ] pending | [ ]* optional | [x] complete | [!] BLOCKED: reason
[-] DROPPED: reason | [>] -> NN-successor

Built code that has no recorded verification stays `[ ]` with "built in <commit>"; it becomes `[x]` when a verification record under `docs/history/` shows it working. Findings are tracked here because the fork is a public repository with Issues disabled.

## Tasks

- [ ] 1. Foundation: verify what is built
  - [ ] 1.1 `task setup` from a clean lab host creates secrets, images, tarballs, network and runner, and a second run skips every step
    - Built in: `555beec`, `55426a6`
    - Requirements: R1
    - Verification: run twice on a clean host; record both outputs in `docs/history/verification-<date>-lab-setup.md`
  - [ ] 1.2 `MOLECULE_ENV=small task workflow:full` passes on the Mac
    - Built in: `555beec`, `86a1a37`
    - Requirements: R2, R3, R4, R5, R9
    - Verification: full log plus `docker ps` before destroy, in a verification record
  - [ ] 1.3 Same for `dev` and `prod`
    - Depends: 1.2
    - Requirements: R2, R4
  - [ ] 1.4 From the controller, `ansible all -m ping` and `ansible-playbook /workspace/testing/molecule/day0/verify.yml` run with no flags
    - Built in: `86a1a37`
    - Requirements: R6
  - [ ] 1.5 Web terminal login at `:3000/ttyd` works with the generated password and refuses a wrong one
    - Requirements: R7

- [ ] 2. Core: close the gaps between the docs and the code
  - [ ] 2.1 `prod` forms the clusters its inventory describes: run the role's indexer-cluster and search-head-cluster deployment (`playbooks/splunk_idxc_deploy.yml`, `playbooks/splunk_shc_deploy.yml` or their task files) in a scenario, and make day0 verify report a real cluster state
    - Requirements: R4
    - Note: until then, the README must not call the `prod` nodes a cluster
  - [ ] 2.2 `infra/verify.yml` checks SSH from the controller to every node as `ansible`, so a broken key fails infra instead of day0
    - Requirements: R3
  - [ ] 2.3 Git server: create the Gitea admin, the `test/splunk_apps` repository with the apps `prod` names, and the deploy key at `git_key`, or remove `git_apps` from `prod` until day 2 needs them
    - Requirements: R8
  - [ ] 2.4 Controller Ansible matches the runner: install `ansible-core` at the runner's pinned version in the controller image instead of Ubuntu's apt `ansible`, and print both versions in infra verify
    - Requirements: R6, NFR Fidelity
  - [ ] 2.5 Image checks use `docker image inspect <name>` instead of `docker images | grep -q name:latest`, which fails on Docker CLIs that print repository and tag in separate columns
    - Requirements: R1, R10
  - [ ] 2.6 `download.yml` defaults `MOLECULE_ENV` when empty (`default('small', true)`), as `prepare.yml` already does
    - Requirements: R1
  - [ ] 2.7 Test the lab against `upstream/master`'s role (24 commits past `555beec`: nix-user refactor, app deployment rewrite with `apps`/`git_apps`, `splunk_secret_content`); record what breaks
    - Requirements: R4, R5

- [ ] 3. Portability and isolation for the pve2 VM and the pre-production host
  - [ ] 3.1 Record the facts of each lab host before the first run: OS, kernel and cgroup version, Docker engine and CLI versions, egress to download.splunk.com and Docker Hub, the user the lab runs as, DNS search domains
    - Requirements: R10
    - Verification: `docs/history/research-<date>-lab-hosts.md`, kept generic; host-specific details stay in the private work notes, not this public repo
  - [ ] 3.2 `MOLECULE_ENV=small task workflow:full` passes on the pve2 VM
    - Depends: 1.2, 3.1
    - Requirements: R10
  - [ ] 3.3 Published ports bind to `127.0.0.1` by default with a variable to widen them; Gitea registration disabled
    - Requirements: NFR Isolation
  - [ ] 3.4 Remove the Docker socket from the controller, or document why the operator path needs it (nothing in the scenarios uses it from the controller)
    - Requirements: NFR Isolation
  - [ ] 3.5 Decide whether nodes can run without `privileged` and `cgroupns_mode: host` on the target hosts' cgroup version; record the result
    - Requirements: NFR Isolation
  - [ ] 3.6 Lab names cannot resolve to real hosts: give the lab network its own DNS suffix or names that cannot collide, and fail infra if any inventory host lacks a running container
    - Requirements: NFR Isolation
  - [ ] 3.7 Container names, network and ports take a lab prefix so two labs can share a Docker host
    - Requirements: R10
  - [ ] 3.8 Reapply the veth offload fix on container start (a systemd unit in the node images) so it survives restarts of the lab host
    - Requirements: R10
  - [ ] 3.9 `MOLECULE_ENV=small task workflow:full` passes on the pre-production host
    - Depends: 3.2, 3.3, 3.4, 3.6
    - Requirements: R10

- [ ] 4. Reproducibility
  - [ ] 4.1 Pin exact versions: base images by tag and digest, Gitea, ttyd (already 1.7.7), pip packages in the runner, Galaxy collections, go-task
    - Requirements: NFR Reproducibility

- [ ] 5. Polish and docs
  - [ ] 5.1 `testing/README.md` matches the code after 2.x and 3.x (topology names, what `prod` forms, ports, host requirements)
  - [ ] 5.2 Remove or wire `day0/destroy.yml`; stop `mol-run` after `infra:test` or drop `runner:start` from `setup`
  - [ ] 5.3 `diag:ssh` and `diag:terminal` exit non-zero on failure
  - [ ] 5.4 Remove the Twingate block from `.env.example`, or implement it under a spec

## Log
- 2026-11-02: Spec reconstructed from the code at `6ff020f` and set ACTIVE (decided by the agent; the owner may reverse). No lab run has a recorded result, and the work Mac has none of the lab images. Gaps found while reading are tasks 2.1–2.7, 3.3–3.8, 4.1 and 5.2–5.4. Kun named the hosts the lab will run on: the pve2 VM first, then the pre-production host (`docs/steering/product.md`).
