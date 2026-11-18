# Verification: cluster formation, in two halves

- **Date:** 2026-11-18
- **Code:** the working tree on top of `115e63d` (`main`), committed with this record.
- **Host:** macOS 27.2 on arm64, Docker engine 29.8.2 (OrbStack), 15.66 GiB memory and 16 to 17 GB of free engine disk. Splunk Enterprise 9.4.2, amd64 images, emulated.
- **Runner:** Molecule 25.12.0, ansible-core 2.21.6.
- **Raw output:** `testing/.runs/2026-11-18-clusters/` on the machine that ran it (not committed).

## Why halves

`MOLECULE_ENV=prod task workflow:quick` failed at the Splunk install on all eight Enterprise nodes with `tar: … Cannot write: No space left on device` (`prod-quick.log`). An installed node took 2.7 GB of engine disk here (three nodes grew the volumes by 8.1 GB), and each node also holds the 1.1 GB package while it unpacks, so `prod` needs about 22 GB steady and about 30 GB at its peak. This engine had 16 to 17 GB free, most of the rest held by other projects' images and volumes.

To exercise the new plays, two temporary topologies were cut from `prod`, with `prod`'s own `group_vars`, and removed afterwards:

- indexer half: `splunk-master`, `splunkapp-prod01`, `splunkapp-prod02`, the controller;
- search head half: `splunk-master`, `splunk-deploy`, `splunkshc-prod01`, `splunkshc-prod02`, the controller.

## Indexer cluster: verified

| Step | Result |
|---|---|
| `task workflow:quick` | exit 0. day0 converge ran the manager and peer plays; verify printed "splunkapp-prod01, splunkapp-prod02 are Up peers of splunk-master" (`idxc-quick.log`) |
| `task day0:converge` again on the clustered lab | exit 0; the peer play skipped both nodes (`idxc-converge-again.log`) |
| `systemctl stop Splunkd` on `splunkapp-prod02`, then `task day0:verify` | exit 201 (`idxc-neg-verify.log`). Two checks failed: the service assert on the stopped node ("Splunkd is inactive on splunkapp-prod02"), and, on `splunk-master`, "Wait until every indexer is an Up peer of the manager" after all 30 tries. |

Memory right after day0, one `docker stats` reading: `splunk-master` 978 MiB, `splunkapp-prod01` 802 MiB, `splunkapp-prod02` 814 MiB.

## Search head cluster: formed, verify could not pass on this host

Four nodes installing at once ran out of disk, so Splunk was installed two nodes at a time (`molecule converge -s day0 -- --limit 'splunk-master:splunk-deploy'`, then the full converge).

| Step | Result |
|---|---|
| day0 converge | exit 0. The search heads joined the indexer cluster, the deployer was configured, both members were initialised and restarted, and "Bring up cluster captain" reported `changed` on `splunkshc-prod01` (`shc-converge.log`) |
| `splunk show shcluster-status` on a member | a captain elected (`splunkshc-prod01`, `service_ready_flag : 1`) and both members listed |
| `task day0:verify` | exit 201 after 30 tries: the members endpoint answered HTTP 503 |

Both members showed `status : AutomaticDetention`. `splunkd.log` gives the cause: `DiskMon - MinFreeSpace=5000. The diskspace remaining=2207 is less than 1 x minFreeSpace`. With four nodes installed the engine disk had 2.2 GB free, under Splunk's 5 GB floor, so Splunk detained the members. Verify failing here is the check doing its job; what is not shown is the same check passing on a healthy search head cluster.

Two defects in the first draft of the new plays were found and fixed during these runs:

- the captain check used `splunk_auth`, whose user name comes from the role's defaults and is undefined in a play that does not load the role;
- `splunk show shcluster-status` exits 0 on a member that has not joined a cluster, so the bootstrap was skipped until the check also read the command's words.

## Second attempt at the search head half, same day

After the Git server and image work (tree at `c1f4906`), the four-node search head half was started again, to lower Splunk's free-disk floor on the members for the test and see the member check pass. It did not get that far: with two nodes installed, the install of the two search heads failed with `tar: … Cannot write: No space left on device` (`shc2-converge.log`). The day's image rebuilds had taken the engine's free disk from about 17 GB to 14.4 GB. The lab was torn down and the temporary topology removed. A healthy search head cluster is still unshown.

## Not covered

- `prod` as a whole (eleven containers) has not run. It needs a host with about 30 GB of free engine disk; memory for nine Splunk nodes at 0.8 to 1 GiB each is 8 to 9 GiB before load.
- The search head cluster verify passing, and its member-count check failing on a fault of its own (it failed here because of the disk, not a stopped member).
- Day 1 on a clustered lab.
