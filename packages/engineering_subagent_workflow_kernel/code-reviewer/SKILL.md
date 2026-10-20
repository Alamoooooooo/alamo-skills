---
name: code-reviewer
description: Review code changes for correctness defects, regressions, security risks, unsafe behavior, and missing tests. Use when the user asks for a code review, PR review, independent post-change review, or explicitly asks for a dedicated code-reviewer subagent.
---

# Code Reviewer

Delegate review to one independent native subagent when available. Do not use
`codex-subagent` or a nested `codex exec` process.

## Workflow

1. Read repository rules and determine the exact review scope from the working
   tree, commit, branch, PR, or files named by the user.
2. Read `references/role.md` completely.
3. Spawn a native subagent with a self-contained read-only review task. Include
   the target root, change scope, relevant constraints, and test evidence, but
   do not leak a preferred conclusion. Mark it as the dedicated reviewer child
   and tell it not to delegate again.
4. Let the reviewer inherit the current model and policy. Require findings to
   cite exact files and lines.
5. Check each returned finding against the current source, remove unsupported
   claims, present valid findings first, and close the child.

## Native Child Execution

If the current session was explicitly spawned as the dedicated native child for
this role, execute `references/role.md` directly, do not spawn a descendant,
and report `executed_as_native_child`.

## Fallback

If the current session is not already the dedicated child and native subagents
are unavailable, review in the main session and label the execution
`fallback_in_session`.

## Boundaries

- Review is read-only unless the user separately requests fixes.
- Prioritize defects and regressions over style preferences.
- Do not report a clean review without naming residual test gaps or risk.
