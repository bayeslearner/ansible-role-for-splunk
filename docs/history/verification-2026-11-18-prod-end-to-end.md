# Verification: `prod` end to end

- **Date:** 2026-11-18, 12:42 to 13:30 UTC.
- **Code:** the working tree on top of `4b6553c` (`main`), committed with this record. Two fixes were made during the run and are part of that tree: the AlmaLinux node image installs `procps-ng`, and `setup:secrets` sets the key's file mode every time.
- **Host:** a second Mac (Apple Silicon, 128 GB memory) with its own Docker engine: Docker 29.8.2 under OrbStack, 47 GB given to the engine, 102.8 GB of engine disk free at the start. Images built as `linux/amd64` (`DOCKER_DEFAULT_PLATFORM`), so Splunk runs emulated, as on the first Mac.
- **Topology:** `MOLECULE_ENV=prod`: eleven containers. Splunk Enterprise 9.4.2 on eight nodes, a Universal Forwarder on one, the Git server, the controller.
- **Raw output:** `~/lab-runs/2026-11-18-prod/` on that machine, outside any synced folder (not committed).

All commands run from `testing/`.

## Runs

| Step | Result |
|---|---|
| `task setup` | exit 0: the five `localhost/…` images built from the pinned Dockerfiles, Splunk 9.4.2 packages downloaded (`setup.log`) |
| `MOLECULE_ENV=prod task workflow:quick` | exit 0 (`p3-quick.log`): infra, then day0 converge "Executed: Successful" with the disk check in front, the install on nine nodes and both clusters formed; day0 verify printed "splunkapp-prod01, splunkapp-prod02 are Up peers of splunk-master" and "splunkshc-prod01, splunkshc-prod02 are Up members of the search head cluster" |
| `MOLECULE_ENV=prod task day1:test` | exit 0 (`p3-day1.log`): restart, status and licence on every node, verify passed |
| `task day0:verify` again, about five minutes after day1 | exit 0, both clusters reported Up again (`p3-verify-again.log`) |
| `task infra:destroy` | exit 0; no lab container left; only the Git server's volume remains; engine disk back to 100.9 GB free |

Read back on the running lab, outside the playbooks:

| What | Result |
|---|---|
| `splunk show cluster-status` on `splunk-master` | "Replication factor met", "Search factor met"; `splunkapp-prod01` and `splunkapp-prod02` each `Searchable YES`, `Status Up` |
| `splunk show shcluster-status` on `splunkshc-prod01` | a dynamic captain (`splunkshc-prod02`), `service_ready_flag : 1`, both members `status : Up` |
| `deploymentclient.conf` on `splunk-uf01` | `targetUri = splunk-fwdmanager:8089`, `clientName = test-uf01`, as the inventory sets them |
| `splunk list deploy-clients` on `splunk-fwdmanager` | one client: `clientName: test-uf01`, `hostname: splunk-uf01` |

This is the first run in which the two clusters formed in one lab.

## Found by this run

1. **A synced checkout loses the lab key's file mode.** The first pass failed at day0's first SSH step on every node: "WARNING: UNPROTECTED PRIVATE KEY FILE! Permissions 0644 for '/workspace/testing/.secrets/id_rsa' are too open … This private key will be ignored." The checkout on this machine arrived through a file sync, which does not carry file modes, and `setup:secrets` only set the mode when it created the key. It now runs `chmod 600` on the key, the password file and the secrets inventory every time, and reruns when the key's mode is wrong.
2. **The AlmaLinux node image had no `ps`, so Splunk's own command line did not work there.** The second pass installed Splunk on all nine nodes, then failed joining the two AlmaLinux nodes to the clusters. Run by hand on `splunkapp-prod02`, `splunk edit cluster-config` printed "/opt/splunk/bin/pid_check.sh: line 70: ps: command not found" and "needs splunkd to be up, but splunkd is unreachable", while the service was active. The same command on the Ubuntu indexer succeeded. The image now installs `procps-ng`. Neither half-size cluster test included an AlmaLinux node with Splunk installed, which is why this did not show earlier.

The third pass, from a clean lab on the rebuilt image, is the one in the table above.

## Disk and memory (task 5.5, `prod` only)

Engine disk: 28.2 GB used before the lab, 63.4 GB with `prod` installed and both clusters formed: 35.2 GB for the lab, images included. day0's check asks for 39 GB free for `prod`, which this confirms as about right.

`docker stats --no-stream`, one reading each:

| Container | Right after day0 | Five minutes after day1 |
|---|---|---|
| `splunk-master` | 962 MiB | 729 MiB |
| `splunk-license` | 704 MiB | 677 MiB |
| `splunk-fwdmanager` | 658 MiB | 670 MiB |
| `splunk-deploy` | 663 MiB | 704 MiB |
| `splunkapp-prod01` | 908 MiB | 813 MiB |
| `splunkapp-prod02` | 854 MiB | 804 MiB |
| `splunkshc-prod01` | 695 MiB | 667 MiB |
| `splunkshc-prod02` | 925 MiB | 712 MiB |
| `splunk-uf01` | 184 MiB | 167 MiB |
| `git-server` | 155 MiB | 153 MiB |
| `ansible-controller` | 73 MiB | 74 MiB |
| **Total** | **6.6 GiB** | **6.0 GiB** |

Each Splunk Enterprise node also held about one CPU core while otherwise idle. These nodes run amd64 Splunk under emulation on an ARM host, so that CPU figure says little about a native host. The lab carried no data and ran no searches.

## Not covered

- A native amd64 Linux host, and Podman.
- The search head cluster with a member stopped, in the full lab (shown in the half-size lab).
- The role's app deployment from the Git server (day 2, spec 10).
- Memory and CPU for the other three topologies on this host, and any figure under load.
