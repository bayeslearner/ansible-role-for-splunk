# Verification: the lab's containers on a Podman engine, and the platform the images are built for

- **Date:** 2026-11-18.
- **Code:** the working tree on top of `005a911` (`main`), committed with this record.
- **Engine:** Podman 6.0.2 on the first Mac: its default machine (Fedora CoreOS, arm64, rootless, cgroup v2, SELinux enforcing, 2 GiB of memory). `docker` on the path was a link to `podman`, as on a host with only Podman installed. The engine socket given to the runner was the machine's rootless one (`DOCKER_SOCK=/run/user/<uid>/podman/podman.sock`).
- **Raw output:** `testing/.runs/2026-11-18-podman/` on that machine (not committed).

No Splunk was installed in this test; it covers the image builds and the infra scenario's create step, which is what task 3.12 asks for.

## Result for task 3.12

| Step | Result |
|---|---|
| `task setup:images`, with no platform variable in the environment | exit 0; five images stored as `localhost/<name>:latest`, each `amd64` |
| `MOLECULE_ENV=dev task infra:create` | `[infra > create] Executed: Successful`: `ansible-controller` and `splunk-dev` created from the `localhost/…` images, no pull attempted; `splunk-dev` runs systemd as PID 1 on `x86_64` |
| `LAB_NAME=p LAB_PORT_OFFSET=400 MOLECULE_ENV=prod task infra:create` | `[infra > create] Executed: Successful`: all eleven containers created, the two AlmaLinux nodes and the Git server included, no pull attempted; ports 3400, 2622 and 9329 published |
| `LAB_NAME=p … MOLECULE_ENV=small task reset`, then `MOLECULE_ENV=dev task reset` | exit 0 each; no lab container, volume or network left in the Podman store |

`molecule create` also runs the scenario's prepare step, and that step failed on this engine, so both `task infra:create` commands exited non-zero after their create step had succeeded. See "Not shown here".

## Three things the attempt found

1. **The images were amd64 only because of a variable in one person's shell.** Both Macs used so far have `DOCKER_DEFAULT_PLATFORM=linux/amd64` set outside the lab. Podman ignores that variable, built arm64 images, and the runner image failed to build ("Failed building wheel for onigurumacffi": no arm64 wheel). On Docker without the variable the same would happen, and Splunk's x86_64 packages could not run in arm64 node images anyway. The Taskfile now passes `--platform` (`LAB_PLATFORM`, default `linux/amd64`) to every build and every runner start. After the change, the five images built as amd64 under Podman with the variable unset.
2. **SELinux blocks the runner from the engine socket.** With SELinux enforcing, the runner got "Permission denied" opening the socket mounted into it. Probed directly: a request to `/version` over the mounted socket fails with `PermissionError: [Errno 13]`, and returns 200 when the same container is started with `--security-opt label=disable`. The Taskfile has a new setting, `LAB_RUNNER_ARGS`, empty by default, whose value is added to the runner's arguments; `LAB_RUNNER_ARGS='--security-opt label=disable'` was used for the runs above.
3. **The Docker CLI's builder does not see Podman's local images.** With the real `docker` client pointed at the Podman socket, building the controller image failed at `FROM localhost/splunk-base-ubuntu2204:latest`: that client builds through its own builder container, which looked for a registry named `localhost`. With `podman` as the build command the same Dockerfile builds. A Podman host should build with `podman` (or the `podman-docker` package), not a separately installed Docker client.

## The same Taskfile on Docker

On the second Mac (Docker under OrbStack), with `DOCKER_DEFAULT_PLATFORM` unset and one image removed first so it had to be rebuilt:

| Step | Result |
|---|---|
| `MOLECULE_ENV=prod task infra:test` | exit 0, six "Executed: Successful" |
| the rebuilt `localhost/splunk-git-server:latest` | `amd64` |

## Not shown here

- **The prepare step on this engine.** It failed on every node with "Docker version check … failed: SIGSEGV": the `docker` client inside the amd64 runner crashes under this machine's emulation of amd64. The Docker connection that prepare uses calls that client. On the pre-production host (x86_64, root Podman) prepare and day0 (converge and verify) passed on 2026-11-10 and 2026-11-11 with nothing emulated; day1 was not run there, so this is a limit of an ARM machine running the lab under Podman, not of Podman.
- A rootful Podman engine with today's code, and an x86_64 Linux host with today's code (tasks 3.2 and 3.9).

## Left as found

The lab's images, containers, networks and volumes were removed from the Podman store and the machine was stopped, as it was before. One mistake in the cleanup: `podman image prune -a` also removed two unrelated images that were in the store before the test (`caddy:2-alpine` and `alpine:3.20`). Both were pulled again; `alpine:3.20` is the same image, `caddy:2-alpine` is now a newer build than the one that was there.
