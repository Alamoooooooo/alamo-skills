#!/usr/bin/env python3
"""Repository self-check: pairing, links, metadata, script syntax.

Every rule this script enforces is a rule from CONTRIBUTING.md. If the check
passes, those rules hold; if it fails, the output names the file and the reason,
so a reviewer does not have to look for it by hand.

    python3 scripts/check.py          # run everything
    python3 scripts/check.py --quiet  # only failures

Exit code is 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".obsidian", ".trash"}
# A markdown link target that is not checked: external, anchor-only, or an
# illustrative absolute path such as file:///… in the design notes.
SKIP_LINK_PREFIX = ("http://", "https://", "mailto:", "#", "<", "/", "file:", "…")
REQUIRED_PACKAGE_FILES = ("README.md", "PORTABLE_USAGE.md", "metadata.json")
METADATA_REQUIRED = ("name", "summary", "repository_role", "license")

problems: list[str] = []


def fail(where: str, why: str) -> None:
    problems.append(f"{where}: {why}")


def walk(base: str = ROOT):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            yield os.path.join(dirpath, name)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def md_files():
    return [p for p in walk() if p.endswith(".md")]


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_package_files() -> None:
    pkg_root = os.path.join(ROOT, "packages")
    if not os.path.isdir(pkg_root):
        fail("packages/", "missing")
        return
    for name in sorted(os.listdir(pkg_root)):
        pkg = os.path.join(pkg_root, name)
        if not os.path.isdir(pkg):
            continue
        for required in REQUIRED_PACKAGE_FILES:
            if not os.path.isfile(os.path.join(pkg, required)):
                fail(f"packages/{name}/", f"missing {required}")
        has_skill = False
        for _, _, filenames in os.walk(pkg):
            if "SKILL.md" in filenames:
                has_skill = True
                break
        if not has_skill:
            fail(f"packages/{name}/", "no SKILL.md anywhere inside")


def check_bilingual_pairs() -> None:
    for path in walk():
        name = os.path.basename(path)
        if not name.endswith(".md"):
            continue
        base = os.path.dirname(path)
        if name.endswith(".zh-CN.md"):
            twin = name[: -len(".zh-CN.md")] + ".md"
            if not os.path.isfile(os.path.join(base, twin)):
                fail(rel(path), f"Chinese version has no English twin ({twin})")
        elif name in ("README.md", "INSTALL.md"):
            twin = name[: -len(".md")] + ".zh-CN.md"
            if name == "INSTALL.md" and not os.path.isfile(os.path.join(base, twin)):
                fail(rel(path), "INSTALL.md requires INSTALL.zh-CN.md")


def check_links() -> None:
    for path in md_files():
        base = os.path.dirname(path)
        text = read(path)
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if target.startswith(SKIP_LINK_PREFIX):
                continue
            if re.match(r"^[A-Za-z]:[\\/]", target):
                continue
            clean = target.split("#")[0]
            if not clean:
                continue
            full = os.path.normpath(os.path.join(base, clean))
            if not os.path.exists(full):
                fail(rel(path), f"dead link -> {target}")


def check_metadata() -> None:
    for path in walk():
        if not path.endswith("metadata.json"):
            continue
        try:
            data = json.loads(read(path))
        except json.JSONDecodeError as exc:
            fail(rel(path), f"invalid JSON: {exc}")
            continue
        for key in METADATA_REQUIRED:
            if key not in data:
                fail(rel(path), f"missing key: {key}")
        if "license" in data and data["license"] != "Apache-2.0":
            fail(rel(path), 'license must be "Apache-2.0"')


def check_scripts() -> None:
    for path in walk():
        if not path.endswith(".py"):
            continue
        # compile() rather than py_compile: no __pycache__ is written, so running
        # the check cannot itself create the artifacts the next check forbids.
        try:
            compile(read(path), path, "exec")
        except SyntaxError as exc:
            fail(rel(path), f"does not compile: {exc.msg} (line {exc.lineno})")


def check_root_readmes() -> None:
    en = os.path.join(ROOT, "README.md")
    zh = os.path.join(ROOT, "README.zh-CN.md")
    if not (os.path.isfile(en) and os.path.isfile(zh)):
        fail("README.md / README.zh-CN.md", "one of the two is missing")
        return
    n_en = len(re.findall(r"^## ", read(en), re.M))
    n_zh = len(re.findall(r"^## ", read(zh), re.M))
    if n_en != n_zh:
        fail(
            "README.md vs README.zh-CN.md",
            f"section count differs: {n_en} vs {n_zh}",
        )


def check_no_artifacts() -> None:
    bad_ext = {".pyc", ".pyo", ".zip", ".tmp"}
    for path in walk():
        name = os.path.basename(path)
        if os.path.splitext(name)[1] in bad_ext:
            fail(rel(path), "build artifact should not be committed")
        if name in (".DS_Store", "Thumbs.db"):
            fail(rel(path), "OS artifact should not be committed")


CHECKS = (
    ("package files", check_package_files),
    ("bilingual pairs", check_bilingual_pairs),
    ("relative links", check_links),
    ("metadata", check_metadata),
    ("script syntax", check_scripts),
    ("root README parity", check_root_readmes),
    ("no build artifacts", check_no_artifacts),
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Repository self-check")
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    args = ap.parse_args()

    for label, fn in CHECKS:
        before = len(problems)
        fn()
        found = len(problems) - before
        if not args.quiet:
            status = "ok" if found == 0 else f"{found} problem(s)"
            print(f"[{status:>14}] {label}")

    if problems:
        print()
        for p in problems:
            print(f"  ! {p}")
        print(f"\n{len(problems)} problem(s). Nothing is checked into git by this script.")
        return 1

    if not args.quiet:
        print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
