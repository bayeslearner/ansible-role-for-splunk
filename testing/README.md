# Splunk Virtual Lab

This directory contains a Docker + Molecule harness for exercising this role against systemd-based container topologies.

Goals:
- virtual lab: SSH into the ansible-controller and operate it like a real Splunk deployment
- repeatable integration testing for role changes
- realistic SSH connectivity (instead of docker connection for converge)
- optional web terminal into the controller for interactive debugging

## Architecture

```
Host (macOS / Linux)
  |
  task setup / task infra:test          <-- Taskfile is the single entry point
  |
  +-- molecule-runner (ephemeral)        Runs molecule via Docker socket
  |
  +-- splunk-test-network (Docker bridge)
        |
        +-- ansible-controller           <-- SSH / web terminal here
        |     ansible.cfg + SSH keys       run playbooks like production
        |     /workspace (bind mount)
        |
        +-- splunk-master                Cluster Manager
        +-- splunk-license               Splunk node in the licence-manager and DMC groups
        +-- splunkapp-prod01             Indexer (cluster peer)
        +-- splunkapp-prod02             Indexer (cluster peer, AlmaLinux)
        +-- splunkshc-prod01             Search Head
        +-- splunkshc-prod02             Search Head (AlmaLinux)
        +-- splunk-deploy                SH Deployer
        +-- splunk-fwdmanager            Deployment Server
        +-- splunk-uf01                  Universal Forwarder
        +-- git-server                   Gitea (app repos)
        +-- caddy, cloudflared           front door, only after `task lab:open`

Topology shown: prod (MOLECULE_ENV=prod)
small (default) = splunk-license + splunkapp-prod01 + controller
dev             = single all-in-one node + controller
dms             = single all-in-one node on a newer Splunk + controller
```

## Prereqs
- Docker, with free disk for the topology. Every node keeps Splunk on the container engine's own disk: about 2.7 GB per Splunk Enterprise node once installed, plus 1.1 GB while its package unpacks. day0 checks before it installs and stops if the installs plus a 6 GB margin do not fit: `dev` and `dms` need 10 GB free, `small` 14 GB, `prod` 39 GB.
- Memory for the topology. Measured on a freshly installed lab with no data and no searches ([record](../docs/history/verification-2026-11-18-memory-and-disk-per-topology.md)); a Splunk 9.4.2 node rests at 640 to 810 MiB and about one core, Splunk 10.6.1.1 (`dms`) at twice the memory. The suggested figure is about twice the resting one, rounded up, a rule of thumb that no run has tested at the limit:

  | Topology | Lab memory at rest | Suggested engine memory | Engine disk used | Free disk day0 asks for |
  |---|---|---|---|---|
  | `dev` | 0.7 GiB | 2 GiB | 3.3 GB | 10 GB |
  | `dms` | 1.5 GiB | 4 GiB | 4.2 GB | 10 GB |
  | `small` | 1.4 to 1.7 GiB | 4 GiB | 6.3 GB | 14 GB |
  | `prod` | 6.0 to 6.6 GiB | 16 GiB | 35 GB | 39 GB |

