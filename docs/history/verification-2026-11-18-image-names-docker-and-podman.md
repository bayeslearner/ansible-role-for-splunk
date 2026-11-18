# Verification: image names that Docker and Podman both resolve

- **Date:** 2026-11-18, for spec 05 task 3.12.
- **Code:** the working tree on top of `1911a22` (`main`), committed with this record.
- **Engines:** Docker 29.8.2 (OrbStack) and Podman 6.0.2 (its default machine, rootless, cgroup v2), both on macOS arm64. The Podman machine was started for the probe and stopped afterwards.
- **Raw output:** `testing/.runs/2026-11-18-image-names/` on the machine that ran it (not committed). The Podman probe's output is quoted below; it was not saved to a file.

## The fault, reproduced on Podman

A one-file image was built with `podman build -t labprobe:latest`. Podman stored it as `localhost/labprobe:latest`. Then the module the lab creates containers with, `community.docker.docker_container` 5.4.0 on ansible-core 2.21.6, was pointed at Podman's Docker-compatible socket:

| `image:` given to the module | Result on Podman |
|---|---|
| `labprobe:latest` | FAILED: "Error pulling image labprobe:latest - 500 Server Error … images/create?tag=latest&fromImage=labprobe: Internal Server Error (\"connection refused\")" |
| `localhost/labprobe:latest` | CHANGED: container created from `localhost/labprobe:latest` |

The engine itself accepts the short name: a direct `POST /containers/create` with `"Image":"labprobe:latest"` created a container. The module is what fails, because it looks the image up first, does not match the short name to `localhost/labprobe`, and asks for a pull.

## The same name on Docker

| Check on Docker | Result |
|---|---|
| `docker build -t localhost/labprobe:latest` | built |
| a second image with `FROM localhost/labprobe:latest` | built from the local image, no pull (the same `FROM` also built under `podman build`) |
| the module with `image: localhost/labprobe:latest` | CHANGED: container created |

## The lab on the new names

The five images are now `localhost/molecule-runner`, `localhost/splunk-ansible-controller`, `localhost/splunk-base-ubuntu2204`, `localhost/splunk-base-almalinux9` and `localhost/splunk-git-server`, all `:latest`, in the Taskfile, `infra/create.yml`, the two `docker_image` variables and the controller's `FROM`.

| Step on Docker | Result |
|---|---|
| `task setup` | exit 0; the five `localhost/…` images exist (`names-setup.log`) |
| `MOLECULE_ENV=prod task infra:test` | exit 0 (`names-prod-infra.log`) |
| `MOLECULE_ENV=small task workflow:quick`, then `task day1:test` | exit 0, exit 0; `docker ps` shows the nodes running `localhost/splunk-base-ubuntu2204:latest` and the controller `localhost/splunk-ansible-controller:latest`; no pull in either log |

## Not covered

The lab itself has not run on Podman with the new names. Task 3.12's own check, `infra:create` on a Podman engine creating every container with no pull, needs the five images built in a Podman store and a rootful engine, as on the pre-production host. The probe shows the mechanism with the same module and the same naming.

A lab host that already has the images under their old names keeps them; `task setup` builds the new names from cache.
