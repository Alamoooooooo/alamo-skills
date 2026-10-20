#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export.py —— 把课程导出成可离线阅读的教材。

产物：
  教材.md    —— 纯 Markdown（大纲 + 每份作业的题目 / 作答 / 批改反馈 + 资料库）
  教材.docx  —— 需要 python-docx（`pip install python-docx`）

用法:
  python export.py --course <course-dir>                 # 默认 教材.md
  python export.py --course <course-dir> --format docx   # 输出 教材.docx
  python export.py --course <course-dir> --out D:/x/教材.md
"""
import os
import re
import sys
import argparse
import datetime

import yaml


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def sections(body):
    """把 `## 标题` 切分成 dict（保持顺序）。"""
    out = []
    for chunk in re.split(r"\n(?=## )", body):
        m = re.match(r"## (.+)", chunk)
        if m:
            out.append((m.group(1).strip(), chunk[m.end():].strip()))
    return out


def load_course(course):
    syllabus = os.path.join(course, "syllabus.md")
    fm, body = ({}, "")
    if os.path.exists(syllabus):
        fm, body = split_fm(open(syllabus, encoding="utf-8").read())
    nodes = fm.get("nodes", [])

    hw_dir = os.path.join(course, "homework")
    hws = {}
    if os.path.isdir(hw_dir):
        for fn in sorted(os.listdir(hw_dir)):
            if fn.startswith("hw-") and fn.endswith(".md"):
                hfm, hbody = split_fm(open(os.path.join(hw_dir, fn), encoding="utf-8").read())
                hfm["_secs"] = dict(sections(hbody))
                hws[hfm.get("id") or fn[:-3]] = hfm
    return fm, body, nodes, hws


def build_md(course, title):
    fm, body, nodes, hws = load_course(course)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = [
        f"# {title} · 学习教材",
        "",
        f"> 导出于 {now} · 共 {len(nodes)} 个模块 / {len(hws)} 份作业",
        "> 由 study-coach 的 `export.py` 生成。作答与批改均取自作业笔记原文。",
        "",
        "---",
        "",
        "## 目录",
        "",
    ]
    for i, n in enumerate(nodes, 1):
        m = n.get("mastery")
        flag = f"{round(m * 100)}%" if m else "未开始"
        L.append(f"{i}. {n.get('title', n['id'])}（{flag}）")
    L += ["", "---", ""]

    for i, n in enumerate(nodes, 1):
        m = n.get("mastery")
        L += [f"## {i}. {n.get('title', n['id'])}", ""]
        if n.get("prereqs"):
            L.append(f"- 先修：{'、'.join(n['prereqs'])}")
        L.append(f"- 掌握度：{round(m * 100)}%" if m else "- 掌握度：未开始")
        L.append("")

        attached = n.get("homework") or []
        for hid in attached:
            h = hws.get(hid)
            if not h:
                continue
            L += [f"### 作业 · {h.get('title', hid)}", ""]
            L.append(
                f"- 状态：{h.get('status', 'pending')}｜等级：{h.get('grade', '-')}"
                f"｜分数：{h.get('score', '-')}｜批改次数：{h.get('attempts', 0)}"
            )
            L.append("")
            for key in ("题目要求", "我的作答", "批改反馈"):
                val = h["_secs"].get(key)
                if val:
                    L += [f"#### {key}", "", val, ""]
        L.append("")

    res = os.path.join(course, "resources", "资料库.md")
    if os.path.exists(res):
        L += ["---", "", "## 附录 · 资料库", ""]
        L.append(open(res, encoding="utf-8").read().strip())
        L.append("")

    return "\n".join(L)


def md_to_docx(md_text, out_path):
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.oxml.ns import qn
    except ImportError:
        print("[error] 缺 python-docx，先运行：pip install python-docx")
        return 1

    # 中文字体按平台选，并把 eastAsia 也指到同一字体，否则中文会落到默认字体
    font = {"nt": "Microsoft YaHei", "darwin": "PingFang SC"}.get(os.name, "Noto Sans CJK SC")
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = font
    style.font.size = Pt(10.5)
    try:
        style.element.rPr.rFonts.set(qn("w:eastAsia"), font)
    except Exception:
        pass

    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("#### "):
            doc.add_heading(ln[5:], level=3)
        elif ln.startswith("### "):
            doc.add_heading(ln[4:], level=2)
        elif ln.startswith("## "):
            doc.add_heading(ln[3:], level=1)
        elif ln.startswith("# "):
            doc.add_heading(ln[2:], level=0)
        elif ln.strip() in ("---", ""):
            pass
        elif ln.startswith("> "):
            p = doc.add_paragraph(ln[2:])
            p.style = doc.styles["Quote"] if "Quote" in [s.name for s in doc.styles] else p.style
        elif ln.startswith("- ") or re.match(r"^\d+\. ", ln):
            doc.add_paragraph(re.sub(r"^(-\s+|\d+\.\s+)", "", ln), style="List Bullet")
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                raw = lines[i].strip().strip("|")
                if not re.match(r"^[\s:\-|]+$", raw):
                    rows.append([c.strip() for c in raw.split("|")])
                i += 1
            if rows:
                cols = max(len(r) for r in rows)
                t = doc.add_table(rows=0, cols=cols)
                t.style = "Table Grid"
                for r in rows:
                    cells = t.add_row().cells
                    for j in range(cols):
                        cells[j].text = re.sub(r"[*`]", "", r[j] if j < len(r) else "")
            continue
        else:
            doc.add_paragraph(re.sub(r"[*`]", "", ln))
        i += 1

    doc.save(out_path)
    print(f"[ok] 已导出 Word: {out_path}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="课程教材导出")
    ap.add_argument("--course", required=True, help="课程实例目录")
    ap.add_argument("--format", default="md", choices=["md", "docx"])
    ap.add_argument("--out", help="输出路径（缺省写到课程目录下 教材.md / 教材.docx）")
    ap.add_argument("--title", default=None, help="教材标题，缺省用目录名")
    args = ap.parse_args()

    course = os.path.abspath(args.course)
    if not os.path.isdir(course):
        print(f"[error] 课程目录不存在: {course}")
        return 2
    title = args.title or os.path.basename(course)

    md = build_md(course, title)
    if args.format == "md":
        out = args.out or os.path.join(course, "教材.md")
        open(out, "w", encoding="utf-8").write(md)
        print(f"[ok] 已导出 Markdown: {out}（{len(md)} 字符）")
        return 0

    out = args.out or os.path.join(course, "教材.docx")
    return md_to_docx(md, out)


if __name__ == "__main__":
    sys.exit(main())
