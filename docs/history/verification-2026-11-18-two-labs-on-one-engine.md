# Verification: several labs on one container engine

- **Date:** 2026-11-18, about 14:50 to 15:50 UTC.
- **Code:** the working tree on top of `b5253b8` (`main`), committed with this record.
- **Host:** the second Mac of the `prod` record (Docker 29.8.2 under OrbStack, amd64 images emulated). Unrelated containers and programs were running on it.
- **Raw output:** `~/lab-runs/2026-11-18-two-labs/` on that machine (not committed).

## What changed

`LAB_NAME=<letters and digits>` gives a lab its own container names (`<name>-<host>`), network (`splunk-test-network-<name>`) and volumes (`ansible-splunk-lab-<name>-…`). `LAB_PORT_OFFSET=<n>` moves its three published ports (web terminal 3000, Git SSH 2222, Git HTTP 8929) by `n`. Inside its network each container keeps its inventory name as a network alias and as its hostname, so the inventory, the role and the controller see the same names in every lab. With neither variable set, every name and port is what it was before.

## Three labs at once

All commands from `testing/`. Lab A is the unnamed lab; B and C are named.

| Step | Result |
|---|---|
| A: `MOLECULE_ENV=dev task workflow:quick` | exit 0, Splunk installed |
| B: `LAB_NAME=b LAB_PORT_OFFSET=100 MOLECULE_ENV=small task workflow:quick`, with A up | exit 0, Splunk installed on both nodes |
| B and A: `task diag:ssh` | exit 0 each: each controller reaches its own nodes over SSH |
| B then A: `task day1:test` | exit 0 each |
| C: `LAB_NAME=c LAB_PORT_OFFSET=200 MOLECULE_ENV=prod task infra:setup`, with A and B up | exit 0: eleven more containers, Git server bootstrapped |
| C: `task diag:ssh`, `task diag:terminal` | exit 0 each; the terminal answers 401 on port 3200 |
| C's Git server | HTTP 200 on `127.0.0.1:9129`; nothing on 8929 |
| C: `task reset`, then B: `task reset` | exit 0 each; only A's containers, network and volume remain, plus the unnamed lab's Git volume from earlier runs |
| A: `task day0:verify` after the other two were removed | exit 0 |
| A: `task infra:destroy` | exit 0; no lab container left |

With all three up, `docker ps` listed 16 lab containers: `ansible-controller` and `splunk-dev`; four named `b-…`; eleven named `c-…`. Published ports: 3000, 3100, 3200 for the three web terminals; 2422 and 9129 for C's Git server. Networks: `splunk-test-network`, `-b`, `-c`. Volumes: `ansible-splunk-test-splunk-dev-data` for A, two `ansible-splunk-lab-b-…`, ten `ansible-splunk-lab-c-…`.

Isolation, read on the running labs:

| Check | Result |
|---|---|
| `hostname` inside `b-splunk-license` | `splunk-license` |
| `getent hosts splunk-license splunkapp-prod01` on B's controller | both resolve, to B's own network |
| `getent hosts splunk-license` on A's controller (A has no such node) | exit 2: B's nodes are not visible from A |

## Found: a busy port is not an error to the engine

B's `task diag:terminal` failed: it expected 401 on port 3100 and got 200. Another program on that machine already listened on `127.0.0.1:3100`, the engine published B's port there without complaint, and the other program answered. B's lab itself was sound (its SSH check and day1 passed).

`task infra:create` now runs a check first (`task lab:ports`): when this lab's controller does not exist yet and something answers on the web terminal's port, it stops with the port, the current offset and the two Git ports the offset also moves. It also refuses a `LAB_NAME` with anything but lower-case letters and digits.

| Case | Result |
|---|---|
| `LAB_NAME=b LAB_PORT_OFFSET=100 MOLECULE_ENV=dev task infra:create` on the machine where 3100 is taken | stops: "Port 3100 on this machine is already in use…" |
| `LAB_NAME=d LAB_PORT_OFFSET=300 MOLECULE_ENV=dev task infra:test` | exit 0, six "Executed: Successful" |
| `MOLECULE_ENV=dev task infra:test`, unnamed | exit 0 |
| `LAB_NAME=B-2 task network:create` | stops: "LAB_NAME may hold only lower-case letters and digits (got 'B-2')" |
| On the first Mac: `task lab:ports` against a port held by a test server, and a free one | stops; exit 0 |

## Reset under another topology

Found while checking requirement R9 ("`task reset` SHALL remove every container, volume and network the lab created") against the code: `reset` relied on `infra:destroy`, which removes the hosts of the topology `MOLECULE_ENV` names at that moment. `reset` now also removes whatever is still on the lab's network.

With an unnamed `dev` lab up beside it, lab C was built with `LAB_NAME=c LAB_PORT_OFFSET=200 MOLECULE_ENV=prod task infra:setup` (eleven containers), then addressed as `small`:

| Step | Result |
|---|---|
| `LAB_NAME=c … MOLECULE_ENV=small task infra:destroy` | 7 of C's 11 containers remain: the old behaviour of `reset` |
| `LAB_NAME=c … MOLECULE_ENV=small task reset` | prints "Removing containers left on splunk-test-network-c:" and the seven names; afterwards C has 0 containers, 0 volumes and no network |
| the unnamed lab | both containers still up; `task diag:ssh` exit 0 |
| `MOLECULE_ENV=small task reset` on the unnamed `dev` lab | exit 0; no lab container, network member or lab volume left |

## Later the same day: the Git ports, and destroy's ignored errors

`task lab:ports` now also probes the Git server's two ports when the topology has a `git_server` group and this lab's Git server does not exist yet. On the first Mac, with test listeners:

| Case | Result |
|---|---|
| `prod`, the Git HTTP port held by an HTTP server | stops: "Port 2777 or 9484 on this machine is already in use…" |
| `small`, same offset (no Git server in the topology) | exit 0 |
| `prod`, the Git SSH port held by a listener that speaks no HTTP | stops with the same message |
| `prod`, all three ports free | exit 0 |

`infra/destroy.yml` ignored every error from removing a container. Removing a container that is already gone is not an error, so nothing needed ignoring, and a removal that really failed went unreported unless a later task happened to fail too. The three `ignore_errors` are gone. On the second Mac:

| Case | Before | After |
|---|---|---|
| `molecule destroy -s infra` with no engine behind the socket | exit 2, but only at the fourth task: `failed=1 ignored=2` | exit 2 at the first task: `failed=1 ignored=0` |
| `MOLECULE_ENV=prod task infra:test` (create, prepare, verify, destroy) | | exit 0 |
| `MOLECULE_ENV=prod task infra:destroy` with nothing to remove | | exit 0, `ok=4 failed=0 ignored=0` |

## Not covered

- Two labs running day0 at the same moment. Here they ran one after another.
- Two labs started from two different checkouts.
- `task infra:destroy` leaves a lab's network in place, named or not; `task reset` removes it.
