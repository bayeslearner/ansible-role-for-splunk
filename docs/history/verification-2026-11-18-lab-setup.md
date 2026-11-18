# Verification: `task setup` on a machine that never had the lab

- **Date:** 2026-11-18.
- **Code:** `4b6553c` plus the two fixes of the `prod` record for the first run; `2b81607` for the secrets run.
- **Hosts:** the second Mac of the `prod` record, which had none of the lab's images, packages or network before that day; and an empty copy of the Taskfile on the first Mac for the secrets step.
- **Raw output:** `~/lab-runs/2026-11-18-prod/setup.log` and `~/lab-runs/2026-11-18-sizes/small-setup.log` on the second Mac (not committed).

Task 1.1 asks for two runs of `task setup` on a clean host. This record shows each thing the first run creates on a machine that lacked it, and the second run skipping. It is assembled from two machines, for the two reasons under "Not one unbroken run".

## First run, second Mac

`task setup`, exit 0 (`setup.log`, 3,287 lines):

| Step | Result |
|---|---|
| `setup:secrets` | "up to date": the secrets were already in the checkout (see below) |
| `setup:images` | all five built: "naming to `localhost/splunk-base-almalinux9:latest` done", and the same line for `splunk-base-ubuntu2204`, `splunk-ansible-controller`, `splunk-git-server` and `molecule-runner`; the runner installed `ansible-core-2.21.6` |
| `download:splunk` | "Download Splunk Enterprise" changed, "Download Splunk Universal Forwarder" changed; `changed=2 failed=0` |
| `network:create` | created `splunk-test-network` (the engine printed its id) |

The lab built on those images then ran `prod` end to end ([record](verification-2026-11-18-prod-end-to-end.md)).

## Second run, same machine

`task setup` again, later the same day, exit 0 (`small-setup.log`, 25 lines):

| Step | Result |
|---|---|
| `setup:secrets` | "up to date" |
| `setup:images` | "up to date" |
| `download:splunk` | runs its play, both downloads `ok`; `changed=0` |
| `network:create` | "up to date" |

The download step is the one step that is not skipped by the Taskfile: its play runs each time and finds the files present.

## Secrets, in an empty directory

A copy of `testing/Taskfile.yml` alone in an empty directory on the first Mac, so nothing existed:

| Step | Result |
|---|---|
| `task setup:secrets` | exit 0, "Secrets OK". Created `id_rsa` (mode 600), `id_rsa.pub`, `ansible_password` (600), `inventory/inventory.yml`, and `inventory/group_vars/all.yml` (600) holding `splunk_admin_password` and `gitea_secret_key` |
| `task setup:secrets` again | "up to date" |
| after `chmod 644` on the key, `task setup:secrets` | the key is back at mode 600 |

The scratch directory and its secrets were deleted afterwards.

## Not one unbroken run

- **Secrets were not generated on the second Mac.** Its checkout arrives through a file sync, which had already delivered the first Mac's `.secrets/`. That is why the generation is shown separately. It also means two machines shared one set of lab secrets, which the lab does not intend; a checkout made with `git clone` has no `.secrets/` and generates its own.
- **The five base images were pulled before `task setup` on the second Mac,** through the engine's API. `docker build` in that machine's non-interactive session could not use the desktop credential store to pull. On a host with a normal login session, `setup:images` pulls them itself, as it did on the first Mac.

## Not covered

- A Linux host, and Podman.
- `task setup` with `MOLECULE_ENV=dms`, which downloads a second Splunk version; the `dms` run in the [sizing record](verification-2026-11-18-memory-and-disk-per-topology.md) went through it with exit 0.
