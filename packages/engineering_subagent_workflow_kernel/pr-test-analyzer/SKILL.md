---
name: pr-test-analyzer
description: Analyze whether tests cover the behavior changed by a commit, branch, PR, patch, or working tree. Use when the user asks about test coverage quality, missing test cases, regression protection, test sufficiency, or explicitly asks for a dedicated pr-test-analyzer subagent.
---

# PR Test Analyzer

Delegate test-gap analysis to one independent native subagent when available.
Do not invoke `codex-subagent` or start a nested `codex exec` process.

## Workflow

1. Read repository rules and identify the exact change scope and available test
   evidence.
2. Read `references/role.md` completely.
3. Spawn a native subagent with a self-contained read-only task containing the
   target root, diff or commit scope, relevant test commands, and constraints.
   Mark it as the dedicated test-analysis child and tell it not to delegate
   again.
4. Let the child inherit the current model and policy. Require source and test
   line references for every claimed gap.
5. Verify the returned behavior-to-test map, integrate actionable gaps, and
   close the child.

## Native Child Execution

If the current session was explicitly spawned as the dedicated native child for
this role, execute `references/role.md` directly, do not spawn a descendant,
and report `executed_as_native_child`.

## Fallback

If the current session is not already the dedicated child and native subagents
are unavailable, analyze tests in the main session and label the execution
`fallback_in_session`.

## Boundaries

- Remain read-only unless the user separately asks to add tests.
- Evaluate behavioral coverage, not line-count percentages alone.
- Distinguish tests that exist, tests that ran, and tests whose outcomes are
  current.
