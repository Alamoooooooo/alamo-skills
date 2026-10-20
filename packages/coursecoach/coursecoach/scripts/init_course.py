#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_course.py —— 从阶段列表创建一个课程实例。

生成:
  <dir>/syllabus.md          （Skill Graph）
  <dir>/homework/            （空目录）
  <dir>/resources/资料库.md    （资料库骨架）
  <dir>/课程主页.html         （sync.py 编译）

用法:
  python init_course.py --dir D:/courses/rust --title "Rust 系统编程" --stages stages.json
  python init_course.py --dir D:/courses/rust --title "Rust 系统编程" --stages '[{"id":"s1","title":"基础"}]'
"""
import os
import sys
import json
import argparse
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def load_stages(s):
    if os.path.isfile(s):
        with open(s, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(s)


def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)  # 免得子进程日志抢在本脚本之前
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="创建课程实例")
    ap.add_argument("--dir", required=True, help="课程实例目录")
    ap.add_argument("--title", required=True, help="课程标题")
    ap.add_argument("--slug", default="", help="可选 slug（默认取目录名）")
    ap.add_argument("--stages", required=True, help="阶段 JSON（文件路径或内联）")
    ap.add_argument("--force", action="store_true", help="允许写入非空目录")
    args = ap.parse_args()

    course = os.path.abspath(args.dir)
    slug = args.slug or os.path.basename(course.rstrip("\\/"))
    if os.path.isdir(course) and os.listdir(course) and not args.force:
        raise SystemExit(f"[error] 目录非空，拒绝覆盖: {course}（用 --force 强制）")

    stages = load_stages(args.stages)
    if not isinstance(stages, list) or not stages:
        raise SystemExit("[error] stages 必须是非空数组")

    nodes = []
    ids = set()
    for s in stages:
        nid = s["id"]
        if nid in ids:
            raise SystemExit(f"[error] 重复节点 id: {nid}")
        ids.add(nid)
        node = {
            "id": nid,
            "title": s.get("title", nid),
            "prereqs": s.get("prereqs", []) or [],
            "homework": s.get("homework", []) or [],
            "mastery": None,
        }
        if s.get("summary"):
            node["summary"] = s["summary"]
        if s.get("points"):
            node["points"] = s["points"]
        if s.get("weeks"):
            w = s["weeks"]
            keys = ("sprint", "standard", "long")
            if isinstance(w, (int, float)):
                node["weeks"] = {k: float(w) for k in keys}
            elif isinstance(w, (list, tuple)):
                vals = [float(x) for x in list(w)[:3]] * 1
                while len(vals) < 3:
                    vals.append(vals[-1])
                node["weeks"] = dict(zip(keys, vals))
            else:
                node["weeks"] = {k: float(w.get(k) or 0) for k in keys}
        nodes.append(node)
    for n in nodes:
        miss = [p for p in n["prereqs"] if p not in ids]
        if miss:
            raise SystemExit(f"[error] 节点 {n['id']} 的先修不存在: {miss}")

    os.makedirs(course, exist_ok=True)
    os.makedirs(os.path.join(course, "homework"), exist_ok=True)
    os.makedirs(os.path.join(course, "resources"), exist_ok=True)

    fm = {"title": args.title, "track": "冲刺", "nodes": nodes}
    fm_text = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    body = (
        f"# {args.title}\n\n"
        f"> 由 coursecoach 生成（slug: {slug}）。Skill Graph 见上方 frontmatter；"
        f"节点按先修链串联，mastery ≥ {0.6} 解锁后继。\n\n"
        "## 使用说明\n\n"
        "- 做作业：打开 `homework/hw-*.md`，在「我的作答」区作答。\n"
        "- 看进度：`python scripts/sync.py --course <本目录>` 生成 `课程主页.html`。\n"
        "- 演化大纲：`python scripts/syllabus.py --course <本目录> add-node / set-prereqs`。\n"
    )
    with open(os.path.join(course, "syllabus.md"), "w", encoding="utf-8") as f:
        f.write("---\n" + fm_text + "---\n" + body)

    res = (
        "# 资料库\n\n> 课程资源清单。每条注明来源与用途，宁少勿滥。\n\n"
        "## 课程 / 教程\n\n## 书籍\n\n## 论文\n\n## 工具\n"
    )
    with open(os.path.join(course, "resources", "资料库.md"), "w", encoding="utf-8") as f:
        f.write(res)

    print(f"[ok] 课程已创建: {course}")
    print(f"     节点 {len(nodes)} 个: {', '.join(n['id'] for n in nodes)}")

    no_pts = [n["id"] for n in nodes if not n.get("points")]
    no_wk = [n["id"] for n in nodes if not any((n.get("weeks") or {}).values())]
    if no_pts:
        print(f"[warn] 缺 points（看板无知识点标签）: {', '.join(no_pts)}")
    if no_wk:
        print(f"[warn] 缺 weeks（看板无课时与周期）: {', '.join(no_wk)}")
    if no_pts or no_wk:
        print("       补齐：python scripts/syllabus.py --course <本目录> set-points/set-weeks <node> ...")

    sync = os.path.join(HERE, "sync.py")
    if os.path.exists(sync):
        subprocess.run([sys.executable, sync, "--course", course], check=False)


if __name__ == "__main__":
    main()
