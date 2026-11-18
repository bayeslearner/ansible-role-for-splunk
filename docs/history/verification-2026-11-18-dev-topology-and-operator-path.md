# Verification: the `dev` topology, the operator path, and a regression caught

- **Date:** 2026-11-18
- **Code:** the working tree on top of `234c8aa` (`main`), committed with this record.
- **Host and runner:** as in `verification-2026-11-18-small-topology.md`.
- **Raw output:** `testing/.runs/2026-11-18-dev/` on the machine that ran it (not committed).

All commands run from `testing/`.

## Regression in `234c8aa`, fixed here

The first `MOLECULE_ENV=dev task workflow:quick` after `234c8aa` failed at day0 converge. `dev`, `small` and `dms` each have an `indexer` group for a standalone indexer and no `clustermanager`, so the new "Join the indexers to the cluster as peers" play tried to join a manager that does not exist and failed after six tries. The peer play and the search-head play now also require a `clustermanager` group. After the fix:

| Command | Result |
|---|---|
| `MOLECULE_ENV=small task workflow:full` | exit 0 (`small-after-clusters.log`) |
| `MOLECULE_ENV=dev task workflow:quick` | exit 0; `[day0 > converge]` and `[day0 > verify]` "Executed: Successful" (`dev-quick.log`) |
| `MOLECULE_ENV=dev task day1:test` | exit 0 (`dev-day1.log`) |

`dms` (Splunk Enterprise 10.6.1.1) was run later the same day on the tree at `cb98458`: `MOLECULE_ENV=dms task download:splunk` exit 0, then `MOLECULE_ENV=dms task workflow:full` exit 0 with 10 Molecule steps "Executed: Successful" (`dms-download.log`, `dms-full.log`). That is its first run on Docker; its earlier record is from Podman on the pre-production host.

## Setup run twice (task 1.1)

A second `task setup` on the host that had already run it: exit 0, with `setup:secrets`, `setup:images` and `network:create` reported "up to date", the download play `changed=0`, and "Molecule runner already running" (`setup-second.log`). The first run is in the `small` record. Neither ran on a host that had never seen the lab; this Mac had old Splunk packages in `testing/software/` and existing secrets.

## From the controller, no flags (task 1.4)

On the `dev` lab, as `ansible` in an interactive shell on `ansible-controller`:

- `ansible all -m ping -o`: `splunk-dev` and `ansible-controller` answered `pong`.
- `ansible-playbook /workspace/testing/molecule/day0/verify.yml`: `failed=0` on `splunk-dev` and `localhost`.

## Web terminal login (task 1.5)

`curl` against `http://localhost:3000/ttyd/`: HTTP 200 with the generated password, 401 with a wrong password, 401 with none. `/ttyd` without the trailing slash answers 301 to `/ttyd/`.

## Diagnostic targets (task 5.3)

| Target | Lab state | Exit |
|---|---|---|
| `task diag:ssh` | healthy | 0 |
| `task diag:ssh` | `sshd` stopped on `splunk-dev` | 201 |
| `task diag:terminal` | healthy | 0 |
| `task diag:terminal` | `ttyd` stopped | 201 ("Expected 401 from the password prompt, got 502") |

## Download default (task 2.6)

`MOLECULE_ENV= task download:splunk` (the variable set but empty): `failed=0`.

## Memory, one reading after day1

`splunk-dev` 763 MiB, `ansible-controller` 82 MiB.

## A failed day0 used to delete the lab (task 5.2)

Found after the runs above, on the tree at `9735f35`, and fixed in the commit that adds this section.

`task day0:test` runs `molecule test -s day0`. When a step fails, `molecule test` runs the scenario's destroy step, and `day0/destroy.yml` removed the controller and every node. Their data volumes stayed behind, which is the stale-volume state that fails the next day0.

| Tree | Steps on `dev` | Result |
|---|---|---|
| before | `task infra:setup`; `systemctl stop sshd` on `splunk-dev`; `task day0:test` | exit 201; the log shows "Stop and remove ansible-controller" and "Stop and remove Splunk containers"; 0 lab containers left; volume `ansible-splunk-test-splunk-dev-data` left (`bug-day0-before.log`) |
| after | the same | exit 201; no destroy step ran; both containers still up; after restarting `sshd`, `task diag:ssh` answered `pong` (`bug-day0-after.log`) |
| after | `MOLECULE_ENV=dev task workflow:full` | exit 0; 10 Molecule steps "Executed: Successful"; no lab container left (`dev-full-after-fix.log`) |

The fix: `day0:test` and `day1:test` pass `--destroy=never`, and `day0/destroy.yml` is deleted. Removing containers stays with `task infra:destroy`.

## Diagnostics on a failed day0 too

