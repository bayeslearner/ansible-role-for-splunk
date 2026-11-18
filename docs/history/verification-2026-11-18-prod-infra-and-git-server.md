# Verification: `prod` infrastructure and the Git server

- **Date:** 2026-11-18
- **Code:** the working tree on top of `09508a0` (`main`), committed with this record.
- **Host:** macOS 27.2 on arm64, Docker engine 29.8.2 (OrbStack). Runner: Molecule 25.12.0, ansible-core 2.21.6.
- **Scope:** the infra stage of `prod` only: eleven containers, no Splunk install, so it fits this host's disk. Day 0 on `prod` is still owed (see the cluster formation record).
- **Raw output:** `testing/.runs/2026-11-18-prod-infra/` on the machine that ran it (not committed).

All commands run from `testing/` with `MOLECULE_ENV=prod`.

## What was a placeholder

`infra/prepare.yml` ended with a "Bootstrap Git Server" play that echoed two messages. Gitea started with no user, no repository and no key. `prod` named its apps with `git_project: test/splunk_apps/`, `git_server: "git@git-server"` and `git_key: /tmp/test_git_key`, a file nothing wrote. The role clones `<git_server>/<git_project>/<app name>` (`roles/splunk/tasks/splunk_apps/fetch_git.yml`), so those settings named an address that is not a valid SSH URL.

## As built

- The play creates the owner `test`, installs the lab SSH key on it, creates one repository per app named in the inventory's `git_apps` (six on `prod`), and seeds each with `default/app.conf`. Every step can run again.
- `prod` sets `git_server: "ssh://git@git-server"`, `git_project: test` and `git_key` to the lab key, so the role's address for an app is `ssh://git@git-server/test/<app>`.
- `infra/verify.yml` lists each repository's `main` branch from the controller as `ansible` with the lab key, on topologies that have a Git server.
- The controller image has `git`.
- The lab's Gitea accepts the lab's 2048-bit RSA key: its image sets `GITEA__ssh__MINIMUM_KEY_SIZE_CHECK=false` and `GITEA__ssh.minimum_key_sizes__RSA=2047`. Without them Gitea 28.4.0 answers "key length is not enough: got 2048, needs 3071".

## Runs

| Step | Result |
|---|---|
| `task infra:test`, Git volume removed first | exit 0; 6 Molecule steps "Executed: Successful" (`git-prod-infra-test.log`) |
| `molecule verify -s infra` | exit 0: "Runner and controller both run ansible-core 2.21.6"; "The controller reached every node over SSH as ansible" (nine nodes); six repositories listed (`git-verify-ok.log`) |
| on the controller as `ansible`: `git clone --branch main ssh://git@git-server/test/test_search_app` | cloned; `default/app.conf` holds the `[ui]` and `[launcher]` stanzas with the app's name |
| delete `test/test_lookup_app` through the API, then `molecule verify -s infra` | exit 2: "ssh://git@git-server/test/test_lookup_app is not readable from the controller" (`git-verify-neg.log`) |
| `task infra:prepare` again, then verify | prepare exit 0 (it recreated the repository); verify exit 0 |

## Found by these runs

1. **The AlmaLinux nodes had no `scp`.** The first `prod` infra verify failed on `splunkapp-prod02` and `splunkshc-prod02`: "bash: line 1: scp: command not found". The lab inventory sets `ansible_ssh_transfer_method: scp`, and the AlmaLinux image installed `openssh-server` without `openssh-clients`. Nothing could have run on those two nodes over SSH. The image now installs `openssh-clients`. This is the check added in task 2.2 catching its first real fault.
2. **A rejected key looked like a duplicate.** Gitea answers 422 both for a key it already has and for one it refuses, and the first draft accepted 422. The play now lists the keys, adds the lab key only when it is absent, and accepts only 201.
3. **The seed file had literal `\n` in it.** The app.conf text is now a YAML block in the play's vars.

## Sign-up off, and where the ports bind (task 3.3)

On the tree at `a7e70cb`, with the Git server image rebuilt and its volume removed first:

| Check | Result |
|---|---|
| `task infra:setup` then `molecule verify -s infra` | both exit 0; six repositories listed for the owner (`reg-infra-setup.log`, `reg-verify.log`) |
| Gitea's `app.ini` | `[service] DISABLE_REGISTRATION = true` |
| `POST /user/sign_up` with a new user | HTTP 403; the sign-up page says "Registration is disabled"; the user does not exist afterwards (404) |
| `docker port git-server` | `22/tcp -> 127.0.0.1:2222`, `8929/tcp -> 127.0.0.1:8929` |

The image used to set `GITEA__admin__DISABLE_REGISTRATION=false`, a key in the wrong section that left sign-up open. The owner is created by the `gitea` command inside the container, which does not need sign-up.

## Memory, infra only

One `docker stats` reading with all eleven containers up and no Splunk installed: each node about 30 MiB, `ansible-controller` 70 MiB, `git-server` 186 MiB.

## Not covered

- The role deploying these apps (its `splunk_apps` tasks). That is day 2 work (spec 10); this record shows the repositories exist at the address the role will use and are readable with the key it will use.
- Day 0 and day 1 on `prod`.
- A lab whose key was generated with a different size or type.
