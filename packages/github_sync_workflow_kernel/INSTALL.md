# Installing github_sync_workflow_kernel

## What gets installed

One skill, `github-sync-agent`. Its `agents/` and `references/` directories ship
inside it, so the whole directory is the unit.

Python 3.8+ standard library only — no dependencies to install.

## Install on Codex

```bash
cd packages/github_sync_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

Destination defaults to `$CODEX_HOME/skills`, or `~/.codex/skills` when
`CODEX_HOME` is unset.

## Install on any host that reads `SKILL.md`

```bash
cp -r github-sync-agent ~/.workbuddy/skills/github-sync-agent
```

Copy the directory, not just `SKILL.md`: the skill loads its role reference and
workflow notes from subdirectories next to itself.

## Verify

Ask something read-only first:

> Which repository is this workspace actually targeting, and what is unpushed?

A correct run reports the repository it picked, the branch, the remotes, and any
uncommitted changes **before** proposing a commit. If it jumps straight to
`git add -A`, stop — that is the failure mode this skill exists to prevent.

## Pitfalls

**It does not install or configure Git.** The skill assumes `git` works and that
authentication is already set up (SSH key or credential helper). It will help you
walk through a broken auth setup, but it does not hold credentials and installs
no binaries.

**A workspace root is often not the repository.** If you open a parent folder
containing several repositories, the skill is designed to discover the real
target first. If you already know which directory you want, say so — that removes
a discovery round.

**Committing is not the default ending.** It will stop after showing the diff
scope and wait when the change set looks unintended, mixed with generated files,
or dominated by line-ending noise. That pause is the feature; approving it
repeatedly without reading the scope defeats the purpose.

**Line-ending and generated-file noise is filtered on purpose.** If a file you
expected to see is missing from the proposed commit, it was classified as noise —
check the reported reason rather than forcing it in.

## Uninstall

```bash
rm -rf ~/.codex/skills/github-sync-agent
```

Nothing outside that directory is touched: no hooks, no Git config, no global
aliases.
