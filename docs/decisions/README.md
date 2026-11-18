# Decisions

Every decision file for this project, owner questions (`<YYYY-MM-DD>-<NN>-<topic>.md`) and ADRs (`<YYYY-MM-DD>-adr-<NNNN>-<topic>.md`), named by date so the listing is the timeline.

| Date | File | Status | Summary |
|---|---|---|---|
| 2026-11-02 | [2026-11-02-01-adopt-spec-layout.md](2026-11-02-01-adopt-spec-layout.md) | decided (agent) | Reconnect git outside Dropbox; adopt `docs/specs`, steering, decisions and feature matrix |
| 2026-11-18 | [2026-11-18-01-main-default-branch.md](2026-11-18-01-main-default-branch.md) | decided (Kun) | Rename `feature/virtual-lab` to `main` and make it the GitHub default; `master` stays the upstream mirror |
| 2026-11-18 | [2026-11-18-02-lab-behaviour-changes.md](2026-11-18-02-lab-behaviour-changes.md) | decided (agent) | Destroy removes node volumes; a failed day0 or day1 keeps the lab; the controller runs the runner's Ansible; day0 forms `prod`'s clusters; day0 verify can fail; the Git server holds one repository per app; nodes stay privileged; lint runs on GitHub Actions; a lab can be named so several share one engine |
| 2026-11-18 | [2026-11-18-03-host-name-and-site-names.md](2026-11-18-03-host-name-and-site-names.md) | open | May the pre-production host's name stay in a public repository; should the indexer site names come back |
