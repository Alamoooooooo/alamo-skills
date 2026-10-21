# Contributing

**English** | [简体中文](CONTRIBUTING.zh-CN.md)

This repository is four skill packages plus the docs around them. There is no
build step, no dependency install beyond `pyyaml`, and no service to run. What it
does have is a set of conventions that keep four packages understandable as they
drift apart, and most of them are enforced by one script.

## Run this before every pull request

```bash
python3 scripts/check.py
```

It verifies seven things:

| Check | What fails it |
|:--|:--|
| package files | a package missing `README.md`, `PORTABLE_USAGE.md` or `metadata.json`, or with no `SKILL.md` anywhere inside |
| bilingual pairs | `INSTALL.md` without `INSTALL.zh-CN.md`, or any `*.zh-CN.md` without its English twin |
| relative links | a markdown link to a file that does not exist |
| metadata | invalid JSON, a missing required key, or a license other than Apache-2.0 |
| script syntax | a `.py` file that does not compile |
| root README parity | the English and Chinese READMEs having a different number of `##` sections |
| no build artifacts | a committed `.pyc`, `.zip`, `.DS_Store` |

Green means every rule below still holds. Red names the file and the reason.
Exit code is non-zero, so it also works as a pre-push hook or a CI step.

## Five rules that carry the most weight

**1. One writer per piece of state.** Inside a package, anything that can be
derived has exactly one entry point that writes it. In `coursecoach`, only
`grade.py` writes a mastery score and only `syllabus.py` writes the node graph —
because a grade has to update the homework frontmatter, the feedback section, the
node's mastery and the unlock state together. Four manual edits will eventually
disagree, silently. If you find yourself editing generated output by hand, the
script is missing a flag, not the docs a warning.

**2. Do not commit build output.** Compiled course boards, exported textbooks and
packed zips stay out. The one exception is deliberate: the pre-built board inside
`packages/coursecoach/coursecoach/examples/` is committed so that someone can
double-click it without running anything. That file is a product sample, not a
build artifact — treat it as data, and regenerate it only when the sample course
itself changes.

**3. Bilingual files come in pairs.** The two root READMEs, and every package's
`INSTALL.md` / `INSTALL.zh-CN.md`. Editing one without the other leaves half the
audience with stale instructions, and nothing about the repository looks broken
afterwards. Section order is kept identical so a reader can check a translation
against the original by position.

**4. Changing a structure means changing `packages/README.md`.** That file is the
only place that explains the three layers, which directory gets copied, and why
`packages/coursecoach/coursecoach/` repeats itself. Add a file convention, move a
directory, or add a package, and it has to be updated in the same commit.

**5. Unbuilt plans go in `todo/`.** Not the repository root. A `TODO_*.md` at the
top level reads as a commitment to everyone who opens the repository; `todo/`
reads as "considered, not promised".

## Commit messages

One line, imperative, no trailing period. Then a blank line, then the reason: what
was wrong before, and why this shape. Do not restate the diff — a reviewer can
read it.

```
Point the README at the live demo

Everything in the coursecoach section asked the reader to install something
before they could judge it: two screenshots prove the board renders, but not
that clicking a stage opens a lesson.
```

One commit, one change. If the message needs "also", it is two commits.

## Before you touch a script

Run it. Not `--help` — an actual course. Compiling is not verification: a script
can compile and still write a broken file, and the failure shows up as a wrong
number in a board three steps later.

```bash
cp -r packages/coursecoach/coursecoach/examples/ai-fullstack /tmp/try
python3 packages/coursecoach/coursecoach/scripts/sync.py --course /tmp/try
```

Then look at the output, not just the exit code.

## What a reviewer checks

- Do both languages say the same thing, in the same order?
- Was any generated file edited instead of regenerated?
- Did the change touch a package structure without touching `packages/README.md`?
- Does the commit message say *why*, not just *what*?
- For a script change: was it actually run against a course?

Squash on merge. The history on `main` is one commit per idea; a pull request with
five `fix typo` commits should not change that.

## Adding a package

1. `packages/<name>/` with `README.md`, `PORTABLE_USAGE.md`, `metadata.json`
2. One directory per installable unit, each containing `SKILL.md`
3. `INSTALL.md` + `INSTALL.zh-CN.md` if the install has pitfalls worth writing down
4. A `license` field in `metadata.json` (`"Apache-2.0"` — the check enforces it)
5. A row in both root READMEs: summary table, its own section, repository tree

`packages/README.md` ends with the same checklist; keep the two in sync.

## Things that will be rejected

- Force-pushing `main`, or rewriting history that has already been published
- Committing `__pycache__`, `.pyc`, or a zip
- A new top-level file whose job is to hold a plan or a scratch note
- A "small cleanup" that renames directories — paths are user-facing, they are in
  install commands, and they are in text other people have already copied
- Unrelated changes bundled into one commit

## Where things live

| File | Answers |
|:--|:--|
| `README.md` | What is in this repository, how to install each package |
| `packages/README.md` | How a package is structured, which directory to copy, why they differ |
| `<package>/README.md` | What that package does, who it is for |
| `<package>/INSTALL.md` | How to install it, and what breaks if you do it subtly wrong |
| `<package>/PORTABLE_USAGE.md` | How to use it on a host that does not install skills |
| `AGENTS.md` | Rules for an AI agent working *on this repository* |
| `todo/` | Considered, not promised |

## License

Apache-2.0. By opening a pull request you agree your contribution is licensed
under the same terms (section 5 of the license); no separate CLA is needed.
Anything you distribute that contains this code must include a copy of `LICENSE`.
