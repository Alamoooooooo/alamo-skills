# Portable Usage

The reusable part of this package is the separation between a short Skill
workflow and a bounded specialist role. A host does not need to understand the
Codex Skill token syntax, but it must decide whether it can provide a governed
native subagent.

## Host With Native Subagents

1. Select the relevant Skill directory.
2. Read its `SKILL.md` and `references/role.md`.
3. Compile a self-contained task context with target, scope, permissions,
   constraints, and output requirements.
4. Spawn one child through the host-native API and identify it explicitly as
   the dedicated child for the selected role.
5. Inherit or narrow parent policy; never broaden it from role prose.
6. Have the child execute the role directly and report
   `executed_as_native_child`; do not recursively delegate.
7. Verify the child result in the parent and close the child.

## Host Without Native Subagents

Execute the same role in the main agent context and mark the result
`fallback_in_session`. Do not silently launch another CLI process and call it a
native child.

## Adapter Requirements

A portable adapter should expose at least:

- native-subagent availability;
- inherited scope and policy;
- task submission and result collection;
- cancellation or close semantics;
- child identity and execution status;
- explicit read/write boundary;
- fallback status.

An external runner is a separate adapter type. It must declare its executable,
agent-card resources, process boundary, model selection, sandbox behavior, and
approval behavior before execution.
