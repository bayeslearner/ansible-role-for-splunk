---
spec_id: 08-lab-front-door
status: DRAFT
closed_as: null
since: 2026-11-18
until: null
epic: testing
features: [lab-front-door]
supersedes: []
superseded_by: null
depends_on: [05-molecule-virtual-lab]
anchors: []
---

# Lab front door

People other than the lab's operator open a kept lab in a browser: after sign-in, with nothing installed, a homepage and one URL each for the web terminal, every Splunk Web and the Git server. Moved out of spec 05 (its group 7 and R11) on 2026-11-18 at the owner's request, before any of it was built. Decision: `docs/decisions/2026-11-18-04-front-door.md`.

# Requirements

## R1. Front door
WHEN the operator shares a lab, THE lab SHALL give each visitor, after sign-in and with nothing installed, a homepage URL and one URL each for the web terminal, every Splunk Web in the topology and the Git server, using the front door of the owner's other teaching labs (Caddy by host name, a static homepage, optionally the lab's own Cloudflare tunnel and Access application).

## Non-Functional
- **Copy, do not design:** the parts, their configuration and the README recipe follow the owner's n8n learning lab (`work-n8n-devenvs/learning-lab`), which shares them with his Cribl lab. A difference from that source is stated and justified where it is made.
- **Tests stay private:** no test target depends on, starts or publishes a front door.
- **No work host facts:** recipes for a shared work host are written generically; host names, networks and users stay out of this public repository.

## Out Of Scope
- Single sign-on against an organisation's identity provider (an owner decision; the LAN path gets a password).
- A terminal per visitor.

# Design

The parts are copied from the owner's n8n learning lab (`work-n8n-devenvs/learning-lab`), which shares them with his Cribl lab: Caddy routing by Host name, a static homepage, a web terminal, and optionally the lab's own `cloudflared` with one tunnel rule to `caddy:80` behind a Cloudflare Access application. What this design decides is when the lab has them, and what a shared lab exposes. Decision: `docs/decisions/2026-11-18-04-front-door.md`.

## When the lab has a front door

Sharing is a separate act on a kept lab, never a side effect of building or testing one.

| Action | Front door | Why |
|---|---|---|
| `workflow:full`, `infra:test`, `dayN:test` | never | a test run destroys its lab at the end; publishing it would expose a lab nobody is there to use, and a test must not depend on Cloudflare or Caddy |
| `workflow:quick`, `infra:setup` + `day0:*` | not started | a kept lab is private to its operator until shared |
| `task lab:open` (new) | started, or refreshed | the operator shares a kept lab. Needs the lab's network and controller (infra done); refuses otherwise and names the target to run. Re-running it after day0, day1 or a topology change regenerates the Caddyfile and homepage and reloads Caddy, so the order of `lab:open` and `day0` does not matter |
| `task lab:close` (new) | removed | stops sharing; the nodes, controller and data stay |
| `infra:destroy`, `task reset` | removed | the front door's containers sit on the lab network and carry the lab prefix, so both already remove them; `infra:destroy` calls `lab:close` first so the tunnel is gone before the nodes |

`LAB_NAME` gives each lab its own front door (`<prefix>caddy`, `<prefix>cloudflared`), and `LAB_PORT_OFFSET` moves its LAN ports, so two shared labs on one engine do not collide.

## What `lab:open` does

1. Reads the topology's inventory (the same files infra reads) and writes, under `.build/front-door/<lab>/`, a Caddyfile with one site block per service and a homepage listing the topology, each node with its role, and one link per service. Services: the homepage, the terminal, each host in a group that runs Splunk Web (search heads, the cluster manager, the deployment server, the monitoring console, standalone nodes) on its port 8000, and the Git server when the topology has one.
2. Starts `<prefix>caddy` on the lab network. Each service gets a public name `<lab>-<service>.<LAB_DOMAIN>` and a LAN port from a block of ports above the lab's other ones, bound to `LAB_BIND_ADDRESS`; the homepage picks public or LAN links by the address it was opened from, as the learning lab's does.
3. Starts `<prefix>cloudflared` only when `.secrets/` holds this lab's tunnel token. Without one, the front door is LAN only.
4. Answers a service that is not up yet (a search head before day0) with a page that names the stage to run, through Caddy's error handling, instead of a bare 502.

