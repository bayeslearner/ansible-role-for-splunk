# Tasks: Molecule virtual lab

## Status Marks
[ ] pending | [ ]* optional | [x] complete | [!] BLOCKED: reason
[-] DROPPED: reason | [>] -> NN-successor

Built code that has no recorded verification stays `[ ]` with "built in <commit>"; it becomes `[x]` when a verification record under `docs/history/` shows it working. Findings are tracked here because the fork is a public repository with Issues disabled.

## Tasks

- [ ] 1. Foundation: verify what is built
  - [ ] 1.1 `task setup` from a clean lab host creates secrets, images, tarballs and the network, and a second run skips every step
    - Second run skips every step: shown 2026-11-18. Still owed: the first run on a host that has never had the lab.
    - Built in: `555beec`, `55426a6`
    - Requirements: R1
    - Verification: run twice on a clean host; record both outputs in `docs/history/verification-<date>-lab-setup.md`
  - [x] 1.2 `MOLECULE_ENV=small task workflow:full` passes on the Mac
    - Built in: `555beec`, `86a1a37`
    - Requirements: R2, R3, R4, R5, R9
    - Verification: full log plus `docker ps` before destroy, in a verification record
  - [ ] 1.3 Same for `dev` and `prod`
    - `dev` passed infra, day0 and day1 on 2026-11-18 (`docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`). `prod` is owed; see 2.1.
    - Depends: 1.2
    - Requirements: R2, R4
  - [x] 1.4 From the controller, `ansible all -m ping` and `ansible-playbook /workspace/testing/molecule/day0/verify.yml` run with no flags
    - Built in: `86a1a37`
    - Requirements: R6
  - [x] 1.5 Web terminal login at `:3000/ttyd` works with the generated password and refuses a wrong one
    - Requirements: R7

- [ ] 2. Core: close the gaps between the docs and the code
  - [ ] 2.1 `prod` forms the clusters its inventory describes: run the role's indexer-cluster and search-head-cluster deployment (`playbooks/splunk_idxc_deploy.yml`, `playbooks/splunk_shc_deploy.yml` or their task files) in a scenario, and make day0 verify report a real cluster state
    - Requirements: R4
    - Code landed 2026-11-18: day0 converge runs the role's manager, peer, search-head, deployer, member and captain tasks on the cluster groups, guarded so it can run twice; `prod` sets `splunk_uri_cm`, replication and search factor 2, and `splunk_mgmt_uri`; day0 verify waits for every indexer and every search head cluster member to be Up. Indexer half verified. Search head half verified on a third attempt the same day: verify passes on the healthy two-member cluster and fails when a member is stopped. `prod` as a whole has not run. Evidence: `docs/history/verification-2026-11-18-cluster-formation.md`. Stays open until `MOLECULE_ENV=prod task workflow:full` passes on a host with about 30 GB of free engine disk.
    - Note: until then, the README must not call the `prod` nodes a cluster
    - Priority: first of the last-mile work. The owner confirmed on the Board (2026-11-18) that `prod` is meant to form the smallest valid clusters, two indexers and two search heads, to exercise the role's cluster tasks.
  - [x] 2.2 `infra/verify.yml` checks SSH from the controller to every node as `ansible`, so a broken key fails infra instead of day0
    - Requirements: R3
  - [x] 2.3 Git server: create the Gitea admin, the `test/splunk_apps` repository with the apps `prod` names, and the deploy key at `git_key`, or remove `git_apps` from `prod` until day 2 needs them
    - Requirements: R8
  - [x] 2.4 Controller Ansible matches the runner: install `ansible-core` at the runner's pinned version in the controller image instead of Ubuntu's apt `ansible`, and print both versions in infra verify
    - Requirements: R6, NFR Fidelity
  - [x] 2.5 Image checks use `docker image inspect <name>` instead of `docker images | grep -q name:latest`, which fails on Docker CLIs that print repository and tag in separate columns
    - Requirements: R1, R10
  - [x] 2.6 `download.yml` defaults `MOLECULE_ENV` when empty (`default('small', true)`), as `prepare.yml` already does
    - Requirements: R1
  - [x] 2.7 Test the lab against `upstream/master`'s role (24 commits past `555beec`: nix-user refactor, app deployment rewrite with `apps`/`git_apps`, `splunk_secret_content`); record what breaks
    - Merged in `eeb2d89`; `ansible-playbook --syntax-check` passes for day0 and day1 converge (ansible-core 2.18). A lab run is still owed.
    - Run 2026-11-18 on `main`, which contains `upstream/master` at `750c071`: `small` and `dev` pass infra, day0 and day1, and the role's cluster tasks formed an indexer cluster. Nothing in the merged role broke those paths. Not exercised: app deployment (`apps`, `git_apps`), which waits for the Git server (2.3).
    - Requirements: R4, R5