On the tree at `05f3ef7`. day1 verify printed diagnostics for a node that is down; day0 verify only said the unit was inactive. Both now include one shared task file, `testing/molecule/tasks/splunk_diagnostics.yml`.

| Step on `dev` | Result |
|---|---|
| `task workflow:quick` | exit 0 |
| `systemctl stop Splunkd` on `splunk-dev`, then `task day0:verify` | exit 201; before the assert it printed "no splunkd process", the last `splunkd.log` errors and `Active: inactive (dead)` (`diag2-day0-neg.log`) |
| the same stopped node, `task day1:verify` | exit 201 with the same diagnostics (`diag-day1-neg.log`, from the first draft of the shared file) |
| Splunk started again, `task day0:verify` and `task day1:test` | exit 0 |

Two defects in the earlier diagnostics were fixed on the way. The process list used `ps` piped to `grep`, which listed its own shell command as a Splunk process; and the AlmaLinux node image has neither `ps` nor `pgrep`, so on those nodes it would always have said no process. The list now reads `/proc` directly: with Splunk running on `splunk-dev` it printed the two `splunkd` processes, and the same loop was tried in both node images.

Not run: the diagnostics on an AlmaLinux node with Splunk installed (those nodes exist only in `prod`).

## The controller without the Docker socket (task 3.4)

On the tree at `1f75b5f`. `infra/create.yml` mounted the host's Docker socket into `ansible-controller`, read-only. A read-only mount of that socket still lets whoever is on the controller drive the whole engine, and nothing on the controller used it: the image has no Docker client, and no playbook run from the controller uses the Docker connection. The mount is removed, with the `HOST_DOCKER_SOCK` variable that only fed it.

| Step on `dev` | Result |
|---|---|
| `task workflow:full` | exit 0, no failed step (`sock-dev-full.log`) |
| `docker inspect ansible-controller`, mounts | the repo at `/workspace`, `/sys/fs/cgroup`, and `.secrets`; no socket |
| `ls /var/run/docker.sock` on the controller | "No such file or directory" |
| `molecule verify -s infra` | exit 0 (`sock-verify.log`) |

The runner still mounts the socket; that is how Molecule creates the lab's containers.

## Lab names that already resolve are refused (task 3.6)

On the tree at `de7cf83`. The lab reaches its hosts by container name, and several names look like real host names. On a machine whose DNS search domains resolve such a name, a playbook run outside the lab network could reach a real host. `infra/create.yml` now looks up every lab host name from the runner, which is not on the lab network during infra, and stops before creating anything if one resolves.

| Step on `dev` | Result |
|---|---|
| `molecule create -s infra` in a runner started with `--add-host splunk-dev:10.9.9.9` | exit 2: "These lab host names already resolve outside the lab, so they could reach a real host: 10.9.9.9 splunk-dev"; no lab container created (`names-neg.log`) |
| `task infra:test` with no such name | exit 0; 6 steps "Executed: Successful" (`names-ok.log`) |

The lookup uses the resolver of the container the runner starts in, which takes its DNS servers and search domains from the engine's host. It was tried with a hosts-file entry, not on a network whose DNS answers for a lab name.

## day0 stops before installing when the engine lacks disk (task 6.7)

On the tree at `bcbf6cf`. Every node keeps Splunk on the container engine's own disk, which the engine's other workloads share. During the day's larger runs that disk filled: the installs failed with "No space left on device", and on a machine that runs other containers a full engine disk also takes those down. `day0/converge.yml` now starts with a play that adds up what the pending installs need (4 GB per Enterprise node, 1 GB per forwarder, nodes that already have Splunk count as 0), adds a 6 GB margin, compares it with the free disk under `/opt`, and stops if it does not fit.

Tested on `dev`'s infrastructure with no Splunk install:

| Run | Result |
|---|---|
| the check with its real numbers (17.3 GB free, one node to install, 10 GB needed) | "Stop when the installs would not fit": `ok` (`disk-ok.log`) |
| the same with the margin forced to 500 GB (`-e lab_disk_gb_margin=500`) | exit 2: "Not enough disk for this topology: 17.3 GB free under /opt, and installing Splunk on 1 node(s) needs about 504 GB including a 500 GB margin. Free disk on the container engine, pick a smaller topology (MOLECULE_ENV), or run the lab elsewhere." (`disk-neg.log`) |

Not run: a whole day0 with the new first play followed by an install. Both test runs selected the play with a temporary tag, which made a later role play fail for an unrelated reason; the tag is removed. The playbook passes a syntax check.

By this check's numbers, `prod` (eight Enterprise nodes and one forwarder) needs 39 GB free, `small` 14 GB, and `dev` or `dms` 10 GB.
