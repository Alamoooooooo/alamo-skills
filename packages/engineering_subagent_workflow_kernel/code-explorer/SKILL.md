---
name: code-explorer
description: Trace existing code paths and explain repository behavior with precise source evidence. Use when the user asks how code works, where behavior is implemented, which modules call each other, what an execution path does, or explicitly asks for a dedicated code-explorer subagent.
---

# Code Explorer

Delegate source tracing to one dedicated native subagent when available. Do not
invoke `codex-subagent` or start a nested `codex exec` process.

## Workflow

1. Identify the repository root, read its governance documents, and bound the
   requested path or behavior.
2. Read `references/role.md` completely.
3. Pass a self-contained read-only task to the host's native subagent spawning
   tool, including target path, entry clues, scope, and requested output. Mark
   the receiver as the dedicated child and tell it not to delegate again.
4. Let the child inherit the current model and policy. Require it to inspect the
   source directly and cite files and lines.
5. Review the trace for unsupported claims, integrate the result, and close the
   child.

## Native Child Execution

If the current session was explicitly spawned as the dedicated native child for
this role, execute `references/role.md` directly, do not spawn a descendant,
and report `executed_as_native_child`.

## Fallback

If the current session is not already the dedicated child and native subagents
are unavailable, perform the trace in the main session and label the execution
`fallback_in_session`.

## Boundaries

- Remain read-only.
- Do not infer dynamic behavior from names alone.
- Separate confirmed flow, configuration-dependent branches, and unresolved
  behavior.