- [ ] 3. Portability and isolation for the pve2 VM and the pre-production host
  - [ ] 3.1 Record the facts of each lab host before the first run: OS, kernel and cgroup version, Docker engine and CLI versions, egress to download.splunk.com and Docker Hub, the user the lab runs as, DNS search domains
    - Requirements: R10
    - Verification: `docs/history/research-<date>-lab-hosts.md`, kept generic; host-specific details stay in the private work notes, not this public repo
  - [ ] 3.2 `MOLECULE_ENV=small task workflow:full` passes on the pve2 VM
    - Depends: 1.2, 3.1
    - Requirements: R10
  - [x] 3.3 Published ports bind to `127.0.0.1` by default with a variable to widen them; Gitea registration disabled
    - Requirements: NFR Isolation
  - [x] 3.4 Remove the Docker socket from the controller, or document why the operator path needs it (nothing in the scenarios uses it from the controller)
    - Requirements: NFR Isolation
  - [x] 3.5 Decide whether nodes can run without `privileged` and `cgroupns_mode: host` on the target hosts' cgroup version; record the result
    - 2026-11-18: decided for the one engine tried (Docker on OrbStack, cgroup v2): nodes stay privileged. A node runs Splunk without `privileged` given the host cgroup namespace and `NET_ADMIN`, but the role's `disable-thp.service` then fails, so the node would no longer be the target the role is written for. Result and the shared-host consequence: `docs/history/research-2026-11-18-nodes-without-privileged.md`. The pve2 VM and the pre-production host still need the same check under 3.1.
    - Requirements: NFR Isolation
  - [x] 3.6 Lab names cannot resolve to real hosts: give the lab network its own DNS suffix or names that cannot collide, and fail infra if any inventory host lacks a running container
    - 2026-11-18: done as a refusal: infra stops before creating anything when a lab host name already resolves outside the lab. The lab's names are unchanged and the network has no DNS suffix of its own; with the check, a collision cannot go unnoticed. Evidence: `docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`.
    - Requirements: NFR Isolation
  - [ ] 3.7 Container names, network and ports take a lab prefix so two labs can share a Docker host
    - Requirements: R10
  - [x] 3.8 Reapply the veth offload fix on container start (a systemd unit in the node images) so it survives restarts of the lab host
    - Requirements: R10
  - [ ] 3.9 `MOLECULE_ENV=small task workflow:full` passes on the pre-production host
    - Depends: 3.2, 3.3, 3.4, 3.6
    - Requirements: R10
  - [x] 3.10 The engine socket is a variable: `DOCKER_SOCK` (default `/var/run/docker.sock`) is the socket the runner mounts (the controller mounted it too until 3.4), so the lab can run against a Podman API service whose storage is not the host's default store (a shared host's `/var` may be too small for the lab)
    - Requirements: R10, NFR Isolation
    - Verification: with `DOCKER_SOCK` pointing at a separate Podman service, `MOLECULE_ENV=dms task infra:setup` creates every container in that service's storage and the default store is unchanged
  - [x] 3.11 A `dms` environment: one all-in-one Splunk Enterprise 10.6.1.1 node (`splunk-dms`) plus the controller, for testing the Data Management API app (Edge Processor control plane, Splunk Enterprise 10.6 and later)
    - Depends: 3.10
    - Requirements: R10
    - Verification: `MOLECULE_ENV=dms task day0:converge` and `day0:verify` pass; `splunk version` on `splunk-dms` reports 10.6.1.1
  - [ ] 3.12 Lab images resolve on a Podman engine: `podman build -t name:latest` stores `localhost/name:latest`, while the Docker-compatible API that `community.docker` calls reads the short name as `docker.io/library/name:latest`, finds nothing and tries a pull (`500 ... connection refused`). Tag the images under both names in `setup:images`, or reference them by a name both engines resolve
    - 2026-11-18: fix landed: the five images are named `localhost/<name>:latest`, which both engines resolve. Reproduced and shown fixed on Podman 6.0.2 with the same module and a probe image; the lab passes on Docker with the new names (`docs/history/verification-2026-11-18-image-names-docker-and-podman.md`). Stays open for its own check: `infra:create` of the lab on a Podman engine.
    - Depends: 3.10
    - Requirements: R10
    - Verification: `infra:create` on a Podman engine creates every container with no pull attempt

