# Installing memory_hotspot_repair_kernel

## What gets installed

Four skills. They must end up side by side in the same parent directory:

| Skill | Role |
|:--|:--|
| `memory-optimizer-agent` | Orchestrator — the entry point you invoke |
| `memory-check` | Audit phase: risk patterns and hot paths |
| `memory-fix` | Remediation phase: targeted, safe changes |
| `memory-review` | Independent post-fix review |

All scripts use the Python 3.8+ standard library only. There is no
`pip install` step.

## Install on Codex

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py --dry-run    # print the plan first
python3 scripts/sync_to_codex_home.py
```

Destination defaults to `$CODEX_HOME/skills`, or `~/.codex/skills` when
`CODEX_HOME` is unset. `--dest` overrides it.

## Install on any host that reads `SKILL.md`

```bash
cp -r memory-optimizer-agent memory-check memory-fix memory-review ~/.workbuddy/skills/
```

Four separate copies into one parent directory — same layout the script produces.

## Verify

```bash
ls ~/.codex/skills | grep '^memory-'
```

Expect four names. Then ask the host something small ("check this file for
memory risks") and confirm the orchestrator announces an audit phase before
changing anything.

## Pitfalls

**The skills reference each other as siblings.** `memory-optimizer-agent` reads
`../memory-check/SKILL.md` for the audit phase, `../memory-fix/SKILL.md` for
remediation, and `../memory-review/SKILL.md` for the review. Installing one
skill into a directory of its own leaves those paths dangling; the failure shows
up mid-run, not at install time.

**Package-level `references/` is not installed.** `overlay-pattern.md` and
`generic-overlay-template.md` live at the package root and are addressed as
`../references/...` from inside each skill. That path only exists when you run
from a checkout of this repository. If you want repository-specific overlays
after installing, copy those two files next to the four skill directories.

**Existing directories are replaced, not merged.** The sync script deletes a
same-named destination before copying. Local edits under
`~/.codex/skills/memory-*/` are lost on the next sync; keep overlays outside
that tree.

**`runs/` is stripped on install.** The script ignores `runs/`, `__pycache__/`
and `*.pyc`, so run artifacts from a checkout do not travel with the skills.

## Uninstall

```bash
rm -rf ~/.codex/skills/memory-check ~/.codex/skills/memory-fix \
       ~/.codex/skills/memory-review ~/.codex/skills/memory-optimizer-agent
```

Remove all four together: a leftover skill will still be found by the
orchestrator's sibling paths and fail in a confusing way.
