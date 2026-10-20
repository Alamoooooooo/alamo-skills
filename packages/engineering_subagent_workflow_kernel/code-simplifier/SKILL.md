---
name: code-simplifier
description: Simplify recently changed or explicitly scoped code while preserving observable behavior. Use when the user asks to reduce complexity, remove duplication, clarify an implementation, or explicitly asks for a dedicated code-simplifier subagent to make bounded code changes.
---

# Code Simplifier

Delegate one bounded simplification task to a native subagent when available.
Do not invoke `codex-subagent` or start a nested `codex exec` process.

## Workflow

1. Read repository rules, inspect the current changes, and define an explicit
   write set. Do not broaden the scope beyond recently changed or user-named
   files.
2. Read `references/role.md` completely.
3. Spawn a native subagent with the target root, authorized write set, behavior
   constraints, existing tests, and required validation. Mark it as the
   dedicated simplifier child and tell it not to delegate again.
4. Let the child inherit the current model, policy, sandbox, and approval
   boundaries. Require it to edit only its scoped workspace and list every
   changed file.
5. Review the returned patch, run proportional validation, integrate only
   behavior-preserving changes, and close the child.

## Native Child Execution

If the current session was explicitly spawned as the dedicated native child for
this role, execute `references/role.md` directly in the scoped workspace, do not
spawn a descendant, and report `executed_as_native_child`.

## Fallback

If the current session is not already the dedicated child and native subagents
are unavailable, simplify in the main session and label the execution
`fallback_in_session`.

## Boundaries

- Do not change public contracts, output formats, error semantics, or data
  meaning unless the user explicitly authorizes that behavior change.
- Preserve unrelated user changes.
- Stop when simplification would require speculative redesign.
