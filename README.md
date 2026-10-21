# Alamo Skill Hub

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Packages: 4](https://img.shields.io/badge/packages-4-6f42c1)](#what-is-in-here)
![Portable agent skills](https://img.shields.io/badge/agent%20skills-portable-2ea44f)

**English** | [简体中文](README.zh-CN.md)

## What Is In Here

| Package | Installs as | Solves | Entry point | Developed |
|:--|:--|:--|:--|:--|
| [`coursecoach`](packages/coursecoach/) | 1 skill | Turning a learning goal into a runnable course | `/coursecoach` | 2026-10-20 |
| [`engineering_subagent_workflow_kernel`](packages/engineering_subagent_workflow_kernel/) | 5 skills | Exploration, architecture, review, simplification, test-gap analysis via host subagents | `$code-explorer` and siblings | 2026-10-20 |
| [`github_sync_workflow_kernel`](packages/github_sync_workflow_kernel/) | 1 skill | Finding the real repo, checking auth, scoping the commit, pushing, verifying | `$github-sync-agent` | 2026-07-21 → 07-22 |
| [`memory_hotspot_repair_kernel`](packages/memory_hotspot_repair_kernel/) | 4 skills | Python memory hotspots: find, fix, validate, review, stop | `$memory-optimizer-agent` | 2026-07-03 → 07-22 |

All four are Apache-2.0, pure Python 3.8+ standard library plus `pyyaml`, and carry no backend.

## The Packages

### coursecoach

The odd one out — it is not about code, it is a learning coach. Give it a topic and a daily time budget and it produces a course that runs: a dependency-ordered syllabus, a compiled interactive board you double-click, written lessons, gradable homework, mastery-gated unlocking, and spaced review.

It is subject-agnostic — programming, a foreign language, an instrument, accounting, an exam all work. What separates it from "ask a model for a study plan" is what happens after the plan: scores, unlocks and review dates live in the files, so a course survives across sessions, can be picked up by a different model, and can be zipped and handed to someone who just double-clicks the board.

**Six things it does.** All triggered in plain language, and every one has a matching button on the board that assembles the sentence for you:

- **Start a course** — say "I want to learn X, one hour a day." It asks about your goal, your current level and your real weekly capacity, offers three pace options (sprint / standard / long), then researches the field, builds the prerequisite graph over a dozen or so nodes, and compiles the board. Produces `syllabus.md` (the only source of truth), `课程主页.html`, and `resources/资料库.md`.
- **Write lessons** — click `📖 补这一章讲解` (fill in this chapter) under any stage, or open a knowledge-point tag and pick `生成讲解`. Works per chapter or per single point. Produces `lessons/stage3.md` or `lessons/stage3--梯度下降.md`; after a recompile the board grows a 📄 button that opens it typeset, with no Obsidian required.
- **Set homework** — say "give me homework on stage 3", or click `📝 给这一章出作业`. Writes the questions plus 3–6 rubric lines and leaves the answer section empty. Produces `homework/hw-*.md`, always in three parts: prompt / answer / feedback.
- **Grade it** — answer the questions, then say "grade hw-stage3-xxx." It judges each rubric line present / partial / absent with a reason (fixed rubric, and length earns nothing extra), converts that to mastery, writes it back, unlocks dependent nodes, and queues the work for review.
- **Fix weak spots** — say "I keep failing at X in stage 3." It reads which knowledge points repeatedly came back partial or absent, decides whether to add resources, split a node or introduce a new one, and writes targeted homework if that is what the gap needs. Changes go through `syllabus.py`, never by hand-editing.
- **Review and export** — "what's due today" returns items on the 1 / 3 / 7 / 16 / 35 / 75-day curve (postpone without corrupting the count); "export to Word" gives you the whole course as one document.

![A generated course board: fourteen stages in the sidebar, a 0% mastery ring, one expanded stage showing nine knowledge-point tags, a homework row with a grading button, and four action buttons; later stages remain locked](packages/coursecoach/docs/board.png)

![A lesson opened in the in-page reader: the board dimmed behind a centred panel showing a typeset heading, a numbered list, a key-idea box and a worked example — with no Obsidian installed](packages/coursecoach/docs/lesson-reader.png)

**Not installing anything yet?** The [live demo](https://coursecoach-demo.app.workbuddy.host/?sharecode=DGYMO3ZV3W) is a real course compiled from the example snapshot, with five lessons inlined: expand a stage, open a lesson, try the search. Nothing to set up.

**Install it** (three steps, about a minute):

```bash
git clone https://github.com/Alamoooooooo/alamo_hub.git
cp -r alamo_hub/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
pip install pyyaml
```

- The installable unit is the directory holding `SKILL.md`, i.e. `coursecoach/coursecoach/`. Once copied, **the folder name must be `coursecoach`** — matching the skill's own name — or the slash command will not resolve.
- On Windows the destination is `C:\Users\<you>\.workbuddy\skills\coursecoach\`. Dropping it in a project's `.workbuddy/skills/` scopes it to that project instead.
- Codex reads `$CODEX_HOME/skills`; hosts without skill support can take `SKILL.md` plus `references/` straight into context and run the scripts by hand.
- Requires Python 3.8+, and **that interpreter must be able to `import yaml`**. Word export additionally needs `pip install python-docx`.
- Reopen the session before it is recognized. Then say "I want to learn X" or `/coursecoach` directly.

Do not start with a real subject — [the install guide](packages/coursecoach/INSTALL.md) includes a 15-minute trial course that shows the whole loop before you commit to anything.

Read: [package README](packages/coursecoach/README.md) · [中文说明](packages/coursecoach/README.zh-CN.md) · [install and 15-minute trial](packages/coursecoach/INSTALL.md) · [portable usage](packages/coursecoach/PORTABLE_USAGE.md)

### engineering_subagent_workflow_kernel

Five development skills that delegate through the host's own subagent mechanism instead of an external runner binary: `code-explorer`, `code-architect`, `code-reviewer`, `code-simplifier`, `pr-test-analyzer`.

Each skill is self-contained — its role reference ships with it. It does not install helper binaries, spawn nested agent processes, choose a model, or weaken the host's approval and sandbox policy. Hosts without native subagents fall back to in-session execution and report `fallback_in_session` so the difference is visible.

Read: [package README](packages/engineering_subagent_workflow_kernel/README.md) · [portable usage](packages/engineering_subagent_workflow_kernel/PORTABLE_USAGE.md)

```bash
cd packages/engineering_subagent_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

### github_sync_workflow_kernel

For the step everyone gets wrong once: deciding which directory is the real repository, whether the remote and auth are actually working, which changes belong in this commit and which are line-ending noise, and whether the push landed.

`github-sync-agent` runs repository discovery, auth and remote inspection, commit-scope review, commit, push, and post-push verification as one workflow. The wiki documents the failure modes it was built against.

Read: [package README](packages/github_sync_workflow_kernel/README.md) · [wiki](packages/github_sync_workflow_kernel/wiki/github-sync-workflow-wiki.md) · [portable usage](packages/github_sync_workflow_kernel/PORTABLE_USAGE.md)

```bash
cd packages/github_sync_workflow_kernel
python3 scripts/sync_to_codex_home.py
```

### memory_hotspot_repair_kernel

For Python services whose RSS keeps climbing, batch jobs that spike during joins or model scoring, and pipelines where "chunking" still loads the whole dataset.

Four coordinated skills: `memory-check` inspects and ranks hotspots, `memory-fix` remediates the highest-value one, `memory-review` reviews the change independently, and `memory-optimizer-agent` orchestrates all four into one bounded loop with explicit stop conditions. The other three also run standalone.

Read: [package README](packages/memory_hotspot_repair_kernel/README.md) · [long-form wiki](packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md) · [portable usage](packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md)

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

## Pick Your Starting Point

| You want to | Install | Then say |
|:--|:--|:--|
| Learn something properly | `coursecoach` | `I want to learn X, one hour a day.` |
| Hand a broad task to a subagent | `engineering_subagent_workflow_kernel` | `Use $code-explorer to trace how feature X is wired.` |
| Commit and push without guessing | `github_sync_workflow_kernel` | `Use $github-sync-agent to sync this repository.` |
| Stop a Python job from OOM-ing | `memory_hotspot_repair_kernel` | `Use $memory-optimizer-agent to optimize memory hotspots in the current codebase.` |

## Install

### Codex

```bash
git clone https://github.com/Alamoooooooo/alamo_hub.git
cd alamo_hub/packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

`sync_to_codex_home.py` copies into `$CODEX_HOME/skills`, or `~/.codex/skills` when `CODEX_HOME` is unset. Add `--dry-run` to preview. The three kernel packages each have their own copy of this script; install only the ones you want.

### WorkBuddy, CodeBuddy, Claude Code, or any host that reads `SKILL.md`

```bash
git clone https://github.com/Alamoooooooo/alamo_hub.git
cp -r alamo_hub/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
```

The installable unit is always the directory that contains `SKILL.md` — `coursecoach/coursecoach/`, `memory-optimizer-agent/`, `github-sync-agent/`, and so on. `pip install pyyaml` is required by `coursecoach`; `export.py --format docx` additionally needs `python-docx`.

For hosts that understand neither skill installation nor `$name` tokens, read the relevant `PORTABLE_USAGE.md`: it explains how to feed the manual and run the scripts by hand.

## Repository Layout

```text
alamo_hub/
├── README.md                          English (this file)
├── README.zh-CN.md                    简体中文
├── AGENTS.md                          conventions for agents working on this repo itself
├── llms.txt                           machine-readable summary for AI crawlers
├── LICENSE                            Apache-2.0
├── packages/                          ← the products
│   ├── README.md                      package conventions: three layers, required files, references vs wiki
│   ├── coursecoach/
│   │   ├── coursecoach/               the skill itself (SKILL.md, references, scripts, examples)
│   │   ├── docs/                      board.png, lesson-reader.png
│   │   └── README.md  README.zh-CN.md  PORTABLE_USAGE.md  INSTALL.md  INSTALL.zh-CN.md  metadata.json
│   ├── engineering_subagent_workflow_kernel/
│   │   ├── code-explorer/  code-architect/  code-reviewer/
│   │   ├── code-simplifier/  pr-test-analyzer/
│   │   ├── scripts/
│   │   └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
│   ├── github_sync_workflow_kernel/
│   │   ├── github-sync-agent/
│   │   ├── scripts/  wiki/
│   │   └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
│   └── memory_hotspot_repair_kernel/
│       ├── memory-optimizer-agent/    orchestrator (primary entry point)
│       ├── memory-check/  memory-fix/  memory-review/
│       ├── references/  scripts/  wiki/
│       └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
├── examples/                          ← optional, never required to install
│   ├── coursecoach/
│   │   └── quick-trial/stages.json    the smallest input that produces a 3-node course
│   └── memory_hotspot_repair_kernel/
│       └── partitioned_batch_pipeline/    one repo-specific adaptation: overlays + run configs
└── todo/                              ← unimplemented plans, nothing depends on them
    └── codex-plugin-packaging.md
```

`packages/` is the product, `examples/` is optional, `todo/` is ideas nobody has promised to build. The conventions that govern a package — the three layers, which files every package carries, what separates `references/` from `wiki/`, and which directory you are actually supposed to copy — live in **[`packages/README.md`](packages/README.md)**.

## Other Files

| File | What it is |
|:--|:--|
| `AGENTS.md` | Rules for an AI agent working *on this repository*: how to distinguish packages from examples, how to update docs and install paths. Not part of any product. |
| `llms.txt` | A flat summary of all four packages for AI crawlers and search. Same content as this README, optimised for machine reading. |
| `todo/` | Unimplemented plans, starting with `codex-plugin-packaging.md`. Read it as "considered, not promised" — nothing here depends on any of it. |
| `metadata.json` (per package) | Machine-readable descriptor: entry point, keywords, supported hosts, script list. |

## License

Apache-2.0. See [LICENSE](LICENSE).
