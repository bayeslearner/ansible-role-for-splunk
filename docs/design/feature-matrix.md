# Feature matrix: the virtual lab

```mermaid
flowchart LR
  TF[Taskfile] --> RUN[molecule-runner]
  RUN --> INF[infra scenario]
  RUN --> D0[day0 scenario]
  RUN --> D1[day1 scenario]
  INF --> NODES[node images]
  INF --> CTRL[controller]
  INF --> GIT[git-server]
  D0 --> ROLE[roles/splunk]
  D1 --> ROLE
  CTRL --> ROLE
```

Legend: ✅ done · 🟡 partial · ❌ missing or broken · ⏳ planned · — not involved. A cell marked ✅ means the code does it; the Verified column says whether a run has shown it. Task references point at `docs/specs/05-molecule-virtual-lab/tasks.md` (the fork has no issue tracker).

## Lab capabilities (spec 05)

| Feature | Taskfile | runner | infra | day0 | day1 | controller | git-server | Verified | Spec | Tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| lab-setup | 🟡 image check depends on Docker CLI format | ✅ download.yml | — | — | — | — | — | no recorded run | 05 | 1.1, 2.5, 2.6 |
| lab-topologies | ✅ `MOLECULE_ENV` | ✅ | ✅ small/dev/prod | ✅ | ✅ | ✅ | — | no recorded run | 05 | 1.3 |
| lab-infra | ✅ | ✅ | 🟡 verify skips SSH | — | — | ✅ | — | no recorded run | 05 | 1.2, 2.2 |
| lab-day0-install | ✅ | ✅ | — | 🟡 installs only; no clusters; verify cannot fail | — | ✅ runnable | — | no recorded run | 05 | 1.2, 2.1 |
| lab-day1-ops | ✅ | ✅ | — | — | ✅ asserts active | — | — | no recorded run | 05 | 1.2 |
| lab-controller | — | — | ✅ prepare | — | — | 🟡 apt Ansible differs from runner | — | no recorded run | 05 | 1.4, 2.4 |
| lab-web-terminal | ✅ diag:terminal | — | ✅ | — | — | ✅ ttyd + nginx; 🟡 open on all interfaces | — | no recorded run | 05 | 1.5, 3.3 |
| lab-git-server | — | — | ✅ starts | 🟡 probes only | — | — | ❌ no repos, users or key | no recorded run | 05 | 2.3 |
| lab-cleanup | ✅ reset | — | ✅ destroy | 🟡 destroy.yml unused | — | — | ✅ | no recorded run | 05 | 5.2 |

> [!warning] Built, not verified
> Every row above. No lab run has a recorded result, and the work Mac has none of the lab images (2026-11-02). Tasks 1.1–1.5 produce the first records.

> [!warning] Known gaps
> - `prod` names a cluster manager, two indexer sites, a search head cluster and a deployer, but day0 only installs Splunk; no cluster is formed (task 2.1).
> - The lab has run only on macOS. Isolation on a shared host (published ports, the Docker socket in the controller, privileged nodes, lab names that can match real hosts) is open (tasks 3.3–3.6).

## Day 2 (spec 10, planned)

| Feature | Taskfile | runner | infra | day0 | day1 | day2 | controller | Verified | Spec |
|---|---|---|---|---|---|---|---|---|---|
| day2-git-app-deploy | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
| day2-backup-recovery | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
| day2-cluster-maintenance | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
| day2-advanced-ops | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
| day2-multi-env | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
| day2-ops-validation | ⏳ | ⏳ | — | — | — | ⏳ | ⏳ | — | 10 |
