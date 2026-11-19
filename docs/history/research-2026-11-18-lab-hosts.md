# Research: the facts of each lab host

- **Date:** 2026-11-18 (the Linux VM's facts were taken at 01:10 UTC on 2026-11-19), for spec 05 task 3.1.
- **Why:** the lab runs systemd in privileged containers and publishes ports, so how it behaves depends on the host's kernel, cgroup version, engine and network. These are the facts to read on a new host before its first run.

## How to take them

On the host, as the user the lab runs as:

```bash
. /etc/os-release; echo "$PRETTY_NAME"; uname -srm
stat -fc %T /sys/fs/cgroup                    # cgroup2fs = cgroup v2
docker version --format '{{.Server.Version}} / CLI {{.Client.Version}}'
docker compose version
id
resolvectl status | grep -i -E 'DNS (Servers|Domain)'
nproc; free -g; df -h /
curl -sS -o /dev/null -w '%{http_code}\n' -I https://download.splunk.com/
curl -sS -o /dev/null -w '%{http_code}\n' https://registry-1.docker.io/v2/
cat /etc/docker/daemon.json
cat /sys/kernel/mm/transparent_hugepage/enabled
```

## The hosts

| Fact | Work Mac and second Mac | Linux VM on the homelab's Proxmox node (`pve-02`) | Pre-production host |
|---|---|---|---|
| OS, kernel | macOS 26, Apple Silicon; the engine's Linux VM (OrbStack, kernel 7.2.12) | Ubuntu 24.04.5 LTS, kernel 6.8.0-147-generic, x86_64 | not yet taken (task 3.9) |
| cgroup | v2, cgroupfs driver | v2 (`cgroup2fs`) | |
| Engine | Docker 29.8.2 (OrbStack); Podman on the second Mac ([record](verification-2026-11-18-lab-on-podman.md)) | Docker 29.1.3, CLI 29.1.3, Compose 2.40.3 (Ubuntu packages) | root Podman and its socket (Log of spec 05, 2026-11-10 and 2026-11-11) |
| Platform the lab builds | `linux/amd64` under emulation (`LAB_PLATFORM`) | `linux/amd64`, native | |
| Lab runs as | the Mac user | `ubuntu`, in the `docker` group, not root | |
| DNS | the Mac's resolver | the router, then two public resolvers; one search domain of the homelab's own | |
| Size | | 4 cores, 8 GiB, 58 GB disk (55 GB free before the run) | |
| Egress | both answer | download.splunk.com 301, Docker Hub registry 401 (both reached) | |
| Docker address pools | the engine's defaults | the homelab's own (`bip` and `default-address-pools` in `daemon.json`), set so container networks do not overlap routed work ranges | |
| Huge pages after a lab run | `always madvise [never]` | `always madvise [never]` (not read before the run) | |

## What the facts change

- **Native x86_64** removes the emulation the Macs need; the same `small` run that takes longer on a Mac took 4 minutes 23 seconds here ([record](verification-2026-11-18-small-on-a-linux-vm.md)).
- **Huge pages.** The role's `disable-thp.service` runs in a privileged node and sets the host kernel's value to `never`. On a host that runs other workloads, the lab changes them ([research](research-2026-11-18-nodes-without-privileged.md)). On the VM the value read `never` after the run; it was not read before, so the change is inferred from the role's unit, not observed.
- **Privileged or not.** Both node images boot to `running` with no failed unit on the VM, privileged and unprivileged (host cgroup namespace, `/sys/fs/cgroup` read-write, `NET_ADMIN`), as on the Mac. The decision to keep nodes privileged (decision 7 of `docs/decisions/2026-11-18-02-lab-behaviour-changes.md`) is unchanged; Splunk was not installed on an unprivileged node here.
- **Address pools.** The lab's network takes whatever subnet the engine assigns. On a host whose pools are set, as on this VM, that subnet stays inside them.
- **Slow package downloads.** On the VM, PyPI served about 64 kB/s during the image build, so `task setup` took 14 minutes 34 seconds. That is the network on the day, not the lab.
