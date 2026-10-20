---
name: code-architect
description: Produce an evidence-grounded implementation architecture for an existing codebase. Use when the user asks for an architecture blueprint, feature design, refactoring design, module boundaries, data flow, implementation sequencing, or explicitly asks for a dedicated code-architect subagent.
---

# Code Architect

Delegate architecture analysis to one dedicated native subagent when the host
supports subagents. Do not invoke `codex-subagent`, start a nested `codex exec`,
or require an external agent-card runner.

## Workflow

1. Read the target repository rules and enough source context to bound the task.
2. Read `references/role.md` completely.
3. Prepare a self-contained delegation message with the target path, requested
   outcome, scope, constraints, known evidence, and required output. State that
   the receiver is the dedicated native child for this role and must not spawn
   another descendant.
4. Use the host's native subagent spawning tool. Prefer a fresh context and let
   the child inherit the current model and policy unless the user requested an
   override.
5. Require the child to read `references/role.md`, inspect the codebase itself,
   remain read-only, and cite concrete files and lines.
6. Do not duplicate the delegated analysis while it runs. Review the returned
   blueprint against repository evidence, then integrate it into the response.
7. Close the child after its result has been collected.

## Native Child Execution

If the current session was explicitly spawned as the dedicated native child for
this role, execute `references/role.md` directly, do not delegate again, and
report `executed_as_native_child` to the parent.

## Fallback

If the current session is not already the dedicated child and the host exposes
no native subagent tool, perform the same role in the main session and state
that `fallback_in_session` was used. Missing subagent support must not be
described as a successful dedicated delegation.

## Boundaries

- Architecture work is read-only unless the user separately asks for
  implementation.
- Repository rules, user scope, sandboxing, approval, and policy remain
  authoritative over Skill prose.
- A blueprint must distinguish inspected facts, assumptions, decisions, and
  unresolved risks.
