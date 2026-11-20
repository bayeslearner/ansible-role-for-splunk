# Verification: the lab's front door on the LAN path

- **Date:** 2026-11-19
- **Code:** `main` with `testing/front-door/render.py` and the `lab:open` / `lab:close` targets (spec 08, tasks 1.1, 1.2, the LAN half of 1.4).
- **Host:** the work Mac (OrbStack). Only the infra stage ran, so no Splunk was installed: the project's rule for an engine shared with other work.
- **Lab:** `LAB_NAME=fd LAB_PORT_OFFSET=300 MOLECULE_ENV=small`, so the front door's LAN ports are 8400 to 8403.
- **Raw output:** `testing/.runs/2026-11-19-fd-*.log` (local, ignored).

## Steps and results

| Step | Command or request | Result |
|---|---|---|
| Lab infra | `task infra:setup` | exit 0 |
| Generated config | `render.py` on `prod`'s inventory, then `caddy validate` in the pinned Caddy image | "Valid configuration"; 11 services (homepage, terminal, Git server, eight Splunk nodes) |
| Open | `task lab:open` | `fd-caddy` started; "No tunnel token … the front door is LAN only"; the homepage answered before the target returned |
| Homepage, no sign-in | `GET :8400/` | 401 |
| Homepage, wrong password | `GET :8400/` as `ansible:nope` | 401 |
| Homepage, lab password | `GET :8400/` as `ansible:<.secrets/ansible_password>` | 200; title "Splunk lab fd", links for the terminal and both Splunk nodes |
| Terminal | `GET :8401/ttyd/` with the same sign-in | 200, "ttyd - Terminal": one sign-in serves Caddy and ttyd |
| A node before day0 | `GET :8402/`, `:8403/` | 503 "splunk-license is not answering yet. Run `task day0:converge` on the lab, then reload this page." |
| Open again | `task lab:open` a second time | same result; the container is recreated with the regenerated config |
| Close | `task lab:close` | `fd-caddy` gone; controller and both nodes still on the lab network |
| Destroy | `task lab:open`, then `task infra:destroy` | exit 0; no `fd-` container left (destroy runs `lab:close` first) |
| Open with no lab | `task lab:open` after destroy | exit 1: "No running lab controller (fd-ansible-controller). Run: MOLECULE_ENV=small task infra:setup" |
| Cleanup | `task reset` | exit 0; no `ansible-splunk-lab-fd-` volume left |
| Lint | `uvx pre-commit run --all-files` | all four hooks pass |

## Not covered

- Splunk Web, Gitea and the terminal through the proxy after day0, and the settings each needs behind Cloudflare then Caddy (task 1.5).
- The tunnel: `lab:open` starts `cloudflared` only when `.secrets/tunnel_token_<lab>` exists; no token was used (task 1.3).
- The homepage's public links, which it picks when opened under `LAB_DOMAIN`.
- A second machine on the LAN (`LAB_BIND_ADDRESS=0.0.0.0`) and the pve-02 VM (task 1.6).
