# CourseCoach · Install and Trial

**English** | [简体中文](INSTALL.zh-CN.md)

Turns an AI from "explains it once and stops" into a tutor that **sets homework,
grades it, and schedules review**: give it a subject, it confirms your goal and
pace, then produces a prerequisite-ordered syllabus, a double-clickable course
board, written lessons, homework with a rubric. Grading writes mastery back, and
review dates follow a forgetting curve.

Everything is local files. **No network, no database, no sign-up.**

> **On the name**: the package and the skill are both `coursecoach` — the thing
> you search for, install, and type is one word. The `coursecoach/` directory is
> the skill itself; there is no second copy anywhere.

---

## 1. Install (one minute)

**From the repository:**

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
pip install pyyaml
```

**Copy it into the skill directory of whichever host you use (pick one):**

```bash
# Claude Code
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.claude/skills/coursecoach

# Cursor
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.cursor/skills/coursecoach

# WorkBuddy / CodeBuddy
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
```

On Windows the destinations are `C:\Users\<you>\.claude\skills\coursecoach\`,
`C:\Users\<you>\.cursor\skills\coursecoach\` and
`C:\Users\<you>\.workbuddy\skills\coursecoach\`. Dropping it in a project's
`.claude/skills/` or `.cursor/skills/` scopes it to that project instead.

Reopen the session afterwards, then say "I want to learn X" or type
`/coursecoach` directly.

**In another agent or model** (Claude Code, Cursor, a home-grown pipeline):
`SKILL.md` is a plain Markdown manual and `references/` are its appendices. Feed
them into the system prompt or context and the whole flow still works; the
scripts run unchanged. Details in [PORTABLE_USAGE.md](PORTABLE_USAGE.md).

## 2. Requirements

- **Python 3.8+** and `pyyaml`: `pip install pyyaml`
- `python-docx` only for Word export: `pip install python-docx`
- Scripts use the standard library plus pyyaml — Windows, macOS and Linux alike,
  no platform lock-in
- **The only real requirement is that the interpreter can `import yaml`.** The
  one with dependencies installed is not necessarily called `python`; try
  `python3` or its absolute path

## 3. First run: build a 15-minute trial course

**Recommended**: in a skill-aware agent, just say "I want to learn X, an hour a
day." It walks through clarification → syllabus → board → homework, and you never
touch a command line.

To run it by hand instead, start with a `stages.json` describing nodes,
knowledge-point tags and the three pace tracks:

```json
[
  {"id":"s1","title":"基本概念","points":["定义","三个例子","常见误解"],"weeks":[1,1.5,3]},
  {"id":"s2","title":"核心方法","prereqs":["s1"],"points":["方法A","方法B"],"weeks":[1,1.5,3]},
  {"id":"s3","title":"动手实战","prereqs":["s2"],"points":["小项目","复盘"],"weeks":[2,2,4]}
]
```

Then build the course (swap `python` for whichever interpreter can `import yaml`):

```bash
python <skill>/scripts/init_course.py --dir ./demo --title "Trial course" --stages stages.json
```

It compiles the board along the way. **Double-click `demo/课程主页.html`** and you
get a collapsible syllabus, a progress ring, knowledge-point tags, and a row of
buttons at the bottom of every chapter: add a lesson, set homework, add
resources, select all points in the chapter.

Click a button → tick the actions → hit "copy command" in the bottom-right dock →
paste the text back into the chat. The agent writes the lesson, sets and grades
homework, re-runs `sync.py`, and the page grows.

**That is the core of the design**: the static page does not pretend to be a
backend. It collects actions and assembles a command. Judgement and writing go to
the model; deterministic computation goes to the scripts.

To see what a course looks like after a few weeks, double-click
`coursecoach/examples/ai-fullstack/课程主页.html` (a real course snapshot with the
answers cleared).

> **Where courses live**: the suggested default is `~/coursecoach/`, one directory
> per course (`~/coursecoach/<slug>/`). The agent confirms the location with you
> before creating anything — say the word if you want it elsewhere; it will not
> write to disk unasked.

Three commands you will use daily:

```bash
python <skill>/scripts/sync.py     --course ./demo        # recompile after editing any md
python <skill>/scripts/syllabus.py --course ./demo next   # what to study next
python <skill>/scripts/review.py   --course ./demo list   # what is due on the curve
```

## 4. Scheduled tasks do not travel with the files

The package ships **no** automations. That is deliberate, not an oversight:
automations are host state, and they do not follow a folder to another machine.
What ships is the recipe to rebuild them, which takes one pass after install:

```bash
python <skill>/scripts/schedule.py --course <course-dir> --check    # is it worth it
python <skill>/scripts/schedule.py --course <course-dir> --json     # full spec
```

Hand the `--json` output to the agent and it creates two via the host's
automation API (**after asking you**):

| Task | Time | What it does |
|:--|:--|:--|
| Daily review reminder | 20:00 | Reports what is due; **never advances state on its own** |
| Weekly frontier pass | Monday 09:00 | Only if the subject moves fast enough to go stale |

On a host with no scheduling (a plain CLI, say) it **degrades without error**:
`review.py list` still computes what is due, nobody just reminds you. See
`coursecoach/references/portability.md`.

## 5. What is in the directory

| Path | Purpose |
|:--|:--|
| `coursecoach/SKILL.md` | The manual: seven phases, action protocol, grading rules, script arguments |
| `coursecoach/references/` | Eight appendices: data model, course design, grading rubric, parallel research, delivery, portability, action protocol, weekly frontier |
| `coursecoach/scripts/` | Nine deterministic scripts: init, syllabus, compile board, grade, review queue, export, reset, pack, schedule recipe |
| `coursecoach/assets/` | Blank templates for the syllabus and homework |
| `coursecoach/examples/ai-fullstack/` | A real course snapshot (answers cleared), double-clickable |

## 5.5 Reading a lesson (Obsidian optional)

`lessons/*.md` is plain Markdown. Four ways to read it, pick whichever fits:

1. **From the course board** — "📄 open this chapter's lesson" at the bottom of a
   chapter. With Obsidian installed it opens in the vault; without it, an in-page
   reader shows typeset headings, tables and code blocks.
2. **In a Markdown editor** — VS Code / Typora / Obsidian on `lessons/xxx.md`,
   best for annotating and taking notes.
3. **Exported as a textbook** — `python scripts/export.py --course <course-dir> [--format docx]`,
   for reading the whole course in one pass, printing, or sending to someone.
4. **Any text editor** — Notepad works. Best when you only want to search a term
   or copy a snippet.

The reader panel is pre-rendered into the HTML at compile time: **no network, no
extra software**. Send the course folder to someone else and they double-click
`课程主页.html` and read typeset lessons. What Obsidian adds is backlinks, the
graph and concept-card jumps — not the ability to read a lesson.

## 6. Boundaries (so expectations stay realistic)

- **It does not make the judgement for you.** How to split knowledge points,
  whether a question is good, how many points an answer earns — those are model
  judgements; the scripts only make them land on disk reliably. A stronger model
  visibly improves the result.
- **Resources need verification.** Links, free tiers and exam requirements found
  by search can be stale. They are marked "unverified" when generated; click
  them yourself before trusting them.
- **The goal has to be checkable.** It must reduce to "draw it / build it /
  explain it back / pass the test". Pure appreciation goals ("I want taste")
  have to be translated into observable behaviour first, or there is nothing to
  grade.
- **Paths in the examples are placeholders.** After swapping in your own course,
  run `sync.py` once and every path in the page updates to the real location.

## 7. When something breaks

| Symptom | Cause |
|:--|:--|
| `ModuleNotFoundError: yaml` | Wrong interpreter, or `pip install pyyaml` |
| Board will not open / blank | Double-click the html file directly; if the browser blocks `file://`, use Chrome |
| Numbers show `NaN` | A node is missing `weeks`; fix with `syllabus.py set-weeks` |
| The copied command points at the wrong directory | The course moved; re-run `sync.py --course <new location>` |
| Clicking a lesson does nothing | Page compiled by an older `sync.py`; re-run it and lessons get pre-rendered |
| A lesson opens as `#` and `**` everywhere | Same; re-run `sync.py`, or open `lessons/*.md` in a Markdown editor |
| Edits to `课程主页.html` keep reverting | It is a build artifact, fully overwritten on the next `sync.py`; edit `syllabus.md` |

---

Protocol details live in `coursecoach/SKILL.md`; design trade-offs in
`coursecoach/references/`. Read both before changing a script — several things
in there look simplifiable and degrade the moment you simplify them.
