# Verification: memory, CPU and disk per topology

- **Date:** 2026-11-18, 13:34 to 14:25 UTC for `small`, `dev` and `dms`; `prod` earlier the same day ([record](verification-2026-11-18-prod-end-to-end.md)).
- **Code:** `7da4eeb` (`main`).
- **Host:** the second Mac of the `prod` record: Apple Silicon, Docker 29.8.2 under OrbStack with 44 GiB of memory visible to containers. The lab's images are amd64 and run emulated. Five unrelated containers were running on the same engine; none belongs to the lab and their memory is not counted below.
- **Raw output:** `~/lab-runs/2026-11-18-sizes/` on that machine (not committed).

## Runs

For each of `small`, `dev` and `dms`, one after another, from `testing/`: `task setup`, `task workflow:quick`, `task day1:test`, `task infra:destroy`. All twelve commands exited 0. Each `workflow:quick` log has six "Executed: Successful" lines and each `day1:test` log two.

`docker stats --no-stream` was read three times per topology: right after day0, five minutes after day1, and one minute after that.

## Memory and CPU per container

| Topology | Container | Right after day0 | 5 min after day1 | 6 min after day1 |
|---|---|---|---|---|
| `small` | `splunk-license` | 181 MiB, 93% | 803 MiB, 202% | 649 MiB, 102% |
| `small` | `splunkapp-prod01` | 193 MiB, 93% | 798 MiB, 185% | 677 MiB, 101% |
| `small` | `ansible-controller` | 74 MiB, 0% | 75 MiB, 0% | 75 MiB, 0% |
| `dev` | `splunk-dev` | 132 MiB, 94% | 641 MiB, 101% | 636 MiB, 105% |
| `dev` | `ansible-controller` | 73 MiB, 0% | 74 MiB, 0% | 74 MiB, 0% |
| `dms` | `splunk-dms` (Splunk 10.6.1.1) | 179 MiB, 91% | 1.47 GiB, 79% | 1.42 GiB, 28% |
| `dms` | `ansible-controller` | 73 MiB, 0% | 75 MiB, 0% | 75 MiB, 0% |

100% is one core. The low reading right after day0 is a node whose server has only just started; it is not a resting figure. The readings after day1 are the ones to size by.

## Per topology

| Topology | Splunk nodes | Lab memory after day1 | Engine disk with the lab installed |
|---|---|---|---|
| `dev` | 1 (9.4.2) | 0.7 GiB | about 3.3 GB |
| `dms` | 1 (10.6.1.1) | 1.5 GiB | 4.2 GB |
| `small` | 2 (9.4.2) | 1.4 to 1.7 GiB | 6.3 GB |
| `prod` | 8 and a forwarder (9.4.2) | 6.0 to 6.6 GiB | 35.2 GB |

Splunk 9.4.2 took 640 to 810 MiB per Enterprise node at rest across all runs, and about one emulated core; Splunk 10.6.1.1 took twice the memory. The disk figures include the unpacked install and what day0 wrote; `prod`'s also includes cluster bundles.

## What this does and does not give

- **Measured:** a lab that has just been installed and restarted, with no data indexed and no searches run. Memory during the install itself was not sampled.
- **Known to work:** `small`, `dev` and `dms` each passed full workflows on an engine with 15.66 GiB (the earlier records of this day). `prod` passed on an engine with 44 GiB.
- **Not measured:** the smallest engine each topology still passes on. The READMEs suggest twice the resting figure as a floor; that is a rule of thumb and no run was made at that limit.
- **Disk for `dev`:** the reading before its install was lost (the script's disk reading failed; see below), so its figure is the installed reading minus the engine's level after the lab was removed, 32.1 GB.
- **CPU:** emulated amd64 on an ARM host. A native amd64 host will differ.

## Fault in the measuring script

The script read engine disk with `docker run alpine df` while `DOCKER_DEFAULT_PLATFORM=linux/amd64` was set; the machine had only the arm64 image and could not pull, so those readings were empty. The disk figures above were read by hand at the same points with `df` inside the lab's controller. This is a fault in the one-off script, not in the lab.
