# coursecoach example

Two ways to look at a course built by this skill, depending on whether you want
to read it or make one.

## Look at one first

The compiled board is a single static HTML file, so the fastest route needs no
install:

**Live demo** — <https://coursecoach-demo.app.workbuddy.host/?sharecode=DGYMO3ZV3W>
(the sharecode is part of the URL; the bare host returns 403)

That demo is a real course with five lessons inlined: expand a stage, click a
knowledge-point tag, open a lesson. It is compiled from the snapshot at
[`../../packages/coursecoach/coursecoach/examples/ai-fullstack/`](../../packages/coursecoach/coursecoach/examples/ai-fullstack/),
which is the fuller example: 14 nodes, a graded homework, the generated board,
the progress page for Obsidian, and the exported textbook.

## Make one yourself

`quick-trial/stages.json` is the smallest useful input: three nodes, three
knowledge points each, three pace tracks. Feed it to the initializer and you get
a working course in two commands.

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
cd alamo-skills

python3 packages/coursecoach/coursecoach/scripts/init_course.py \
  --dir /tmp/coffee \
  --title "手冲咖啡入门" \
  --stages examples/coursecoach/quick-trial/stages.json

python3 packages/coursecoach/coursecoach/scripts/sync.py --course /tmp/coffee
open /tmp/coffee/课程主页.html          # xdg-open on Linux, start on Windows
```

Both scripts need `pip install pyyaml`. `init_course.py` compiles the board
itself, so the second command is only there to show you the input/output split:
`syllabus.md` is yours to edit, `课程主页.html` is generated and never edited by
hand.

After this you have a board with three locked stages, no lessons, no homework.
Everything the skill does from there — writing a lesson, setting homework,
grading it, adding nodes for a gap — starts from that same syllabus file.

## What is deliberately absent

No compiled output is checked in here. A course is a folder produced by
`sync.py`; committing one every time it changes would mean reviewing diffs of a
90 KB generated HTML file. The packaged example under `packages/` exists because
people want to see a finished one without running anything.
