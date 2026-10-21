# Installing engineering_subagent_workflow_kernel

## What gets installed

Five skills, each independent:

| Skill | Job |
|:--|:--|
| `code-explorer` | Trace an execution path and explain how code works, with source evidence |
| `code-architect` | Produce an implementation blueprint for a feature or refactor |
| `code-reviewer` | Review changes for defects, regressions, security risk, missing tests |
| `code-simplifier` | Reduce complexity while preserving observable behaviour |
| `pr-test-analyzer` | Find test gaps in a change set |

Each skill's role reference ships inside its own directory. Install all five —
they are selected per task, and one missing skill just means that job falls back
to the main session for no reason.

Python 3.8+ standard library only.

## Install on Codex

```bash
cd packages/engineering_subagent_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

Destination defaults to `$CODEX_HOME/skills`, or `~/.codex/skills` when
`CODEX_HOME` is unset.

## Install on any host that reads `SKILL.md`

```bash
cp -r code-explorer code-architect code-reviewer code-simplifier pr-test-analyzer \
      ~/.workbuddy/skills/
```

## Verify

Run the cheapest one first:

> Use code-explorer to trace how X is wired, read-only.

A working install opens with what it will read, produces file-and-line evidence,
and ends with a summary rather than a patch. The run should state whether it
executed as a native child or fell back into the main session.

## Pitfalls

**Do not install only the `SKILL.md` files.** Some third-party bundles ship the
skill files without their surrounding resources; the scripts in this package are
written to copy whole directories for exactly that reason. If you copy by hand,
copy the directory.

**Hosts without native subagents still work, differently.** The skill runs in the
main session and reports `fallback_in_session`. The output is usable but shares
the parent's context and turn budget, so a large exploration can crowd out the
rest of the conversation. A session that already *is* the dedicated native child
executes the role directly and reports `executed_as_native_child` — it does not
spawn another child.

**The package never overrides the host.** Approvals, sandboxing, model choice,
repository rules and tool availability remain the host's decision. There is no
helper binary, no nested agent process, and no model selection hidden in here.

**These are read-mostly skills.** Only `code-simplifier` is expected to edit
code, and only within the scope it was given. If `code-explorer` or
`code-reviewer` starts writing files, that is a bug in the invocation, not a
feature.

## Uninstall

```bash
rm -rf ~/.codex/skills/code-explorer ~/.codex/skills/code-architect \
       ~/.codex/skills/code-reviewer ~/.codex/skills/code-simplifier \
       ~/.codex/skills/pr-test-analyzer
```

No global state, no Git hooks, no configuration files outside those directories.