The tunnel, its names and the Access application are created once per shared lab in the operator's Cloudflare account. On the owner's homelab that is lab work for its manager session; this repository carries only the container, the token's place in `.secrets/` and a README recipe.

## Who signs in, and to what

| Where the lab runs | Reached by | Sign-in in front of the lab |
|---|---|---|
| The owner's homelab, guests outside | the tunnel | Cloudflare Access, the people the operator names |
| A shared host, a team on its network | LAN ports | none from the copied pattern, which trusts its LAN. Caddy basic auth with a password in `.secrets/` is the minimum here; the organisation's single sign-on is an owner decision, not part of the copy |
| The operator's own machine | `localhost` | none |

Behind the sign-in, Splunk Web and Gitea keep their own logins; the terminal keeps its basic auth.

## What a shared lab exposes

The web terminal is a shell as `ansible` on the controller, and `ansible` has passwordless sudo in a privileged container (spec 05, design, Security). Whoever is admitted to the terminal is root on the lab and can reach the host's devices. The learning lab's terminal is an unprivileged user on an internal network; this lab's cannot be without giving up what it is for, running the role from the controller. So:

- a shared lab runs on a host that holds nothing else: a throwaway VM (on the owner's homelab, a dev VM on `pve-02`), never an engine shared with other work;
- the Access policy, or the LAN password, admits only people trusted with that VM.

Task 7.4 decides whether guests get the controller's shell or a separate one, after the rest works.

# Tasks

- [ ] 1.1 `task lab:open` and `task lab:close`, as the Design section says: open refuses without infra, writes the Caddyfile and homepage from the inventory under `.build/front-door/<lab>/`, starts or reloads `<prefix>caddy`, and is safe to rerun after day0 or day1; close removes the front door and nothing else; `infra:destroy` calls close first. No test target starts a front door
  - Requirements: R1
- [ ] 1.2 The homepage: the topology, each node with its role, one link per service, public or LAN links by the address it was opened from; a service that is not up yet answers with a page naming the stage to run
  - Requirements: R1
- [ ] 1.3 `<prefix>cloudflared`, started by `lab:open` only when `.secrets/` holds this lab's tunnel token; README recipe for the tunnel, its names and the Access application in the operator's Cloudflare account
  - Requirements: R1
- [ ] 1.4 Sign-in on the LAN path (Caddy basic auth, password generated into `.secrets/` by `setup:secrets`), and the terminal guests get: the controller's shell, which is root on the lab, or a separate one. A shared lab runs only on a host that holds nothing else
  - Requirements: R1
- [ ] 1.5 Splunk Web (sign-in, and the search head cluster's links between members), Gitea and the terminal work behind Cloudflare then Caddy; record the settings each needed (Splunk's `tools.proxy` and `root_endpoint` or none, Gitea's `ROOT_URL`, cookie attributes)
  - Requirements: R1
- [ ] 1.6 From a second machine with nothing installed: after sign-in, the homepage, the terminal, every Splunk Web and the Git server open by their URLs; once through the tunnel on the pve2 VM, once on the LAN without a tunnel. Record in `docs/history/`
  - Requirements: R1
  - Depends: 1.1–1.5
- [ ] 1.7 `testing/README.md` section and the `lab-front-door` row of the feature matrix brought up to what 1.6 showed
  - Requirements: R1

## Log
- 2026-11-18: Created DRAFT from spec 05's group 7, R11 and design section, moved whole at the owner's request. Numbered 08 so it runs before the DRAFT `10-day-2-operations`; the owner may reorder. Depends on 05 closing.
