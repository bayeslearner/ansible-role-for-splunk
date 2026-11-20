# Verification: the front door on a Linux VM, from a second machine, and through a tunnel

- **Date:** 2026-11-19
- **Code:** `099ea18` (`main`), a fresh clone from GitHub.
- **Host:** a throwaway dev VM on the homelab's Proxmox node `pve-02`: Ubuntu 24.04, Docker 29.1.3, 4 cores, 8 GiB, 58 GB, made for this run with the owner's go-ahead ("Yes, run it") and deleted after it.
- **Second machine:** the work Mac, on the same LAN, with nothing of the lab installed; only `curl` and a browser.
- **Topology:** `MOLECULE_ENV=small` (`splunk-license`, `splunkapp-prod01`, controller), `LAB_BIND_ADDRESS=0.0.0.0`.

## Run on the VM

```bash
task setup && task workflow:quick && task lab:open
```

All three exit 0. `lab:open` reported 4 services on LAN ports 8100 to 8103.

## From the second machine, LAN

| Request | Result |
|---|---|
| `GET :8100/` without sign-in | 401 |
| `GET :8100/` as `ansible` with the lab password | 200, "Splunk lab splunk", links for the terminal and both nodes |
| `GET :8101/ttyd/` | 200 |
| Websocket handshake to `:8101/ttyd/ws`, and the same to the controller's own port 3000 | `101 Switching Protocols` both (raw socket; `curl`'s upgrade request timed out on both, so that was the client, not the proxy) |
| `GET :8102/` (splunk-license), `:8103/` (splunkapp-prod01) | 303 to `http://<VM>:<port>/en-US/`: Splunk builds its redirect from the Host header Caddy passes on, so no proxy setting was needed |
| Splunk sign-in through Caddy on both nodes: login page, `POST /en-US/account/login` as `admin` | `{"status":0}`; session cookie `splunkd_8000` set; `/en-US/app/launcher/home` answers 200 signed in |

## Tunnel

Created by the lab session through the Cloudflare API on the owner's word ("or you can just create the tunnel yourself"), copying the n8n learning lab's objects: tunnel `splunk-lab`, one ingress rule to `http://caddy:80`; Access application `splunk-lab` over eleven names (`splunk-home`, `splunk-terminal`, `splunk-git` and one per `prod` node), the owner-only policy `learning-allowed`; then a proxied CNAME per name. Token in the operator's vault and in `.secrets/tunnel_token_splunk` on the VM.

| Check | Result |
|---|---|
| `LAB_DOMAIN=bayeslearner.org task lab:open` | "Tunnel started (cloudflared)"; the connector logged 4 registered connections |
| `GET https://splunk-home…/`, `splunk-terminal…`, `splunk-splunk-license…` without a session | 302 to the Access sign-in page, "Log in to splunk-lab" |
| The owner signed in through Access, then homepage, terminal and Splunk Web | (filled in below) |

## Not covered

- `prod`: the search head cluster's links between members and the Git server behind the proxy (task 1.5); `small` has neither.
- A guest other than the owner (the Access policy admits the owner only).
