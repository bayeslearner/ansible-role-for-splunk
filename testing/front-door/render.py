#!/usr/bin/env python3
"""Write a lab's front door from its inventory: a Caddyfile, a homepage, and the ports to publish.

Spec 08, task 1.1 and 1.2. The parts copy the owner's n8n learning lab (Caddy routing by Host
name, a static homepage that picks public or LAN links by the address it was opened from).
Differences from that source, and why:
- Caddy serves the homepage itself (no separate nginx container): one container fewer per lab.
- Every LAN site sits behind Caddy basic auth as user `ansible` with the lab's own password
  (.secrets/ansible_password). The web terminal (ttyd) checks the same credentials, so a visitor
  signs in once; Caddy strips the header before Splunk Web and the Git server, which have their
  own logins. The source trusts its LAN; a shared lab's terminal is root on the lab (spec 08,
  "What a shared lab exposes"), so the LAN path needs a sign-in.
- Every Splunk Enterprise node gets a link, indexers included, so a visitor sees the whole cluster.

Usage: render.py <hosts.yml> <out dir> --lab <name> --offset <n> --bind <addr>
                  --password-hash-file <file> [--domain <public domain>]
"""
import argparse
import json
import pathlib
import sys

import yaml

LAN_BASE = 8100  # first LAN port of a lab's front door, above the lab's 2222, 3000 and 8929
ROLE_WORDS = {
    "clustermanager": "cluster manager",
    "licensemaster": "licence manager",
    "dmc": "monitoring console",
    "deploymentserver": "deployment server",
    "indexer": "indexer",
    "shcluster": "search head cluster member",
    "shdeployer": "search head deployer",
    "search": "search head",
    "alma_hosts": "AlmaLinux",
}


def groups_of(inventory):
    """Map each group name to the set of hosts in it, children included."""
    found = {}

    def walk(name, node):
        node = node or {}
        hosts = set((node.get("hosts") or {}).keys())
        for child, sub in (node.get("children") or {}).items():
            hosts |= walk(child, sub)
        found[name] = found.get(name, set()) | hosts
        return hosts

    walk("all", inventory["all"])
    return found


def services(groups):
    """The front door's services in a fixed order: homepage, terminal, Git server, Splunk nodes."""
    out = [
        {"key": "home", "name": "Lab homepage", "upstream": None, "what": "This page."},
        {"key": "terminal", "name": "Lab terminal", "upstream": "ansible-controller:3000",
         "what": "A shell as ansible on the controller: run the role, ssh to any node by name.",
         "stage": "task infra:setup", "keep_auth": True},
    ]
    if groups.get("git_server"):
        out.append({"key": "git", "name": "Git server", "upstream": "git-server:8929",
                    "what": "Gitea with one repository per app the topology deploys.",
                    "stage": "task infra:setup"})
    for host in sorted(groups.get("full", ())):
        roles = [w for g, w in ROLE_WORDS.items() if host in groups.get(g, ())]
        out.append({"key": host, "name": host, "upstream": f"{host}:8000",
                    "what": "Splunk Web: " + (", ".join(roles) or "Splunk Enterprise"),
                    "stage": "task day0:converge", "splunk": True})
    return out


def caddyfile(svcs, lab, domain, pw_hash):
    lines = [
        "# Written by testing/front-door/render.py from the topology's inventory; do not edit.",
        "{", "\tauto_https off", "}", "",
    ]

    def body(s, lan):
        b = []
        if lan:
            b += ["\tbasic_auth {", f"\t\tansible {pw_hash}", "\t}"]
        if s["upstream"] is None:
            b += ["\troot * /srv/home", "\tfile_server"]
            return b
        if s.get("keep_auth"):
            b += [f"\treverse_proxy {s['upstream']}"]
        else:
            b += [f"\treverse_proxy {s['upstream']} {{", "\t\theader_up -Authorization", "\t}"]
        b += ["\thandle_errors {",
              f"\t\trespond \"{s['name']} is not answering yet. Run `{s['stage']}` on the lab, "
              f"then reload this page.\" 503",
              "\t}"]
        return b

    for s in svcs:
        if domain:
            lines += [f"http://{lab}-{s['key']}.{domain} {{"] + body(s, False) + ["}", ""]
        lines += [f":{s['port']} {{"] + body(s, True) + ["}", ""]
    lines += ["# Any other name that reaches the tunnel.", ":80 {", "\trespond 404", "}", ""]
    return "\n".join(lines)


