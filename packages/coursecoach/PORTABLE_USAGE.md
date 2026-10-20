# Portable Usage

This document explains how to use `coursecoach` outside a host that natively installs `SKILL.md`
skills.

## Scope

Use this guide when:

- the target environment is not WorkBuddy / CodeBuddy / Codex
- the host has no `~/.workbuddy/skills` directory
- the host cannot resolve a slash-command token such as `/coursecoach`
- you want the workflow as a prompt bundle driven by your own runner

## What Is Portable

- `coursecoach/SKILL.md` — a plain Markdown operating manual, no host syntax required
- `coursecoach/references/` — eight attachments loaded on demand
- `coursecoach/scripts/` — Python 3.8+, standard library plus `pyyaml`
- `coursecoach/assets/` — blank templates
- the process itself: clarify -> syllabus -> compile -> lesson -> homework -> grade -> review

## What Is Not Portable

- **Skill installation.** Copying into `~/.workbuddy/skills/` is one host's convention. On other
  hosts, inject `SKILL.md` into the system prompt or context instead.
- **The slash token.** `/coursecoach` works only where skills are registered. Elsewhere, the same
  effect comes from saying "follow coursecoach/SKILL.md phase 1" and pointing at the file.
- **Scheduled tasks.** Two automations are optional and are *host state*, not files. They do not
  travel with the package. See "Scheduling" below.
- **The `obsidian://` lesson links.** Compiled automatically when the course directory sits inside
  a vault (detected by walking up for `.obsidian`); otherwise they fall back to `file://`.

## Dependencies

| Need | Requirement |
|:--|:--|
| everything | Python 3.8+ and `pyyaml` |
| `export.py --format docx` | `python-docx` (optional) |
| `obsidian://` links | Obsidian installed (optional; without it lessons open in an in-page reader) |
| the board | any modern browser; no server, no network |

The single hard requirement is that **the interpreter can `import yaml`**. A machine may have
several Pythons; point `schedule.py --json` at whichever one satisfies that, or use an absolute
path (which is what the recipe generator does by default, via `sys.executable`).

## Recommended Entry Point

The logical entry point is unchanged: the `coursecoach` skill.

1. Read `coursecoach/SKILL.md`.
2. Do not skip Phase 1 (clarify) or Phase 3 (plan confirmation). The rest of the workflow assumes
   a confirmed syllabus; skipping it produces a course nobody agreed to.
3. Keep the deterministic/judgment split. Scripts own YAML writes, mastery, the unlock chain and
   HTML compilation. The model owns explanation, grading and curation. Moving work across that
   line is the one change that reliably breaks the system.

## Scheduling

The package ships **no** automations. That is a design decision, not an omission: an automation
is host state, and a fake one inside a package is worse than none.

The package ships the **recipe** instead:

```bash
python coursecoach/scripts/schedule.py --course <course-dir> --check   # is it worth creating?
python coursecoach/scripts/schedule.py --course <course-dir> --json    # full spec
```

`--json` returns `name`, `rrule`, `prompt` and `cwds` computed from `__file__` and
`sys.executable`, so the paths point at *your* install location, not the author's. Hand that
output to an agent with a scheduling primitive and it creates the tasks.

| Task | Default time | Reads | Writes |
|:--|:--|:--|:--|
| daily review reminder | 20:00 | `review.py list --json` | nothing |
| weekly frontier pass | Mon 09:00 | syllabus + resources | `syllabus.py`, `resources/资料库.md` |

### Degradation when the host cannot schedule

| Missing capability | Behaviour |
|:--|:--|
| no automation primitive | Nothing is created. `review.py list` still computes due dates; you check it when you enter the course. Say so explicitly rather than leaving a dead task behind |
| no model access in the scheduler | Keep only the review reminder (pure script, no judgment). The frontier pass needs model judgment; run it manually |
| no `.obsidian` vault | Lessons are pre-rendered into `课程主页.html` at compile time and open in an in-page reader panel. Only concept-card links disappear |
| no `localStorage` | The action basket keeps selections in memory only; the flow still works within one session |
| no `python-docx` | `export.py` still emits Markdown; skip `--format docx` |

## Adapting to a Claude Code / Cursor style host

1. Put the skill where the host looks for skills, or paste `SKILL.md` as a system-level
   instruction file.
2. Reference `references/*.md` by path when the workflow reaches that phase — do not inline all
   eight documents into context.
3. Install `pyyaml` in whatever interpreter the host can reach.
4. Run one end-to-end trial on a throwaway course before committing a real study plan:

```bash
python coursecoach/scripts/init_course.py --dir ./demo --title "Trial" --stages stages.json
python coursecoach/scripts/sync.py --course ./demo
```

If `demo/课程主页.html` opens and shows a collapsible syllabus, the environment is ready.

## Verifying a port

Five checks, in order. Stop at the first failure.

1. `python <skill>/scripts/sync.py --course <course-dir>` finishes with no `[warn]`.
2. The board opens from `file://` and renders a progress ring.
3. `syllabus.py --course <course-dir> next` returns the next node and its homework state.
4. `schedule.py --course <course-dir> --json` emits a prompt whose paths match **your** install
   directory.
5. `examples/ai-fullstack/homework/*.md` has an empty answer block and `syllabus.md` has
   `mastery: null` everywhere — proof that the shipped example carries no real answers.