- [ ] 4. Reproducibility
  - [x] 4.1 Pin exact versions: base images by tag and digest, Gitea, ttyd (already 1.7.7), pip packages in the runner, Galaxy collections, go-task
    - 2026-11-18, part done: the runner's pip packages and both images' ansible-core and Galaxy collections are pinned to exact versions (`docs/history/verification-2026-11-18-same-ansible-on-controller.md`). Completed the same day: base images by tag and digest, Gitea 28.4.0, go-task v3.54.0, uv by digest, controller Python 3.12.11. Operating-system packages from `apt` and `dnf` are not pinned.
    - Requirements: NFR Reproducibility

- [ ] 5. Polish and docs
  - [ ] 5.1 `testing/README.md` matches the code after 2.x and 3.x (topology names, what `prod` forms, ports, host requirements)
    - 2026-11-18: brought up to `a05d639`: topology lists, what each stage does and checks, clusters on `prod`, troubleshooting targets, `DOCKER_SOCK` and `LAB_BIND_ADDRESS`, cleanup, disk needs. Stays open for the measured memory and CPU figures (5.5) and for 3.x.
  - [x] 5.2 Remove or wire `day0/destroy.yml`; stop `mol-run` after `infra:test` or drop `runner:start` from `setup`
    - 2026-11-18, first half done: `day0/destroy.yml` was not unused. `molecule test` ran it whenever day0 failed, deleting the lab and leaving its node volumes. It is removed, and `day0:test` and `day1:test` pass `--destroy=never`. Evidence: `docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`. Second half done the same day: `setup` no longer starts `mol-run`; `task runner:shell` starts it on demand and `runner:stop` removes it.
  - [x] 5.3 `diag:ssh` and `diag:terminal` exit non-zero on failure
  - [x] 5.4 Remove the Twingate block from `.env.example`, or implement it under a spec
  - [ ] 5.5 `testing/README.md` and the root README state the RAM and CPU each topology needs, measured and not estimated: after day0 on `small`, `dev`, `dms` and `prod` (with clusters formed, 2.1), record `docker stats --no-stream` per container and the engine's total, and give a minimum and a comfortable figure per topology
    - Depends: 1.2, 1.3, 2.1
    - Requirements: R10
    - Verification: the `docker stats` output in a verification record
  - [x] 5.6 `pre-commit run --all-files` passes: the `ansible-lint` hook is pinned to v24.9.2, which crashes on import against the ansible-core its environment now installs (`ModuleNotFoundError: No module named 'ansible.parsing.yaml.constructor'`), so no Ansible lint runs; and the hook covers `roles/ playbooks/ environments/` but not `testing/molecule/`. Bump the hook, add the lab's playbooks, fix what it reports. `.pre-commit-config.yaml` is upstream's file, so the bump is also an upstream fix.
    - Found 2026-11-18. `end-of-file-fixer`, `trailing-whitespace` and `yamllint` pass on the fork's own files after this commit; `roles/splunkupgrader/templates/local_config_102.j2` (upstream's) failed the first two; it is now excluded from them and left as upstream ships it.

- [ ] 6. Last mile: what PR 252 cut and the review found
  - [x] 6.1 `day0/verify.yml` fails when a node's Splunk unit is not active or its management or web port is closed (it used `ignore_errors` on every check). The cluster plays became asserting with 2.1 and the Git server report stays informational; at the time of this task both were informational until 2.1 and 2.3.
    - Requirements: R4
    - Verification: a day0 run that passes, and one with Splunk stopped on a node that fails at the assert
  - [x] 6.2 `infra/prepare.yml` stops at its first task with the command to run when a lab secret is missing (cut in PR 252)
    - Requirements: R1, R3
    - Verification: an infra run with `.secrets/ansible_password` moved aside
  - [x] 6.3 `day1/converge.yml` accepts the Splunk licence after the restart (cut in PR 252)
    - Requirements: R5
  - [x] 6.4 `day1/verify.yml` prints processes, the last `splunkd.log` errors and the unit status for a node whose service is not active, before its assert (cut in PR 252)
    - Requirements: R5
  - [x] 6.5 `infra/destroy.yml` removes each node's data volume with the node, so a lab built after a destroy starts clean (found by the first full run: a leftover `/opt` volume with no systemd unit failed the role's boot-start check)
    - Requirements: R9
    - Verification: two `task workflow:full` runs in a row
  - [x] 6.6 The AlmaLinux node image installs `openssh-clients`, so `scp` exists on those nodes (the inventory copies files with scp; found by the first `prod` infra verify, which could not reach either AlmaLinux node)
    - Requirements: R2, R3
    - Verification: `prod` infra verify reaches all nine nodes
  - [ ] 6.7 `day0/converge.yml` stops before any install when the container engine's disk cannot hold the pending installs plus a margin, with a message that says how much is free and how much is needed
    - Requirements: R4, R10
    - Verification: the check passing and failing on its own (done 2026-11-18, `docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`); a whole day0 run with the check in front (owed: not run on the Mac, whose engine disk is shared with other work)

