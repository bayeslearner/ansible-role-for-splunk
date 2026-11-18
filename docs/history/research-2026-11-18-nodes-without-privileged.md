# Research: can lab nodes run without `privileged`?

- **Date:** 2026-11-18, for spec 05 task 3.5.
- **Engine:** Docker 29.8.2 (OrbStack) on macOS arm64; cgroup v2, cgroupfs driver, kernel 7.2.12. One engine only: the pve2 VM and the pre-production host were not tried.
- **Code:** node images and playbooks on the tree at `e18562f`.
- **Raw output:** `testing/.runs/2026-11-18-dev/unpriv-*.log` on the machine that ran it (not committed).

## Answer

On this engine a node boots and runs Splunk without `privileged`, given the host cgroup namespace, `/sys/fs/cgroup` mounted read-write and the `NET_ADMIN` capability. One thing the role installs does not work there: its `disable-thp.service`, which writes to `/sys/kernel/mm/transparent_hugepage`. That path is read-only in a container that is not privileged.

The lab keeps `privileged: true` (decision 7 in `docs/decisions/2026-11-18-02-lab-behaviour-changes.md`): the lab exists to exercise the role as it runs on a real host, and a node where one of the role's units always fails is a different target. `cgroupns_mode: host` is required either way.

## What was tried

Booting the Ubuntu node image with `/usr/sbin/init`, `--tmpfs /run --tmpfs /run/lock --tmpfs /tmp`, and:

| Flags | Result |
|---|---|
| `--privileged --cgroupns=host`, `/sys/fs/cgroup` rw (what the lab does) | systemd `running`, sshd active |
| `--privileged --cgroupns=private`, no cgroup mount | the container exits at once, with no log output |
| not privileged, `--cgroupns=private` | exits at once |
| not privileged, `--cgroupns=private`, `--cap-add SYS_ADMIN` | exits at once |
| not privileged, `--cgroupns=host`, `/sys/fs/cgroup` rw | systemd `degraded`: only `lab-veth-offload.service` failed ("netlink error: Operation not permitted") |
| the same plus `--cap-add NET_ADMIN` | systemd `running`, no failed unit, on both the Ubuntu and the AlmaLinux image |

Then the real thing, on `dev`, with the node started as in the last row (`privileged=false capadd=[NET_ADMIN]`, read back with `docker inspect`):

| Step | Result |
|---|---|
| `task workflow:quick` (infra, Splunk install, day0 verify) | exit 0 |
| `task day1:test` (restart, status, licence, verify) | exit 0 |
| `systemctl --failed` on the node | one unit: `disable-thp.service`, "cannot create /sys/kernel/mm/transparent_hugepage/enabled: Read-only file system" |

The create playbook was changed only for this test and restored afterwards.

## A consequence for a shared host

Transparent huge pages are a setting of the kernel, and containers share the host's kernel. On a privileged node the role's unit succeeds, which means it changes the setting for the whole machine the lab runs on, not for the node. On this engine the value read `always madvise [never]` after the day's runs. On a host that runs other workloads, that is a change the lab makes to them. It belongs in the host facts task 3.1 asks for, before the lab runs on a shared host.

## Not covered

- cgroup v1 hosts, and engines with the systemd cgroup driver.
- Podman.
- An AlmaLinux node with Splunk installed (boot only was tried).
- The controller without `privileged`.
