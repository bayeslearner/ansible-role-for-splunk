# Verification: `small` end to end on a Linux Docker VM

- **Date:** 2026-11-18 (run from 01:15 to 01:35 UTC on 2026-11-19)
- **Code:** `d2ee3b7` (`main`), a fresh clone from GitHub.
- **Topology:** `MOLECULE_ENV=small`: `splunk-license`, `splunkapp-prod01`, `ansible-controller`. Splunk Enterprise 9.4.2.
- **Host:** a throwaway Linux VM on the homelab's Proxmox node `pve-02` (the "pve2 VM" of spec 05): Ubuntu 24.04.5, kernel 6.8, x86_64, 4 cores, 8 GiB, 58 GB disk, Docker 29.1.3 as a non-root user in the `docker` group. Its facts: [research-2026-11-18-lab-hosts.md](research-2026-11-18-lab-hosts.md). The VM was made for this run and deleted after it.
- **Added to the VM before the run:** go-task 3.54.0 (the version CI pins) in `~/.local/bin`, and the clone. Nothing else; Docker came with the VM.
- **Runner:** built during `task setup`: Molecule 25.12.0, ansible-core 2.21.6, Python 3.12.
- **Raw output:** `~/lab-runs/pve2/` on the work Mac (`small-full.log`, `host-facts.txt`, `privileged-check.txt`); not committed, the log prints the lab's generated SSH public keys.

## Run

From `testing/` on the VM:

```bash
task setup && MOLECULE_ENV=small task workflow:full
```

| Stage | Result | Time |
|---|---|---|
| `task setup` (secrets, all images built from nothing, Splunk 9.4.2 packages downloaded, network) | exit 0 | 14 min 34 s; most of it PyPI downloads at about 64 kB/s |
| `MOLECULE_ENV=small task workflow:full` | exit 0 | 4 min 23 s |

Inside `workflow:full`, every Molecule step printed "Executed: Successful": infra dependency, create and prepare (twice: once from create's sequence, once from `infra:prepare`), day0 converge and verify, day1 converge and verify, infra destroy. No `fatal:` line and no host with `failed` or `unreachable` above zero in any play recap. Day0 verify printed "Splunkd is active" for both Splunk nodes.

After the run: no containers and no volumes on the engine (`docker system df`: 0 containers, 0 local volumes), 50 GB of the disk free.

## Not covered

- `dev`, `dms` and `prod` on this VM; `prod` needs more memory than 8 GiB ([record](verification-2026-11-18-memory-and-disk-per-topology.md)).
- A Splunk install on an unprivileged node; only boot was tried ([research](research-2026-11-18-lab-hosts.md)).
- The pre-production host (task 3.9).
