---
date: 2026-11-18
status: decided
decided_by: the agent; the owner may reverse
---

# Lab behaviour changed on 2026-11-18

Five choices made while closing spec 05 tasks. Each is technical, inside the steering (a lab you operate like production, with checks you can trust), and reversible by reverting its commit. Evidence for each is a verification record under `docs/history/`.

## 1. A destroyed node takes its data volume with it (`115e63d`)

- **Context:** each node keeps `/opt` in a named volume. `infra:destroy` removed the containers and left the volumes, so the next lab found Splunk installed with no systemd unit and the role's boot-start check failed day0.
- **Options:** remove the node volumes in `infra:destroy`; or keep them and repair the unit on reuse; or tell operators to run `task reset` between labs.
- **Choice:** remove them in `infra:destroy`. A volume without its container is not a usable Splunk install, and a teardown that leaves a broken state behind is a trap. The Git server's volume is kept, because its data does not depend on the container.
- **Reversal:** revert the `destroy.yml` task; data on a node then survives a destroy again, with the failure above.

## 2. A failed day0 or day1 leaves the lab running (`ff82f34`)

- **Context:** `molecule test` runs a scenario's destroy step when a step fails, and `day0/destroy.yml` deleted the controller and every node.
- **Options:** pass `--destroy=never` and delete the playbook; or keep the playbook and document the behaviour.
- **Choice:** `--destroy=never`, playbook deleted. The lab that just failed is the one the operator needs to log into. Removing containers stays with `task infra:destroy`.
- **Reversal:** drop the flag from `day0:test` and `day1:test`.

## 3. The controller's Ansible comes from the runner's pin, on Python 3.12 from uv (`b897e40`)

- **Context:** the controller ran Ubuntu's apt ansible 2.10.8; the runner ran ansible-core 2.21.6. This ansible-core needs a newer Python than Ubuntu 22.04 ships.
- **Options:** give the controller Python 3.12 (uv, pinned to 0.8.22) and the runner's version; or lower both to ansible-core 2.17, the newest that runs on Python 3.10; or move the controller to a newer base image.
- **Choice:** uv and the runner's version. It changes one image and keeps the runner, which every recorded run used, exactly as it was. Lowering both would have put all of today's evidence on a different Ansible than the lab ships.
- **Consequence:** `uv` is a tool this repo did not use before. It is a single binary that installs Python versions and packages; here it only supplies the controller's Python. The familiar alternative is the deadsnakes PPA, which cannot be pinned to a version.
- **Reversal:** restore `ansible` in the controller's apt list and remove the uv block.

## 4. Clusters are formed by day0 on `prod`, with guards (`234c8aa`, `a05d639`)

- **Context:** the owner confirmed on the Board that `prod` is meant to form the smallest valid clusters. The role's peer, search-head, member and captain tasks fail when run on a node already configured.
- **Options:** change `prod` or add a new topology; run the role's example playbooks or the role's task files from day0; let a second converge fail or guard it.
- **Choice:** change `prod` (it already has the groups); run the task files from `day0/converge.yml` in the example playbooks' order; check each node first so converge can run twice. The cluster plays need a `clustermanager` group, because `small`, `dev` and `dms` have an `indexer` group for a standalone indexer.
- **Not decided here:** multisite. The inventory names two sites and the role's manager task sets none, so the cluster is single-site.
- **Reversal:** remove the plays after the install play.

## 5. day0 verify fails on a fault (`115e63d`)

- **Context:** a 2026-03-30 preference kept `ignore_errors` on day0 verify. The portfolio plan the owner approved on 2026-11-18 lists "make day0's verify able to fail".
- **Choice:** the service and port checks assert; the Git server check stays informational until it has repositories (task 2.3).
- **Reversal:** this one reverses an earlier owner preference, so it is the first to revisit if the lab should tolerate a half-working day0 again.

## 6. The Git server holds one repository per app, and accepts the lab's RSA 2048 key (added later the same day)

- **Context:** the role clones `<git_server>/<git_project>/<app name>`. `prod` named a single `test/splunk_apps/` project and a key file nothing wrote. Gitea 28.4.0 refuses RSA keys under 3071 bits, and the lab key is RSA 2048 and is never rotated.
- **Options for the layout:** one repository per app under an owner (what the role's address means), or keep one repository and change how the role is called.
- **Choice:** one repository per app under the owner `test`; `prod` sets `git_server: ssh://git@git-server`, `git_project: test` and the lab key as `git_key`. The owner's password is the lab's generated Splunk admin password, so no new secret is added.
- **Options for the key:** lower Gitea's minimum key size in the lab image; generate a separate, larger key for Git; or change the lab key's type, which would change every existing lab.
- **Choice:** lower the minimum in the lab's Gitea image. The server is reachable only on the lab network and on the lab host's loopback address, and one key for the whole lab is the existing design.
- **Reversal:** remove the two `GITEA__ssh…` lines and give Git its own key.

## 7. Nodes stay privileged (added later the same day)

- **Context:** task 3.5 asks whether nodes can run without `privileged`. On Docker with cgroup v2 they can boot and run Splunk with the host cgroup namespace and the `NET_ADMIN` capability, but the role's `disable-thp.service` fails, because `/sys/kernel/mm` is read-only in such a container (`docs/history/research-2026-11-18-nodes-without-privileged.md`).
- **Options:** drop `privileged` and accept one always-failing unit from the role; drop it and skip that part of the role in the lab; or keep `privileged`.
- **Choice:** keep `privileged`. The lab's purpose is to exercise the role as it behaves on a real host.
- **Consequence to weigh on a shared host:** a privileged node lets the role change transparent huge pages for the whole machine. If the lab is to share a host with other workloads, this choice should be revisited for that host.
- **Reversal:** set `privileged: false` and add `capabilities: [NET_ADMIN]` on the nodes in `infra/create.yml`.

## 8. The fork runs its lint on GitHub Actions (added later the same day)

- **Context:** the lint hooks and the spec lint ran only when someone ran them by hand. The fork had no workflow; neither has upstream. Actions is enabled on the fork.
- **Options:** leave lint to the person committing; or add a workflow that runs the same two commands on every push and pull request to `main`.
- **Choice:** add `.github/workflows/lint.yml`: `pre-commit run --all-files` and `python3 scripts/spec_lint.py`, read-only permissions, no secrets, no lab build. It runs on GitHub's free runners for a public repository.
- **Not done:** a lab run in CI. The lab needs privileged systemd containers, the Splunk packages and 10 GB or more of disk; whether to run `dev` there is a separate question.
- **Reversal:** delete the workflow file.
