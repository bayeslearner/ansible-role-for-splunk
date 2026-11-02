#!/usr/bin/env python3
"""Lint spec frontmatter for schema integrity. CI guardrail — NOT a facts cache.

This is the canonical, lint-ONLY successor to the old `spec_facts.py`. It does
not emit, cache, or project any "facts block" — review reads the specs directly
(spec-driven-dev SKILL.md). It only fails the build when frontmatter is broken.

Usage:
  python3 scripts/spec_lint.py            # lint; exit 1 on any violation
  python3 scripts/spec_lint.py --quiet    # same, print only on failure
  python3 scripts/spec_lint.py --single-active   # also: one ACTIVE spec, others only with an
                                                # "owner exception" line in their Log

Specs root is `docs/specs/` under the repo root. A leftover root `specs/` or `.kiro/specs/` is an
error: move it with `git mv specs docs/specs` (or `git mv .kiro/specs docs/specs`).

Checks (per spec-driven-dev frontmatter schema):
  - frontmatter block parses
  - spec_id (if present) matches the spec's directory name
  - status ∈ {DRAFT, ACTIVE, CLOSED}
  - closed_as is null for open specs and a valid closing flavor for CLOSED specs
  - SUPERSEDED closure requires superseded_by
  - supersedes / superseded_by are bidirectional
  - depends_on / supersedes / superseded_by reference real spec dirs
  - features are unique project-wide

Single source of truth: skills/spec-driven-dev/scripts/spec_lint.py. Projects
that want the CI gate copy this file verbatim into their own scripts/ — do not
hand-edit the copy; re-copy when this changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

VALID_STATUS = {"DRAFT", "ACTIVE", "CLOSED"}
VALID_CLOSED_AS = {"SHIPPED", "FORK-FORWARD", "RETRACTED", "SUPERSEDED"}
NULLISH = {"", "null", "~", "none", "nil", "[]", "{}"}


def is_empty(v) -> bool:
    """True for absent / explicit-null YAML scalars (e.g. `superseded_by: null`)."""
    return v is None or (isinstance(v, str) and v.strip().lower() in NULLISH)


# Retired spec locations. Either one existing means a migration was never finished, so the
# linter refuses to guess which tree is current rather than silently linting only one.
LEGACY_ROOTS: tuple[str, ...] = ("specs", ".kiro/specs")


def find_specs_root(repo: Path) -> Path | None:
    # `specs_root:` in root CLAUDE.md / AGENTS.md overrides the default (SKILL.md,
    # Resolve Paths). First match wins; the steering line is authoritative.
    for steering in ("CLAUDE.md", "AGENTS.md"):
        f = repo / steering
        if f.is_file():
            m = re.search(r"^specs_root:\s*(\S+)", f.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
            if m:
                root = repo / m.group(1).strip().rstrip("/")
                return root if root.is_dir() else None
    root = repo / "docs" / "specs"
    return root if root.is_dir() else None


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"\A---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fm[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        else:
            fm[key] = value
    return fm


def spec_text(spec_dir: Path) -> str:
    for name in ("spec.md", "requirements.md", "design.md", "tasks.md"):
        f = spec_dir / name
        if f.is_file():
            t = f.read_text(encoding="utf-8", errors="replace")
            if t.lstrip().startswith("---"):
                return t
    return ""


def as_list(v) -> list:
    if is_empty(v):
        return []
    items = v if isinstance(v, list) else [v]
    return [x for x in items if not is_empty(x)]


def main() -> int:
    repo = Path.cwd()
    # Fail on any legacy tree before linting, and name the exact move that fixes it.
    for legacy in LEGACY_ROOTS:
        if (repo / legacy).is_dir():
            print(f"spec_lint: {legacy}/ is retired; run `git mv {legacy} docs/specs`",
                  file=sys.stderr)
            return 1
    root = find_specs_root(repo)
    if root is None:
        print("spec_lint: no docs/specs/ directory found", file=sys.stderr)
        return 0  # nothing to lint is not a failure

    dirs = sorted(d for d in root.iterdir() if d.is_dir())
    names = {d.name for d in dirs}
    errors: list[str] = []
    feature_owner: dict[str, str] = {}
    fms: dict[str, dict] = {}

    for d in dirs:
        text = spec_text(d)
        if not text:
            continue  # no frontmatter'd spec file here; skip
        fm = parse_frontmatter(text)
        if not fm:
            errors.append(f"{d.name}: frontmatter block does not parse")
            continue
        fms[d.name] = fm

        sid = fm.get("spec_id")
        if sid and sid != d.name:
            errors.append(f"{d.name}: spec_id '{sid}' != directory name")

        status = fm.get("status")
        closed_as = fm.get("closed_as")
        if status and status not in VALID_STATUS:
            errors.append(f"{d.name}: invalid status '{status}'")
        if status == "CLOSED":
            if closed_as not in VALID_CLOSED_AS:
                errors.append(f"{d.name}: CLOSED requires valid closed_as")
            if closed_as == "SUPERSEDED" and not as_list(fm.get("superseded_by")):
                errors.append(f"{d.name}: SUPERSEDED closure requires superseded_by")
        elif not is_empty(closed_as):
            errors.append(f"{d.name}: open spec requires closed_as null")

        for rel in ("depends_on", "supersedes", "superseded_by"):
            for target in as_list(fm.get(rel)):
                # A successor may live in another spec tree (e.g. a rewrite that carries
                # its own docs/specs/, cited by path). A path-shaped target is checked
                # against the filesystem instead of this tree's directory names.
                if not target:
                    continue
                if "/" in target:
                    if not (repo / target).is_dir():
                        errors.append(f"{d.name}: {rel} -> '{target}' path does not exist")
                elif target not in names:
                    errors.append(f"{d.name}: {rel} -> '{target}' is not a real spec")

        for feat in as_list(fm.get("features")):
            if feat in feature_owner:
                errors.append(
                    f"{d.name}: feature '{feat}' also declared by {feature_owner[feat]}"
                )
            else:
                feature_owner[feat] = d.name

    # Several ACTIVE specs are allowed only when none depends on another, directly or
    # through a chain of depends_on (Kun, 2026-10-24).
    def deps(name: str, seen: set[str]) -> set[str]:
        for t in as_list(fms.get(name, {}).get("depends_on")):
            if t and t not in seen and "/" not in t:
                seen.add(t)
                deps(t, seen)
        return seen
    active = [n for n, fm in fms.items() if fm.get("status") == "ACTIVE"]
    for a_ in active:
        for b_ in sorted(deps(a_, set()) & set(active)):
            errors.append(f"{a_}: ACTIVE beside {b_}, which it depends on; activate it after {b_} closes, or drop the dependency if it is not real")

    # bidirectional supersession
    for name, fm in fms.items():
        for tgt in as_list(fm.get("supersedes")):
            back = as_list(fms.get(tgt, {}).get("superseded_by"))
            if tgt in fms and name not in back:
                errors.append(f"{name}: supersedes '{tgt}' but it lacks superseded_by: {name}")
        # A FORK-FORWARD successor takes the leftovers, not the theme, so it names no
        # `supersedes` back; only a SUPERSEDED spec needs the reciprocal link.
        if fm.get("closed_as") == "FORK-FORWARD":
            continue
        for tgt in as_list(fm.get("superseded_by")):
            fwd = as_list(fms.get(tgt, {}).get("supersedes"))
            if tgt in fms and name not in fwd:
                errors.append(f"{name}: superseded_by '{tgt}' but it lacks supersedes: {name}")

    # A project that runs one sprint at a time passes --single-active: the lowest-numbered
    # ACTIVE spec is the queue head, and any other ACTIVE spec must record why in its Log.
    # Undeclared dependencies cannot be linted; this makes running several at once a
    # recorded choice instead of a default.
    if "--single-active" in sys.argv:
        def num(n: str) -> int:
            m = re.match(r"(\d+)", n)
            return int(m.group(1)) if m else 10**9
        active = sorted((n for n, fm in fms.items() if fm.get("status") == "ACTIVE"), key=num)
        for extra in active[1:]:
            # Split specs keep their Log in tasks.md, so read every file of the spec.
            text = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in sorted((root / extra).glob("*.md")))
            log = text.split("## Log", 1)
            if len(log) < 2 or "owner exception" not in log[1].lower():
                errors.append(f"{extra}: ACTIVE beside {active[0]} without an 'owner exception' line in its Log")

    quiet = "--quiet" in sys.argv
    if errors:
        print(f"spec_lint: {len(errors)} frontmatter violation(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if not quiet:
        print(f"spec_lint: {len(fms)} specs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