- 🚨 On a machine that runs other containers, the lab shares the engine's disk with them. A full engine disk fails the lab and can take the other workloads down. Run the larger topologies on an engine of their own.
- `testing/software/` (the Splunk packages, 1 to 4 GB) and `testing/.runs/` are ignored by git. If the checkout lives in a synced folder such as Dropbox, keep them out of the sync too (`xattr -w com.dropbox.ignored 1 testing/software` on macOS).
- [Task](https://taskfile.dev/) (go-task) on the host. On Linux, where distributions package an unrelated `task`, take the release binary: `curl -fsSL https://github.com/go-task/task/releases/download/v3.54.0/task_linux_amd64.tar.gz | tar -xz -C ~/.local/bin task` (3.54.0 is the version CI uses).
- Hosts the lab has run on:
  - macOS with OrbStack, every topology end to end, the amd64 images emulated on Apple Silicon.
  - A Linux x86_64 VM with Docker, as a user in the `docker` group: nothing is emulated, and `small` ran end to end in 4 min 23 s after setup ([record](../docs/history/verification-2026-11-18-small-on-a-linux-vm.md)).
  - A Linux x86_64 host under root Podman: `dms` passed infra and day0; day1 was not run there.
  - Not working: an Apple Silicon Mac under Podman. The images build and the containers start, but infra's prepare step fails because the runner's amd64 `docker` client crashes under emulation ([record](../docs/history/verification-2026-11-18-lab-on-podman.md)).

  The facts to read on a new host first: [research-2026-11-18-lab-hosts.md](../docs/history/research-2026-11-18-lab-hosts.md).

## Quick start
```bash
cd testing

# one-time setup: secrets, images, downloads, network
task setup

# run the full test suite (infra, day0, day1, destroy)
task workflow:full

# quick workflow (infra + day0, keeps containers for debugging)
task workflow:quick

# list all available commands
task --list

# force rebuild all Docker images
task setup:rebuild
```

## Environments
Select a topology via `MOLECULE_ENV`:
- `small` (default): 2 Splunk nodes + controller
- `dev`: 1 Splunk node + controller
- `dms`: 1 Splunk node on a newer Splunk + controller
- `prod`: 8 Splunk Enterprise nodes + 1 Universal Forwarder + controller + git-server

Examples:
```bash
MOLECULE_ENV=dev task workflow:full
MOLECULE_ENV=prod task workflow:full
```

## What each stage does and checks
Each stage ends with a check, and a failed check fails the run.

| Stage | Does | Fails when |
|---|---|---|
| `infra` | starts one systemd container per inventory host plus the controller; installs the lab SSH key, the `ansible` user and the controller's `ansible.cfg` over the Docker connection | a lab host name already resolves to something outside the lab; a lab secret is missing; PID 1 on a node is not systemd; the controller cannot reach a node over SSH as `ansible`; a port the lab would publish is already in use; on `prod`, the Git server's owner cannot sign in with this checkout's password (the message says to run `task reset`) or a repository cannot be created, seeded or read |
| `day0` | installs Splunk on every node with the role, over SSH; on a topology with a `clustermanager` group it then joins the indexers to the manager, and with `shcluster` and `shdeployer` groups it forms the search head cluster | the Splunk unit is not active (it prints the node's processes, last log errors and unit status first); port 8089 (or 8000 on search heads) is closed; an indexer or a search head cluster member is not Up after five minutes (the message names the expected members, the HTTP status the manager or member gave, and each listed peer with its status) |
| `day1` | restarts Splunk through the role, runs the role's status check, accepts the licence | the Splunk unit is not active (it prints the node's processes, last log errors and unit status first) |

Each stage can be run on its own, in this order, against a lab that is up:

```bash
task infra:setup      # create + prepare, keeps the lab (infra:create and infra:prepare are its two halves)
task infra:test       # create, prepare, verify, then destroy
task day0:test        # converge + verify; day0:converge and day0:verify run one half
task day1:test        # converge + verify; day1:converge and day1:verify run one half
```

`task infra:create` first runs `task lab:ports`, which stops when a port the lab would publish is already in use on this machine.

On `prod`, infra also prepares the Git server: one repository per app the inventory names under `git_apps`, at `ssh://git@git-server/test/<app>`, each with a minimal Splunk app, readable with the lab key. The owner is `test`, with the lab's generated Splunk admin password; the web UI is at `http://localhost:8929`.

The lab has no Splunk licence file. Every node runs on its own trial licence, and `splunk-license` is a plain Splunk node that sits in the role's licence-manager group; no node is pointed at it.

On `prod`, day0 forms a two-peer indexer cluster (replication and search factor 2) and a two-member search head cluster. Two members is below the three Splunk recommends; it is the smallest that exercises the role's cluster tasks.

## Using the ansible-controller
After `task infra:setup`, the ansible-controller is a self-sufficient deployment box. SSH in or use the web terminal, then run playbooks directly:
```bash
# web terminal at http://localhost:3000/ttyd (ansible:<password from .secrets/ansible_password>)
# or: docker exec -it -u ansible ansible-controller bash

# from inside the controller — no --inventory flags needed:
ansible all -m ping
ansible-playbook /workspace/testing/molecule/day0/converge.yml
ansible-playbook /workspace/testing/molecule/day0/verify.yml
```

The controller has an `ansible.cfg` pre-configured with the correct inventory sources and roles path.

## Splunk version
The Splunk version is set in each environment's group_vars:
```yaml
# testing/molecule/environments/<env>/group_vars/all.yml
splunk_package_version: 9.4.2
build_id: e9664af3d956
```
Download URLs and architecture suffixes are derived automatically from the role defaults. After changing the version, re-run `task download:splunk` to fetch the new binaries.

## Secrets
`task setup:secrets` creates secrets if they don't exist in `testing/.secrets/`:
- `inventory/group_vars/all.yml` - YAML vars file with `splunk_admin_password` and `gitea_secret_key`
- `id_rsa` / `id_rsa.pub` - SSH keys for container communication
- `ansible_password` - password for the ansible user on the web terminal

Secrets are loaded as an Ansible inventory source, making them available as regular variables. None of these files are committed to the repository.

## Web terminal (password-protected)
After `task infra:setup`, a web terminal is exposed at `http://localhost:3000/ttyd/`.
- Auth is enabled (`ansible:<password>`).
- The password is in `testing/.secrets/ansible_password`.

## Sharing a lab (front door)

`task lab:open` shares a kept lab with people who have nothing installed: a homepage, the web terminal, every Splunk node's Splunk Web and the Git server, each at its own URL. It copies the front door of the owner's n8n and Cribl teaching labs: one Caddy container on the lab network routes by host name or LAN port, and the lab's own `cloudflared` carries public names when a tunnel token exists. No test target starts it; `task lab:close` removes it and leaves the lab; `infra:destroy` closes it first. Design and reasons: `docs/specs/08-lab-front-door/spec.md`.

```bash
MOLECULE_ENV=small task workflow:quick                    # a kept lab (infra + day0)
LAB_BIND_ADDRESS=0.0.0.0 MOLECULE_ENV=small task lab:open # LAN: http://<host>:8100/
```

- **LAN.** Ports 8100 upward (plus `LAB_PORT_OFFSET`), one per service, in the order `lab:open` prints: homepage, terminal, Git server (when the topology has one), then each Splunk node. Every LAN port asks for user `ansible` and `.secrets/ansible_password`, the pair the terminal checks, so one sign-in covers both. Splunk Web and Gitea keep their own logins (Splunk: `admin`, `splunk_admin_password` in `.secrets/inventory/group_vars/all.yml`).
- **Internet.** Put the tunnel's token in `.secrets/tunnel_token_<lab>` (the unnamed lab is `splunk`) and run `LAB_DOMAIN=<domain> task lab:open`. The public names are `<lab>-<service>.<domain>`, for example `splunk-home` and `splunk-splunk-license`. In the operator's Cloudflare account the tunnel has one rule, every hostname to `http://caddy:80` (`<lab>-caddy` for a named lab), and an Access application covers every name before its CNAME exists; Access is the sign-in, so public names carry no Caddy password.
- **What a visitor gets.** The terminal is a shell as `ansible`, which is root on the lab. Share a lab only on a host that holds nothing else, and only with people trusted with that host.
- A node that is not built yet answers with the stage to run (`task day0:converge`).

## Troubleshooting
```bash
task status          # containers on the lab network
task diag:ssh        # ping every node from the controller over SSH
task diag:terminal   # ttyd and nginx on the controller, and the password prompt
```
Both `diag:` targets exit non-zero when something is wrong.

`task runner:shell` opens a shell in a persistent runner container (`mol-run`) for running `molecule` or `ansible-playbook` by hand against the lab; it starts the container when needed, and `task runner:stop` removes it.

## Engine socket and published ports
- The lab's images are named `localhost/<name>:latest` (`localhost/molecule-runner:latest` and so on). Docker and Podman both resolve that form to the local image.
- `DOCKER_SOCK` (default `/var/run/docker.sock`) is the engine socket the runner mounts. The controller does not get the socket: it reaches the nodes over SSH only. Set it to use another engine, such as a Podman API socket.
- `LAB_BIND_ADDRESS` (default `127.0.0.1`) is the address the lab's published ports bind to: 3000 (web terminal), 2222 and 8929 (Git server), and, while the lab is shared, the front door's ports from 8100 upward. Set `LAB_BIND_ADDRESS=0.0.0.0` to reach them from another machine.
- The lab's images are built and run as `linux/amd64` on every host (`LAB_PLATFORM`), because the role downloads Splunk's x86_64 packages. On an ARM machine such as an Apple Silicon Mac the engine runs them emulated, which is slower; nothing needs setting.
- `LAB_RUNNER_ARGS` adds arguments to the runner container. On a host where SELinux is enforcing, set `LAB_RUNNER_ARGS='--security-opt label=disable'`, or the runner cannot open the engine socket ("Permission denied"). On a Podman host, `docker` must be Podman's own command (`podman-docker`), and `DOCKER_SOCK` its socket.
- `LAB_NAME` and `LAB_PORT_OFFSET` run a second lab on the same engine. `LAB_NAME=b LAB_PORT_OFFSET=100 MOLECULE_ENV=small task workflow:quick` creates containers named `b-<host>` on the network `splunk-test-network-b`, with volumes named `ansible-splunk-lab-b-…` and the three ports moved to 3100, 2322 and 9029. Inside the lab every host keeps its inventory name, so playbooks and the controller work unchanged. Give the same two variables to every later command for that lab (`task shell -- ansible-controller`, `task diag:ssh`, `task reset`). `LAB_NAME` holds lower-case letters and digits only. `task infra:create` stops when a port the lab would publish is already in use on the machine.

## Cleanup
```bash
# remove the lab's containers and each node's data volume; keeps images, the network and the Git server's volume
task infra:destroy

# remove everything the lab created: containers, volumes and the network
task reset
```
`infra:destroy` removes the hosts of the topology `MOLECULE_ENV` names when you run it, so give it the topology the lab was built with. `reset` removes the lab whichever topology built it. Docker volumes are prefixed with `ansible-splunk-test-` (`ansible-splunk-lab-<name>-` for a named lab) to avoid conflicts with other resources on your workstation.
