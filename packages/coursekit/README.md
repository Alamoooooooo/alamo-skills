# Coursekit

![A generated course board: fourteen stages in the sidebar, a 0% mastery ring, one expanded stage showing nine knowledge-point tags, a homework row with a grading button, and four action buttons; later stages remain locked](docs/board.png)

`coursekit` is an installable, portable agent skill package that turns a learning goal into a
course that actually runs: a dependency-ordered syllabus, a self-contained interactive board,
written lessons, gradable homework, mastery-gated progression, spaced review, and a periodic
frontier pass that keeps the syllabus from going stale.

Give it a topic and a daily time budget. It clarifies the goal with you, drafts the syllabus,
compiles a board you can double-click, writes the lesson, sets the homework, grades it against
a written rubric, writes the score back, unlocks the next node, and schedules the review.

**The installed skill is named `study-coach`.** `coursekit` is the package name; the skill inside
it keeps its short call name so invoking it stays cheap. There is no second copy — the package
directory *is* the skill directory plus package metadata.

## Why It Is Not Another Study-Coach Prompt

Most study assistants are a prompt that produces a plan. The plan then rots: nothing enforces
it, nothing scores it, and nothing notices when the field moves. Four properties do the real
work here.

**1. The syllabus is the only source of truth.** Progression, prerequisites, week budgets,
homework attachment, mastery and review dates all live in `syllabus.md` frontmatter. Prose in
the same file is for humans and is never parsed. There is no second file that can disagree.

**2. The board is a build artifact, not a document.** `课程主页.html` is compiled by `sync.py`
from the syllabus. It is never hand-edited, and the skill forbids it explicitly. This is why the
page can be regenerated after every change without drift — and why every number on it is
traceable to one YAML field.

**3. Scores have exactly one entry point.** Only `grade.py` may write `mastery`. The agent
decides *what* a score is; the script decides *where it goes* and which downstream nodes unlock.
A grade is therefore auditable: every score has a rubric line, a reason, and a physical location
in the file.

**4. A course is a folder.** Copy the folder to duplicate a course, zip it to share one, move it
and re-run `sync.py` to fix every path inside. No database, no server, no account.

## What It Produces

| Artifact | Producer | Editable |
|:--|:--|:--|
| `syllabus.md` | `init_course.py` / `syllabus.py` | yes — the single source of truth |
| `课程主页.html` | `sync.py` | **no** — recompiled on every sync |
| `课程进度.md` | `sync.py` | **no** — Obsidian-friendly mirror |
| `lessons/<node>.md` | the agent | yes — lessons, one per chapter or per point |
| `homework/<name>.md` | the agent | answers yes, scores no |
| `resources/资料库.md` | the agent | yes — curated, with a cost note per entry |
| two automations | `schedule.py` recipe + host | no — host state, rebuilt on demand |

## The Closed Loop

```
goal -> clarify -> syllabus (YAML) -> sync -> board
                                  |
        lesson <- action basket <- board     (the page only accumulates actions)
                                  |
        homework -> answers -> grade.py -> mastery -> unlock chain
                                  |
                        review.py -> 1/3/7/16/35/75 days
                                  |
                    weekly frontier -> syllabus.py -> sync
```

The board is deliberately dumb. It is static HTML with inlined data, so it opens from
`file://` with no server. It never pretends to grade, save, or call a model. It collects
selected actions into a clipboard-ready command; the agent executes that command on paste-back.
Deterministic work (compiling, unlocking, scheduling, writing YAML) stays in scripts; judgment
(what to teach, which answer deserves 0.75) stays with the model.

## Deterministic Scripts

Nine scripts, all parameterised by `--course`, all standard library plus `pyyaml`.

| Script | Role |
|:--|:--|
| `init_course.py` | scaffold a course from a stage spec, then compile |
| `syllabus.py` | add nodes, set mastery, prerequisites, points, weeks, track, start date |
| `sync.py` | compile the board and the progress mirror |
| `grade.py` | the only writer of `mastery`; computes the unlock chain |
| `review.py` | spaced-review queue; `mark` advances, `snooze` only moves the date |
| `export.py` | export a readable textbook, optionally to `.docx` |
| `reset.py` | clear answers and scores for a clean share or a restart |
| `pack.py` | package a **course** as a self-contained zip |
| `schedule.py` | emit the **recipe** for the two automations (never creates them) |

## What It Does Not Do

- **It does not grade consistently across models.** A stronger model grades better. The script
  makes the score auditable and correctly placed, not objectively correct.
- **It does not verify its own sources.** Every retrieved link, price or exam rule is marked
  `unverified` until a human clicks it.
- **It does not ship scheduled tasks.** Automations are host state: they do not survive a
  machine change and must not be faked inside a package. `schedule.py` emits the recipe; the
  agent recreates them on the destination host, and says so plainly when a host has no
  scheduling primitive.
- **It does not handle purely aesthetic goals.** "I want good taste" has to be translated into
  observable behaviour first, otherwise there is nothing to grade.

## Install

Skill directory (WorkBuddy / CodeBuddy / any host that reads `SKILL.md`):

```bash
git clone https://github.com/Alamoooooooo/alamo_hub.git
cp -r alamo_hub/packages/coursekit/study-coach ~/.workbuddy/skills/study-coach
pip install pyyaml
```

Then say "I want to learn X, one hour a day" or invoke `/study-coach`.

For non-Codex hosts, see [`PORTABLE_USAGE.md`](PORTABLE_USAGE.md).
中文安装与试玩步骤见 [`INSTALL.zh-CN.md`](INSTALL.zh-CN.md).

## Package Layout

```
packages/coursekit/
├── README.md               this file
├── PORTABLE_USAGE.md       host-agnostic usage and degradation notes
├── INSTALL.zh-CN.md        install + 15-minute trial run (Chinese)
├── metadata.json           machine-readable package descriptor
└── study-coach/            the skill itself (installed under this name)
    ├── SKILL.md            7 phases, action protocol, grading rules, script parameters
    ├── references/         8 deep docs, loaded on demand
    ├── scripts/            9 deterministic scripts
    ├── assets/             blank syllabus and homework templates
    └── examples/ai-fullstack/   a real course snapshot (answers cleared, mastery null)
```

## Start Here

1. [`study-coach/SKILL.md`](study-coach/SKILL.md) — the operating manual the agent follows.
2. `study-coach/examples/ai-fullstack/课程主页.html` — open it to see what a board looks like
   after a course has been running.
3. [`study-coach/references/portability.md`](study-coach/references/portability.md) — moving the
   skill to another agent or operating system.

## License

Apache-2.0, same as the repository.
