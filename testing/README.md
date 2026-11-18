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
- [Task](https://taskfile.dev/) (go-task) on the host

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
| `infra` | starts one systemd container per inventory host plus the controller; installs the lab SSH key, the `ansible` user and the controller's `ansible.cfg` over the Docker connection | a lab host name already resolves to something outside the lab; a lab secret is missing; PID 1 on a node is not systemd; the controller cannot reach a node over SSH as `ansible` |
| `day0` | installs Splunk on every node with the role, over SSH; on a topology with a `clustermanager` group it then joins the indexers to the manager, and with `shcluster` and `shdeployer` groups it forms the search head cluster | the Splunk unit is not active (it prints the node's processes, last log errors and unit status first); port 8089 (or 8000 on search heads) is closed; an indexer or a search head cluster member is not Up |
| `day1` | restarts Splunk through the role, runs the role's status check, accepts the licence | the Splunk unit is not active (it prints the node's processes, last log errors and unit status first) |

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
- `LAB_BIND_ADDRESS` (default `127.0.0.1`) is the address the lab's published ports bind to: 3000 (web terminal), 2222 and 8929 (Git server). Set `LAB_BIND_ADDRESS=0.0.0.0` to reach them from another machine.
- `LAB_NAME` and `LAB_PORT_OFFSET` run a second lab on the same engine. `LAB_NAME=b LAB_PORT_OFFSET=100 MOLECULE_ENV=small task workflow:quick` creates containers named `b-<host>` on the network `splunk-test-network-b`, with volumes named `ansible-splunk-lab-b-…` and the three ports moved to 3100, 2322 and 9029. Inside the lab every host keeps its inventory name, so playbooks and the controller work unchanged. Give the same two variables to every later command for that lab (`task shell -- ansible-controller`, `task diag:ssh`, `task reset`). `LAB_NAME` holds lower-case letters and digits only. `task infra:create` stops when the web terminal's port is already in use on the machine.

## Cleanup
```bash
# remove the lab's containers and each node's data volume; keeps images, the network and the Git server's volume
task infra:destroy

# remove everything the lab created: containers, volumes and the network
task reset
```
`infra:destroy` removes the hosts of the topology `MOLECULE_ENV` names when you run it, so give it the topology the lab was built with. `reset` removes the lab whichever topology built it. Docker volumes are prefixed with `ansible-splunk-test-` (`ansible-splunk-lab-<name>-` for a named lab) to avoid conflicts with other resources on your workstation.