## Log
- 2026-11-02: Spec reconstructed from the code at `6ff020f` and set ACTIVE (decided by the agent; the owner may reverse). No lab run has a recorded result, and the work Mac has none of the lab images. Gaps found while reading are tasks 2.1–2.7, 3.3–3.8, 4.1 and 5.2–5.4. Kun named the hosts the lab will run on: the pve2 VM first, then the pre-production host (`docs/steering/product.md`).
- 2026-11-02: Merged `upstream/master` (`750c071`) into `feature/virtual-lab`. Upstream changed nothing under `testing/`, so the Taskfile entry point and the controller-first design are unchanged. Day0 and day1 converge pass `--syntax-check` against the merged role.
- 2026-11-10: The pre-production host is `splunkapp-preprod02`; `splunkapp-preprod01` does not resolve. Added 3.10 (socket variable) and 3.11 (`dms` environment) for the first run there, and started 3.3 with the published-port bind address (Gitea registration still open). Kun asked for the run.
- 2026-11-10: 3.10 and 3.11 verified on the pre-production host against a separate root Podman API service: infra created the controller and `splunk-dms`, day0 converge ran 61 tasks with none failed, day0 verify passed (its git-server check is ignored when no git server exists), `splunk version` reports 10.6.1.1 build b2ae2962645c, and the host's default container store gained nothing. The run needed the images tagged under `docker.io/library/` names on the host first, which is task 3.12.
- 2026-11-11: On the pre-production host, root Podman's default store now lives on `/app` (`/var/lib/containers` links to `/app/var/lib/containers`), and the lab runs on it through the stock `podman.socket` with `DOCKER_SOCK=/run/podman/podman.sock`; the separate Podman service and store used on 2026-11-10 are retired. Rebuilt there: infra, day0 converge (61 ok, 0 failed) and verify pass. `infra:destroy` cannot remove `mol-run`, the container it runs in; remove it afterwards.
- 2026-11-18: The lab branch is `main` and the fork's default branch (`docs/decisions/2026-11-18-01-main-default-branch.md`). Added group 6 from the Board's "Code tour and last mile" tab and wrote the code for 2.2 and 6.1 to 6.4; all five playbooks pass `ansible-playbook --syntax-check` on ansible-core 2.18.1. Lab runs are still owed for each.
- 2026-11-18: First recorded runs on the Mac, `small` topology: setup, infra, day0, day1 and two consecutive `workflow:full` runs pass, and each new check (2.2, 6.1, 6.2, 6.4) was shown to fail on its fault. Evidence: `docs/history/verification-2026-11-18-small-topology.md`. Closes 1.2, 2.2 and 6.1 to 6.5. Open from this run: `dev` and `prod` (1.3), the second `task setup` run (1.1), and the runner's unpinned ansible-core, 2.21.6 on this build (4.1).
- 2026-11-18: 2.1 written and run in two halves on the Mac (`docs/history/verification-2026-11-18-cluster-formation.md`). The whole `prod` topology does not fit this Mac's Docker disk: the install failed with "No space left on device" on all eight Enterprise nodes. Disk is now a stated requirement to measure with memory in 5.5.
- 2026-11-18: `234c8aa` broke day0 on `small`, `dev` and `dms`, whose standalone `indexer` group was sent to join a missing manager; fixed by requiring a `clustermanager` group, and `small` (full) and `dev` (infra, day0, day1) pass again. Also closed 1.4, 1.5, 2.6 and 5.3 with evidence in `docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`.
- 2026-11-18: A failed day0 deleted the lab (Molecule ran `day0/destroy.yml` on failure); fixed and shown before and after on `dev`. This corrects the design's earlier statement that `day0/destroy.yml` is never invoked.
- 2026-11-18: Closed 2.7 (lab runs against the merged upstream role), 5.2 (runner started on demand) and 5.4 (`.env.example` lists the lab's real settings instead of an unimplemented Twingate block).
- 2026-11-18: 2.4 closed. The controller ran ansible 2.10.8 from apt while the runner ran ansible-core 2.21.6; both now pin 2.21.6 and the same collections, infra verify asserts they match, and the controller ran ping, day0 verify and day1 on `small` with it.
- 2026-11-18: `dms` (Splunk 10.6.1.1) passes a full workflow on the Mac after the day's changes to day0 and day1, so 3.11 still holds (`docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`). Every topology except `prod` now has a full recorded run on today's code.
- 2026-11-18: 2.3 closed: the Git server placeholder is replaced by a bootstrap (owner, lab key, one repository per app in `git_apps`, a seed app in each), `prod`'s Git settings now form the address the role clones, and infra verify lists every repository from the controller. `prod`'s infra stage passes with eleven containers. The run found that the AlmaLinux nodes had no `scp` (6.6, fixed). Evidence: `docs/history/verification-2026-11-18-prod-infra-and-git-server.md`.
- 2026-11-18: `infra` names its destroy sequence, which removes a false "Missing playbook" warning Molecule printed on every infra destroy (5 times in the day's logs); `dev` infra test and destroy now print none.
- 2026-11-18: 4.1 closed: every base image is pinned by tag and digest, and Gitea, go-task, uv and the controller's Python have exact versions. All five images rebuild and `small` passes a full workflow on them. `prod`'s infra scenario also passes on them.
- 2026-11-18: 3.3 closed: the lab's published ports bind to `127.0.0.1` unless `LAB_BIND_ADDRESS` widens them (in place since 3.10), and the Git server now refuses sign-up (HTTP 403) while the bootstrap still creates its owner. Evidence: `docs/history/verification-2026-11-18-prod-infra-and-git-server.md`.
- 2026-11-18: day0 verify prints the same failure diagnostics as day1, from one shared task file; the process list reads `/proc`, because the AlmaLinux image has no `ps` (`docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`).
- 2026-11-18: 3.4 closed: the controller no longer mounts the Docker socket; `dev` passes a full workflow and infra verify without it (`docs/history/verification-2026-11-18-dev-topology-and-operator-path.md`).
- 2026-11-18: 3.8 closed: a systemd unit in both node images turns checksum offload off at every boot, replacing the one-off task in prepare; it holds across a container restart on Ubuntu and AlmaLinux nodes (`docs/history/verification-2026-11-18-prod-infra-and-git-server.md`).
- 2026-11-18: 3.6 closed with a check in `infra/create.yml` that refuses lab host names which already resolve outside the lab.
- 2026-11-18: 3.5 closed with a recorded experiment. Finding for shared hosts: on a privileged node the role's huge-pages unit changes the setting for the whole machine, because containers share the host's kernel.
- 2026-11-18: Regression on the day's last code commit (`7d3d91a`): `prod` infra, `small` and `dms` in full, `dev` with the operator path, and five failure cases all behave as recorded earlier (`docs/history/verification-2026-11-18-final-regression.md`).
- 2026-11-18: Reconciled `prod`'s inventory with what is built: the `splunk_idxc_site` host variables and the `indexer_site1` / `indexer_site2` groups are removed (nothing in the role, the playbooks or the lab read them), and the docs say `splunk-license` is a plain node with no licence file behind it. `prod` infra test passes on the trimmed inventory (`testing/.runs/2026-11-18-prod-infra/sites-prod-infra-test.log`, local). A real licence manager needs a licence file, which the lab does not have.
- 2026-11-18: 5.6 closed: the `ansible-lint` hook moves from v24.9.2, which crashed on import, to v26.11.0, and now also covers `testing/molecule/`; `.ansible-lint` mocks the three `community.docker` modules the lab uses; upstream's `local_config_102.j2` is excluded from the two whitespace hooks so it stays as upstream ships it. `pre-commit run --all-files` passes all four hooks, and the lint hook fails on a probe playbook with a non-FQCN module. The role, playbooks and environments pass the newer lint unchanged. The version bump is also a fix upstream needs.
- 2026-11-18: 3.12 fix landed and proven in a probe on Podman; the lab's own run on Podman is owed. The spec's requirements, design and tasks were also corrected in eleven places where one line contradicted another (found while the Board tab was regenerated).
- 2026-11-18: The search head cluster half of 2.1 is verified: with Splunk's free-disk floor lowered for the test, day0 verify reports both members Up, and fails when one is stopped (`docs/history/verification-2026-11-18-cluster-formation.md`). 2.1 stays open only for the two clusters together in a full `prod` run.
- 2026-11-18: The day's larger runs filled the container engine's disk on the Mac, which is shared with other work. Added 6.7: day0 now checks free disk before any install. No more Splunk installs are run on this Mac for the lab; `prod`, 5.5 and the whole-day0 check for 6.7 go to a machine with its own engine. The lab's `software/`, `.runs/` and `.build/` folders are marked to stay out of Dropbox sync on this checkout. Also corrected seven more lines where the spec contradicted itself, and day0 verify's indexer report now says so when a topology has a manager and no indexers.
