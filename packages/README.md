# Packages

Four installable skill packages. Each one is self-contained: once you copy it
out of this repository, it still works. Nothing here needs a backend, a database
or an account.

This page is the map. It explains the layer every package shares, why the four
of them do not look identical, and which directory you are supposed to copy.

## The three layers

Every package has the same three layers, even when the middle one is more than
one directory.

1. **Package directory** — `packages/<package>/`. Everything about the package
   that is *not* installed: README, screenshots, metadata, install notes.
2. **Installable unit** — the directory holding `SKILL.md`. This is the only
   thing you copy into a host's skills folder.
3. **Content directories** inside the unit — `references/`, `scripts/`,
   `examples/`, `assets/`.

```text
packages/coursecoach/            ← 1. package: for reading, not for installing
├── README.md  README.zh-CN.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md
├── metadata.json
├── docs/board.png
└── coursecoach/                 ← 2. installable unit: copy THIS
    ├── SKILL.md
    └── references/  scripts/  examples/  assets/    ← 3. content
```

## Why `coursecoach/coursecoach` repeats itself

It is not a typo. The outer directory is the package, the inner one is the unit.

If the two were flattened into `packages/coursecoach/`, then
`cp -r packages/coursecoach ~/.workbuddy/skills/coursecoach` would also drag
`README.md`, `README.zh-CN.md` and a folder of PNGs into the skills directory.
Those files are for humans browsing this repository; the host does not need
them. Keeping the unit one level down makes the copy command exact.

A package repeats its name only when the package and the skill share a name.
`memory_hotspot_repair_kernel` contains four skills, so nothing repeats.

## Which directory to copy

| Package | Installable units | Copy command |
|:--|:--|:--|
| `coursecoach` | `coursecoach/` | `cp -r packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach` |
| `memory_hotspot_repair_kernel` | `memory-optimizer-agent/` `memory-check/` `memory-fix/` `memory-review/` | copy all four; the orchestrator is `memory-optimizer-agent` |
| `github_sync_workflow_kernel` | `github-sync-agent/` | `cp -r packages/github_sync_workflow_kernel/github-sync-agent ~/.workbuddy/skills/github-sync-agent` |
| `engineering_subagent_workflow_kernel` | `code-explorer/` `code-architect/` `code-reviewer/` `code-simplifier/` `pr-test-analyzer/` | copy all five |

The target folder name should match the skill's own name; slash commands and
`$` invocations resolve against it.

### Codex

Three of the four packages ship `scripts/sync_to_codex_home.py`, which copies
their units into `$CODEX_HOME/skills` (`~/.codex/skills` when `CODEX_HOME` is
unset) and replaces same-named directories:

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

`coursecoach` has no such script. It is a single unit, so the `cp -r` command in
the table above is the entire install, on Codex and everywhere else. A host that
does not install skills at all can still use any package — read its
`PORTABLE_USAGE.md`.

## What every package has

| Item | Required | Purpose |
|:--|:--|:--|
| `README.md` | yes | What the package is, who it is for, where to start |
| `PORTABLE_USAGE.md` | yes | How to use it on a host that does not install skills |
| `metadata.json` | yes | Machine-readable descriptor: entry point, skills, hosts, keywords |
| `SKILL.md` in each unit | yes | The manual the host actually loads |
| `scripts/` | optional | Deterministic work: parsing, compiling, writing files |
| `references/` | optional | Methodology the skill loads **at run time**, on demand |
| `wiki/` | optional | Long-form articles for **humans**, with their own assets |
| `INSTALL.md` | optional | Install plus a trial run, when the install has real pitfalls. Written as `INSTALL.<lang>.md` when it exists in one language only (`coursecoach` ships `INSTALL.zh-CN.md`) |
| `docs/` | optional | Screenshots referenced from the README |

`references/` and `wiki/` are not two names for one thing:

- `references/` is read by the agent while it works — rubrics, data models,
  overlay templates. Missing one changes behaviour.
- `wiki/` is read by a person who wants the background. Missing one changes
  nothing about how the skill runs.

A package with neither is fine: `engineering_subagent_workflow_kernel` keeps its
methodology inside each `SKILL.md` instead.

## Where the four differ, and why

| Package | Units | Run-time docs | Human docs | Extra |
|:--|:--|:--|:--|:--|
| `coursecoach` | 1, same name as package | `references/` inside the unit | `README.zh-CN.md` | `docs/` screenshots, `INSTALL.zh-CN.md` |
| `memory_hotspot_repair_kernel` | 4 | package-level `references/` | `wiki/` | — |
| `github_sync_workflow_kernel` | 1, different name | — | `wiki/` | — |
| `engineering_subagent_workflow_kernel` | 5 | — | — | `scripts/sync_to_codex_home.py` |

Two differences are deliberate and should stay:

- **Where `references/` lives.** A single-unit package keeps it inside the unit
  (it will be copied along). A multi-unit package keeps it at package level,
  because all four or five units read the same material and copying it four
  times would let the copies drift.
- **Uneven file sets.** `coursecoach` is the only package with screenshots and a
  Chinese README because it is the only one whose output is a visual artifact
  worth showing. Adding empty `docs/` folders to the others to make the tree
  look symmetrical would be noise.

## Adding a package

1. Create `packages/<name>/` with `README.md`, `PORTABLE_USAGE.md`,
   `metadata.json`.
2. Put each unit in its own directory containing `SKILL.md`.
3. Scripts used by a unit go in the unit's `scripts/`; scripts used to package
   the whole thing go in the package's `scripts/`.
4. Lists every unit under `skills` in `metadata.json`, with its path.
5. Add the package to both root READMEs — the summary table, its own section,
   and the repository tree. The English and Chinese versions are updated
   together; see `../AGENTS.md`.
