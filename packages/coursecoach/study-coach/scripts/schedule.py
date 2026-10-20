#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排期配方：把「该建哪几条自动化」变成确定性输出。

自动化是**宿主状态**，不是文件——它不进 zip，换个机器就没有了。
所以这里不负责"建"，只负责两件确定性的事：
  1. 给出该建的自动化的完整规格（名字 / rrule / prompt / cwds）
  2. 检查这门课现在值不值得建（没有作业就没有复习可提醒）

真正的创建由 agent 调宿主的 automation_update 完成——这是宿主能力，脚本碰不到。

用法：
    python schedule.py --course <dir>            # 人读的说明
    python schedule.py --course <dir> --json     # agent 读，直接照建
    python schedule.py --course <dir> --kind review|weekly
    python schedule.py --course <dir> --check    # 只做前置条件自检

幂等约定：名字里带课程标题，agent 先 list 再按名字比对，已存在就不重复建。
"""
import argparse
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
REF = os.path.join(SKILL, "references", "weekly-frontier.md")
PY = sys.executable


def posix(p):
    return os.path.abspath(p).replace("\\", "/")


def load(course):
    p = os.path.join(course, "syllabus.md")
    if not os.path.isfile(p):
        raise SystemExit(f"[error] 不是课程目录（缺 syllabus.md）: {course}")
    text = open(p, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        raise SystemExit("[error] syllabus.md 缺 frontmatter")
    fm = yaml.safe_load(m.group(1)) or {}
    title = str(fm.get("title") or os.path.basename(os.path.abspath(course))).strip()
    return fm, title


def hw_state(course):
    """作业与批改现状，用来判断"该不该建提醒"。"""
    d = os.path.join(course, "homework")
    files = []
    if os.path.isdir(d):
        files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    graded = 0
    pending = 0
    for f in files:
        t = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
        m = re.search(r"^---\s*\n(.*?)\n---", t, re.S)
        meta = {}
        if m:
            try:
                meta = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                meta = {}
        if meta.get("review_due") or str(meta.get("status", "")).lower() in ("graded", "已批改"):
            graded += 1
        else:
            pending += 1
    return {"homework": len(files), "graded": graded, "pending": pending}


def specs(course, title):
    c = posix(course)
    review = {
        "kind": "review",
        "name": f"「{title}」· 每日复习提醒",
        "scheduleType": "recurring",
        "rrule": "FREQ=DAILY;BYHOUR=20;BYMINUTE=0",
        "cwds": c,
        "prompt": (
            f"运行 {PY} {HERE}/review.py --course {c} list --json，"
            "若有到期或逾期作业，用一句话列出「课程 · 作业 · 逾期天数」，"
            "并提示「复习完说一声，我再推进下次复习时间」。"
            "没有到期就只回一句「今日无到期复习」。"
            "不要自动 mark——复习是否通过由用户说了算。"
        ),
    }
    weekly = {
        "kind": "weekly",
        "name": f"「{title}」· 前沿周更",
        "scheduleType": "recurring",
        "rrule": "FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0",
        "cwds": c,
        "prompt": (
            f"每周做一次本课程的前沿周更。先读 {posix(REF)}"
            "（读不到就按下面的硬规矩执行）。\n\n"
            f"【课程目录】{c}\n"
            "该目录含 syllabus.md（唯一数据源）/ resources/资料库.md / lessons/；"
            "课程主页.html 是 sync.py 的编译产物，不是手改对象。\n\n"
            f"【脚本】{PY} {HERE}\n\n"
            "【步骤】\n"
            "1. 用 freshness=d7 检索 8 个维度：架构 / 开放权重与发布 / 训练与后训练 / "
            "强化学习 / Agent 与编排 / 协议标准 / 评测与独立复测 / 工程与效率。"
            "只收会改变学习重点的（旧知识过时、值得新增专题、该调整顺序）；"
            "融资、产品营销、刷榜一律丢弃。一周 0–3 条真增量即为正常。\n"
            f"2. 先读 syllabus.md 现状，再增量写回："
            f"新知识点用 syllabus.py set-points（整表覆盖，必须带全原有全部知识点）；"
            f"新节点用 add-node（先修须已存在）；周数用 set-weeks（顺序 冲刺,标准,长线）；"
            f"资料追加到 resources/资料库.md（链接 + 用途 + 代价 + 日期 + ✅/⚠️）。\n"
            f"3. 跑 {PY} {HERE}/sync.py --course {c}，确认末尾零 [warn]。\n"
            "4. 汇报 ≤5 行。没有增量就说「本周无实质增量」并列出扫过的维度，不要硬塞。\n\n"
            "【硬禁令】不许手改 课程主页.html；不许手写 mastery（只有 grade.py 能回写）；"
            "不许改作业的 review_due；不许只改 syllabus 正文数字而不改 frontmatter。"
        ),
    }
    return {"review": review, "weekly": weekly}


def main():
    ap = argparse.ArgumentParser(description="排期配方：该建哪几条自动化")
    ap.add_argument("--course", required=True)
    ap.add_argument("--kind", choices=["review", "weekly"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true", help="只做前置条件自检，不输出配方")
    a = ap.parse_args()

    course = os.path.abspath(a.course)
    fm, title = load(course)
    st = hw_state(course)

    if a.check:
        print(f"[课程] {title}")
        print(f"       作业 {st['homework']} 份（已批改 {st['graded']} · 未批改 {st['pending']}）")
        verdict = []
        if st["graded"] == 0:
            verdict.append("还没有已批改作业 → 复习提醒目前只会回「今日无到期复习」，可以先不建")
        else:
            verdict.append("已有批改记录 → 适合建复习提醒")
        if not os.path.isdir(os.path.join(course, "resources")):
            verdict.append("没有 resources/ → 周更无处写资料，先建目录或跳过周更")
        else:
            verdict.append("有 resources/ → 可建周更")
        for v in verdict:
            print(f"  · {v}")
        sys.exit(0)

    all_specs = specs(course, title)
    if a.kind:
        out = [all_specs[a.kind]]
    else:
        out = [all_specs["review"], all_specs["weekly"]]

    if a.json:
        print(json.dumps({
            "course": posix(course),
            "title": title,
            "skill": posix(SKILL),
            "automations": out,
        }, ensure_ascii=False, indent=2))
        return

    print(f"[课程] {title}  ({posix(course)})")
    print(f"       作业 {st['homework']} 份（已批改 {st['graded']}）")
    print()
    print("先调宿主的自动化列表，按 name 比对；已存在就跳过，别重复建。")
    print()
    for s in out:
        print(f"── {s['name']}")
        print(f"   类型   {s['scheduleType']}")
        print(f"   时间   {s['rrule']}")
        print(f"   工作目录 {s['cwds']}")
        print(f"   prompt:")
        for line in s["prompt"].splitlines():
            print(f"     {line}")
        print()
    print("建完再跑一次本脚本核对；宿主不支持自动化时，降级做法见 references/portability.md。")


if __name__ == "__main__":
    main()
