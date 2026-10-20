#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syllabus.py —— 查询 / 修改 Skill Graph（课程大纲），并给出下一步建议。

用法:
  python syllabus.py --course <dir> list
  python syllabus.py --course <dir> add-node --id s3 --title "异步编程" [--prereqs s2] [--homework hw-s3]
  python syllabus.py --course <dir> set-mastery --id s1 --value 0.75
  python syllabus.py --course <dir> set-prereqs --id s3 --prereqs s1,s2
  python syllabus.py --course <dir> attach-hw --id s1 --hw hw-s1-basics
  python syllabus.py --course <dir> set-points --id s1 --points "广播|广播规则,形状"
  python syllabus.py --course <dir> set-weeks --id s1 --weeks 2,2.5,4
  python syllabus.py --course <dir> set-summary --id s1 --summary "一句话概述"
  python syllabus.py --course <dir> next
"""
import os
import re
import argparse

import yaml

UNLOCK_PASS = 0.6


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise SystemExit("[error] syllabus.md 缺少 frontmatter")
    return m.group(1), text[m.end():]


def load(course):
    path = os.path.join(course, "syllabus.md")
    if not os.path.exists(path):
        raise SystemExit(f"[error] 找不到 {path}")
    text = open(path, encoding="utf-8").read()
    fm_raw, body = split_fm(text)
    return yaml.safe_load(fm_raw) or {}, body, path


def save(fm, body, path):
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    open(path, "w", encoding="utf-8").write("---\n" + new_fm + "---\n" + body)


def umap(nodes):
    return {n["id"]: (n.get("mastery") or 0) for n in nodes}


def is_unlocked(n, m):
    pr = n.get("prereqs") or []
    return all(m.get(p, 0) >= UNLOCK_PASS for p in pr) if pr else True


def cs(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def cmd_list(nodes):
    m = umap(nodes)
    print(f"{'id':<22}{'mastery':<9}{'解锁':<6}{'作业':<24}title")
    print("-" * 96)
    for n in nodes:
        mv = n.get("mastery")
        mstr = "未开始" if mv is None else f"{mv:.2f}"
        print(f"{n['id']:<22}{mstr:<9}{'是' if is_unlocked(n, m) else '否':<6}{','.join(n.get('homework') or []) or '-':<24}{n.get('title','')}")


def parse_weeks(s):
    """--weeks "2" 或 "2,2.5,4"（sprint,standard,long）-> dict。"""
    if not s:
        return None
    parts = [x.strip() for x in str(s).split(",") if x.strip()]
    try:
        vals = [float(x) for x in parts]
    except ValueError:
        raise SystemExit(f"[error] --weeks 需为数字：{s}")
    if len(vals) == 1:
        vals = vals * 3
    elif len(vals) != 3:
        raise SystemExit("[error] --weeks 支持 1 个或 3 个数字（冲刺,标准,长线）")
    return {"sprint": vals[0], "standard": vals[1], "long": vals[2]}


def cmd_add_node(fm, a):
    nodes = fm.setdefault("nodes", [])
    if any(n["id"] == a.id for n in nodes):
        raise SystemExit(f"[error] 节点已存在: {a.id}")
    prereqs = cs(a.prereqs)
    ids = {n["id"] for n in nodes}
    miss = [p for p in prereqs if p not in ids]
    if miss:
        raise SystemExit(f"[error] 先修节点不存在: {miss}")
    node = {
        "id": a.id,
        "title": a.title,
        "prereqs": prereqs,
        "homework": cs(a.homework),
        "mastery": None,
    }
    if getattr(a, "summary", ""):
        node["summary"] = a.summary
    pts = cs(getattr(a, "points", ""))
    if pts:
        node["points"] = pts
    w = parse_weeks(getattr(a, "weeks", ""))
    if w:
        node["weeks"] = w
    nodes.append(node)
    print(f"[ok] 新增节点 {a.id} ({a.title})，先修 {prereqs or '无'}，知识点 {len(pts)} 个")


def find(nodes, nid):
    for n in nodes:
        if n["id"] == nid:
            return n
    raise SystemExit(f"[error] 找不到节点: {nid}")


def cmd_set_mastery(fm, a):
    n = find(fm.get("nodes", []), a.id)
    v = float(a.value)
    if not 0 <= v <= 1:
        raise SystemExit("[error] mastery 必须在 0-1")
    n["mastery"] = v
    print(f"[ok] {a.id} mastery -> {v}")


def cmd_set_prereqs(fm, a):
    nodes = fm.get("nodes", [])
    n = find(nodes, a.id)
    prereqs = cs(a.prereqs)
    ids = {x["id"] for x in nodes}
    miss = [p for p in prereqs if p not in ids]
    if miss:
        raise SystemExit(f"[error] 先修节点不存在: {miss}")
    if a.id in prereqs:
        raise SystemExit("[error] 节点不能以自己为先修")
    n["prereqs"] = prereqs
    print(f"[ok] {a.id} 先修 -> {prereqs or '无'}")


def cmd_attach_hw(fm, a):
    n = find(fm.get("nodes", []), a.id)
    hws = n.get("homework") or []
    if a.hw not in hws:
        hws.append(a.hw)
    n["homework"] = hws
    print(f"[ok] {a.id} 作业 -> {hws}")


def cmd_set_points(fm, a):
    """知识点标签：逗号分隔；支持 `标签|概念卡名` 映射到 Obsidian 概念卡。"""
    n = find(fm.get("nodes", []), a.id)
    items = [x.strip() for x in (a.points or "").split(",") if x.strip()]
    out = []
    for it in items:
        if "|" in it:
            t, note = [x.strip() for x in it.split("|", 1)]
            out.append({"t": t, "note": "20-概念/" + note if note else None})
        else:
            out.append(it)
    n["points"] = out
    print(f"[ok] {a.id} 知识点 {len(out)} 个 -> {[p if isinstance(p, str) else p['t'] for p in out]}")


def cmd_set_weeks(fm, a):
    n = find(fm.get("nodes", []), a.id)
    w = parse_weeks(a.weeks)
    if not w:
        raise SystemExit("[error] --weeks 不能为空")
    n["weeks"] = w
    print(f"[ok] {a.id} weeks -> {w}")


def cmd_set_summary(fm, a):
    n = find(fm.get("nodes", []), a.id)
    n["summary"] = a.summary
    print(f"[ok] {a.id} summary -> {a.summary}")


TRACK_ALIAS = {
    "sprint": "冲刺", "冲刺": "冲刺",
    "standard": "标准", "标准": "标准",
    "long": "长线", "长线": "长线",
}


def cmd_set_track(fm, a):
    """课程默认节奏档。输入接受中英文，统一存中文（与既有课程数据一致，sync 直接渲染）。"""
    key = TRACK_ALIAS.get((a.track or "").strip().lower())
    if not key:
        raise SystemExit("[error] --track 只接受 冲刺/标准/长线（或 sprint/standard/long）")
    fm["track"] = key
    print(f"[ok] 课程默认节奏 -> {key}（页面首次打开用此档；已开过的浏览器保留本地选择）")


def cmd_set_start(fm, a):
    """课程开始日期，用于主页算「第 X 周起」。接受 YYYY-MM-DD，也接受 today。"""
    import datetime
    v = (a.date or "").strip()
    if v.lower() in ("today", "now", "今天"):
        v = datetime.date.today().isoformat()
    try:
        d = datetime.date.fromisoformat(v)
    except ValueError:
        raise SystemExit("[error] --date 需要 YYYY-MM-DD（或写 today）")
    fm["start"] = d.isoformat()
    # 课程级字段放前面，避免 start 落在 nodes 长列表之后
    head = [k for k in ("title", "track", "start", "nodes") if k in fm]
    if [k for k in fm] != head + [k for k in fm if k not in head]:
        new = {k: fm[k] for k in head}
        new.update({k: v for k, v in fm.items() if k not in new})
        fm.clear()
        fm.update(new)
    print(f"[ok] 开课日期 -> {d.isoformat()}")


def cmd_next(nodes):
    m = umap(nodes)
    for n in nodes:
        if is_unlocked(n, m) and (n.get("mastery") or 0) < UNLOCK_PASS:
            state = "未开始" if n.get("mastery") is None else "未达标"
            hws = n.get("homework") or []
            print(f"[下一步] {n['id']} · {n['title']}  ({state}, mastery={n.get('mastery')})")
            if not hws:
                print("  → 该节点还没有作业，建议生成 hw-<id>.md 并 attach-hw")
            else:
                print(f"  → 已有作业 {hws}，去作答后说「批改 {hws[0]}」")
            return
    for n in nodes:
        if not is_unlocked(n, m):
            prereqs = n.get("prereqs") or []
            print(f"[下一步] 当前全部达标；下一个待解锁：{n['id']} · {n['title']}")
            print(f"  → 需先达标先修：{prereqs}")
            return
    print("[下一步] 所有节点已达标，可进入 Capstone / 扩展新节点。")


def main():
    import sys

    try:
        sys.stdout.reconfigure(line_buffering=True)  # 免得子进程日志抢在本脚本之前
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Skill Graph 查询与修改")
    ap.add_argument("--course", required=True, help="课程实例目录")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sub.add_parser("next")

    p = sub.add_parser("add-node")
    p.add_argument("--id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--prereqs", default="")
    p.add_argument("--homework", default="")
    p.add_argument("--points", default="", help="知识点，逗号分隔")
    p.add_argument("--weeks", default="", help="周数：2 或 2,2.5,4")
    p.add_argument("--summary", default="", help="一句话概述")

    p = sub.add_parser("set-mastery")
    p.add_argument("--id", required=True)
    p.add_argument("--value", required=True)

    p = sub.add_parser("set-prereqs")
    p.add_argument("--id", required=True)
    p.add_argument("--prereqs", default="")

    p = sub.add_parser("attach-hw")
    p.add_argument("--id", required=True)
    p.add_argument("--hw", required=True)

    p = sub.add_parser("set-points", help="设置知识点标签（逗号分隔，可写 标签|概念卡名）")
    p.add_argument("--id", required=True)
    p.add_argument("--points", required=True)

    p = sub.add_parser("set-weeks", help="设置周数（2 或 2,2.5,4）")
    p.add_argument("--id", required=True)
    p.add_argument("--weeks", required=True)

    p = sub.add_parser("set-summary", help="设置一句话概述")
    p.add_argument("--id", required=True)
    p.add_argument("--summary", required=True)

    p = sub.add_parser("set-track", help="设置课程默认节奏档（冲刺/标准/长线）")
    p.add_argument("--track", required=True)

    p = sub.add_parser("set-start", help="设置开课日期（YYYY-MM-DD 或 today）")
    p.add_argument("--date", required=True)

    a = ap.parse_args()
    course = os.path.abspath(a.course)
    fm, body, path = load(course)

    if a.cmd == "list":
        cmd_list(fm.get("nodes", []))
        return
    if a.cmd == "next":
        cmd_next(fm.get("nodes", []))
        return

    if a.cmd == "add-node":
        cmd_add_node(fm, a)
    elif a.cmd == "set-mastery":
        cmd_set_mastery(fm, a)
    elif a.cmd == "set-prereqs":
        cmd_set_prereqs(fm, a)
    elif a.cmd == "attach-hw":
        cmd_attach_hw(fm, a)
    elif a.cmd == "set-points":
        cmd_set_points(fm, a)
    elif a.cmd == "set-weeks":
        cmd_set_weeks(fm, a)
    elif a.cmd == "set-summary":
        cmd_set_summary(fm, a)
    elif a.cmd == "set-track":
        cmd_set_track(fm, a)
    elif a.cmd == "set-start":
        cmd_set_start(fm, a)

    save(fm, body, path)
    # 改图后自动重编译主页
    sync = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync.py")
    if os.path.exists(sync):
        import subprocess, sys
        subprocess.run([sys.executable, sync, "--course", course], check=False)


if __name__ == "__main__":
    main()
