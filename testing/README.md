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
        +-- splunk-license               License Manager / DMC
        +-- splunkapp-prod01             Indexer (site1)
        +-- splunkapp-prod02             Indexer (site2, AlmaLinux)
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
- Docker, with free disk for the topology: each Splunk Enterprise node took 2.7 GB once installed, plus 1.1 GB while its package unpacks. `small` fits in about 8 GB; `prod` needs about 30 GB. Measured memory and CPU figures are owed (spec 05, task 5.5).
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
| `infra` | starts one systemd container per inventory host plus the controller; installs the lab SSH key, the `ansible` user and the controller's `ansible.cfg` over the Docker connection | a lab secret is missing; PID 1 on a node is not systemd; the controller cannot reach a node over SSH as `ansible` |
| `day0` | installs Splunk on every node with the role, over SSH; on a topology with a `clustermanager` group it then joins the indexers to the manager, and with `shcluster` and `shdeployer` groups it forms the search head cluster | the Splunk unit is not active; port 8089 (or 8000 on search heads) is closed; an indexer or a search head cluster member is not Up |
| `day1` | restarts Splunk through the role, runs the role's status check, accepts the licence | the Splunk unit is not active (it prints the node's processes, last log errors and unit status first) |

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

## Engine socket and published ports
- `DOCKER_SOCK` (default `/var/run/docker.sock`) is the engine socket the runner and the controller mount. Set it to use another engine, such as a Podman API socket.
- `LAB_BIND_ADDRESS` (default `127.0.0.1`) is the address the lab's published ports bind to: 3000 (web terminal), 2222 and 8929 (Git server). Set `LAB_BIND_ADDRESS=0.0.0.0` to reach them from another machine.

## Cleanup
```bash
# remove the lab's containers and each node's data volume; keeps images, the network and the Git server's volume
task infra:destroy

# remove everything the lab created: containers, volumes and the network
task reset
```
Docker volumes are prefixed with `ansible-splunk-test-` to avoid conflicts with other resources on your workstation.
