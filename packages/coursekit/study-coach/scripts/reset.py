#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reset.py —— 把作业重置为「未作答 / 未批改」，并回退对应节点的 mastery。

用途：
  · 重做一份已批改的作业（保留题目与 rubric，只清空作答与反馈）
  · 分享 / 发布课程模板前脱敏（去掉真实作答与分数）
  · 演示数据回零

会做的事：
  1) 作业 frontmatter：status -> pending，score/grade/graded_at -> null，attempts -> 0，
     删除 review_due / review_count / last_reviewed
  2) 「## 我的作答」「## 批改反馈」两区内容清空为占位符（标题保留）
  3) 若该节点已无任何已批改作业，把 syllabus 里该节点 mastery 置 null
  4) 自动重编译主页

不会做的事：
  · 不删作业文件本身（要删请手工）
  · 不动「## 题目要求」与 `rubric`（那是题目设计，不是作答记录）

用法:
  python reset.py --course <course-dir> --hw hw-stage0-vec
  python reset.py --course <course-dir> --all
  python reset.py --course <course-dir> --all --keep-mastery   # 只清文字，保留掌握度
"""
import os
import re
import sys
import argparse
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))

ANSWER_PH = "（⬇️ 在这里作答 / 修改。脚本永远不会动这一块。）"
FEEDBACK_PH = "（⬇️ grade.py 自动写回：逐条 rubric 判定 + 分数 + 等级 + 改进建议。批改前为空。）"

GRADE_MASTERY = {"优秀": 0.9, "良好": 0.75, "及格": 0.6, "不及格": 0.0}


def split_fm(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not m:
        raise ValueError("找不到 frontmatter（文件需以 --- 包裹的 YAML 开头）")
    return m.group(1), text[m.end():]


def one_line(s):
    return s.replace("\r\n", "\n").replace("\r", "\n")


def reset_body(body):
    body = one_line(body)

    def repl_answer(m):
        return m.group(1) + "\n" + ANSWER_PH + "\n"

    body = re.sub(
        r"(##\s*我的作答[^\n]*\n)(.*?)(?=\n##\s*批改反馈|\Z)",
        repl_answer,
        body,
        flags=re.S,
    )

    if re.search(r"##\s*批改反馈", body):
        body = re.sub(
            r"(##\s*批改反馈[^\n]*\n)(.*)\Z",
            lambda m: m.group(1) + "\n" + FEEDBACK_PH + "\n",
            body,
            flags=re.S,
        )
    else:
        body = body.rstrip() + "\n\n## 批改反馈\n\n" + FEEDBACK_PH + "\n"
    return body


def resolve_hw(course, hw):
    if os.path.isabs(hw) and os.path.exists(hw):
        return hw
    for c in (
        os.path.join(course, hw),
        os.path.join(course, "homework", hw),
        os.path.join(course, "homework", hw + ".md"),
    ):
        if os.path.exists(c):
            return os.path.abspath(c)
    raise SystemExit(f"[error] 找不到作业: {hw}")


def all_hw(course):
    d = os.path.join(course, "homework")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.startswith("hw-") and f.endswith(".md")]


def reset_one(path):
    text = open(path, encoding="utf-8").read()
    fm_raw, body = split_fm(text)
    fm = yaml.safe_load(fm_raw) or {}
    before = (fm.get("status"), fm.get("score"), fm.get("grade"), fm.get("attempts"))

    fm["status"] = "pending"
    fm["score"] = None
    fm["grade"] = None
    fm["graded_at"] = None
    fm["attempts"] = 0
    for k in ("review_due", "review_count", "last_reviewed"):
        fm.pop(k, None)

    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    open(path, "w", encoding="utf-8", newline="\n").write("---\n" + new_fm + "---\n" + reset_body(body))
    print(f"[ok] 已重置 {os.path.basename(path)}：{before} -> ('pending', None, None, 0)")
    return fm.get("stage")


def refresh_mastery(course, stages):
    """节点下若已无已批改作业，把该节点 mastery 置 null。"""
    path = os.path.join(course, "syllabus.md")
    if not os.path.exists(path) or not stages:
        return
    text = open(path, encoding="utf-8").read()
    fm_raw, body = split_fm(text)
    fm = yaml.safe_load(fm_raw) or {}
    nodes = fm.get("nodes") or []
    by_id = {n["id"]: n for n in nodes}

    hw_dir = os.path.join(course, "homework")
    graded = {}
    if os.path.isdir(hw_dir):
        for fn in os.listdir(hw_dir):
            if fn.startswith("hw-") and fn.endswith(".md"):
                h = yaml.safe_load(split_fm(open(os.path.join(hw_dir, fn), encoding="utf-8").read())[0]) or {}
                if h.get("status") == "graded" and h.get("grade") in GRADE_MASTERY:
                    graded.setdefault(h.get("stage"), []).append(GRADE_MASTERY[h["grade"]])

    changed = []
    for sid in stages:
        n = by_id.get(sid)
        if not n:
            continue
        vals = graded.get(sid) or []
        new = (sum(vals) / len(vals)) if vals else None
        if vals:
            new = round(new, 3)
        if n.get("mastery") != new:
            n["mastery"] = new
            changed.append(f"{sid} -> {new if new is not None else 'null'}")

    if not changed:
        print("[skip] mastery 无需变更")
        return
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    open(path, "w", encoding="utf-8", newline="\n").write("---\n" + new_fm + "---\n" + body)
    print("[ok] mastery 已回退: " + "; ".join(changed))


def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)  # 别让子进程的日志抢在本脚本之前
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="重置作业作答与批改记录")
    ap.add_argument("--course", required=True, help="课程实例目录")
    ap.add_argument("--hw", default="", help="作业 md 路径或 homework/ 下文件名")
    ap.add_argument("--all", action="store_true", help="重置该课程全部作业")
    ap.add_argument("--keep-mastery", action="store_true", help="只清文字，不回退节点 mastery")
    args = ap.parse_args()

    course = os.path.abspath(args.course)
    if not os.path.isdir(course):
        raise SystemExit(f"[error] 目录不存在: {course}")
    if not args.all and not args.hw:
        raise SystemExit("[error] 需要 --hw <作业> 或 --all")
    if args.all and args.hw:
        raise SystemExit("[error] --all 与 --hw 不能同时用")

    targets = all_hw(course) if args.all else [resolve_hw(course, args.hw)]
    if not targets:
        raise SystemExit("[error] 没找到任何 hw-*.md")

    stages = []
    for p in targets:
        sid = reset_one(p)
        if sid:
            stages.append(sid)

    if not args.keep_mastery:
        refresh_mastery(course, stages)
    else:
        print("[skip] 按 --keep-mastery 保留 mastery")

    sync = os.path.join(HERE, "sync.py")
    if os.path.exists(sync):
        print("[run] 重编译课程主页 ...")
        subprocess.run([sys.executable, sync, "--course", course], check=False)


if __name__ == "__main__":
    main()