def homepage(svcs, lab, domain, env):
    def card(s):
        return (f'<a class="card" data-svc="{s["key"]}"><div class="name">{s["name"]}</div>'
                f'<div class="what">{s["what"]}</div></a>')

    start = "\n".join(card(s) for s in svcs if s["key"] in ("terminal", "git"))
    nodes = "\n".join(card(s) for s in svcs if s.get("splunk"))
    pub = {s["key"]: f"https://{lab}-{s['key']}.{domain}/" for s in svcs} if domain else {}
    lan = {s["key"]: s["lan_port"] for s in svcs}
    return HTML.format(lab=lab, env=env, start=start, nodes=nodes,
                       domain=json.dumps(domain or ""), pub=json.dumps(pub), lan=json.dumps(lan))


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Splunk lab {lab}</title>
<style>
  :root {{ --ink: #111418; --quiet: #5b6470; --line: #dde1e6; --accent: #0b5fff; --bg: #ffffff; --card: #f6f8fa; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 40px 16px 64px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }}
  p.lead {{ color: var(--quiet); margin: 0 0 32px; }}
  h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: .06em; color: var(--quiet); margin: 32px 0 12px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 12px; }}
  a.card {{ display: block; padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); color: inherit; text-decoration: none; }}
  a.card:hover {{ border-color: var(--accent); }}
  .name {{ font-weight: 600; font-size: 17px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  .what {{ color: var(--quiet); font-size: 14px; margin: 4px 0 0; }}
  footer {{ margin-top: 40px; color: var(--quiet); font-size: 13px; }}
</style>
</head>
<body>
<main>
  <h1>Splunk lab {lab}</h1>
  <p class="lead">Topology <code>{env}</code>: Splunk nodes built by ansible-role-for-splunk, each a container on the lab's own network. Open a node's Splunk Web below (user <code>admin</code>, the lab's generated password), or use the terminal to run the role.</p>
  <h2>Start here</h2>
  <div class="grid">
{start}
  </div>
  <h2>Splunk nodes</h2>
  <div class="grid">
{nodes}
  </div>
  <footer>A node that is not built yet answers with the lab stage to run. Written by <code>task lab:open</code>.</footer>
</main>
<script>
  // The same page answers through the lab's tunnel (public names) and on the LAN (one port per service).
  const domain = {domain}, pub = {pub}, lan = {lan};
  const isPub = domain && location.hostname.endsWith(domain);
  const base = location.protocol + "//" + location.hostname + ":";
  for (const a of document.querySelectorAll("a[data-svc]")) a.href = isPub ? pub[a.dataset.svc] : base + lan[a.dataset.svc] + "/";
</script>
</body>
</html>
"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("inventory")
    p.add_argument("out")
    p.add_argument("--lab", required=True)
    p.add_argument("--env", required=True)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--bind", default="127.0.0.1")
    p.add_argument("--password-hash-file", required=True,
                   help="bcrypt hash of the LAN password, from `caddy hash-password`")
    p.add_argument("--domain", default="")
    a = p.parse_args()

    groups = groups_of(yaml.safe_load(pathlib.Path(a.inventory).read_text()))
    svcs = services(groups)
    for i, s in enumerate(svcs):
        s["port"] = LAN_BASE + i               # inside the Caddy container
        s["lan_port"] = LAN_BASE + i + a.offset  # on the host
    out = pathlib.Path(a.out)
    (out / "html").mkdir(parents=True, exist_ok=True)
    pw_hash = pathlib.Path(a.password_hash_file).read_text().strip()
    (out / "Caddyfile").write_text(caddyfile(svcs, a.lab, a.domain, pw_hash))
    (out / "html" / "index.html").write_text(homepage(svcs, a.lab, a.domain, a.env))
    (out / "ports").write_text(" ".join(f"-p {a.bind}:{s['lan_port']}:{s['port']}" for s in svcs) + "\n")
    print(f"front door for lab {a.lab}: {len(svcs)} services, LAN ports "
          f"{svcs[0]['lan_port']}-{svcs[-1]['lan_port']} on {a.bind}"
          + (f", public names *.{a.domain}" if a.domain else ", no public names"))
    for s in svcs:
        print(f"  {s['lan_port']}  {s['name']}")


if __name__ == "__main__":
    sys.exit(main())
