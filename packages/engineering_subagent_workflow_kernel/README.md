# Engineering Subagent Workflow Kernel

This package provides five installable development Skills that use a host's
native subagent mechanism instead of an external `codex-subagent` executable:

- `code-explorer`
- `code-architect`
- `code-reviewer`
- `code-simplifier`
- `pr-test-analyzer`

Each Skill contains its own role reference and an explicit fallback for hosts
without native subagents. The package does not install helper binaries, launch
nested `codex exec` processes, choose a model, or weaken the host's approval and
sandbox policy.

## Why This Package Exists

Installing only the Skill subdirectories from some third-party bundles can
leave thin wrappers that reference a missing runner or external agent cards.
This package is self-contained at the Skill-directory level, so the normal
Codex Skill sync path installs every resource each wrapper needs.

## Codex Installation

Preview the installation:

```bash
python3 scripts/sync_to_codex_home.py --dry-run
```

Install or update all five Skills:

```bash
python3 scripts/sync_to_codex_home.py
```

The default destination is `$CODEX_HOME/skills`, or `~/.codex/skills` when
`CODEX_HOME` is unset. Existing directories with the same five names are
replaced by the package versions.

## Runtime Contract

The normal execution path is:

```text
user request
  -> Skill trigger and instructions
  -> host-native subagent spawn
  -> scoped specialist work
  -> parent verification and integration
  -> child close
```

The host remains authoritative for permissions, sandboxing, approval, model,
repository rules, and tool availability. If no native subagent interface is
available, the Skill runs in the main session and reports
`fallback_in_session`. A session already created as the dedicated native child
executes the role directly and reports `executed_as_native_child`; it does not
recursively spawn another child.

## Verification

Validate all Skill directories with the Skill Creator validator, run the sync
script against a temporary destination, and forward-test at least
`code-architect` with a read-only repository task before treating the package
as operational.
