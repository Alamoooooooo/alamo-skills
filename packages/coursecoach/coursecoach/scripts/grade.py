#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grade.py —— 按 result JSON 写回批改结果。

读 <hw> 作业 md 与 <result> 评分 JSON，安全写回：
  1) 作业 frontmatter：status/score/grade/graded_at/attempts
  2) 「## 批改反馈」区（只替换该区及其之后，绝不碰「我的作答」）
  3) <course>/syllabus.md 对应 stage 节点 mastery
最后自动调用 sync.py 重编译课程主页。

用法:
  python grade.py --course <course-dir> --hw <hw路径或文件名> --result <评分json>

评分 JSON:
{
  "score": 85,
  "grade": "良好",                 // 可选，缺省按 score 自动定级
  "items": [{"label":"...","status":"present|partial|absent","note":"..."}],
  "summary": "...",
  "next_hint": "..."
}
"""
import os
import re
import sys
import json
import argparse
import datetime
import subprocess

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
GRADE_BY_SCORE = [("优秀", 90), ("良好", 80), ("及格", 60), ("不及格", 0)]
GRADE_MASTERY = {"优秀": 0.9, "良好": 0.75, "及格": 0.6, "不及格": 0.0}
STATUS_ICON = {"present": "✓ 满足", "partial": "~ 部分", "absent": "✗ 缺失"}


def auto_grade(score):
    for g, thr in GRADE_BY_SCORE:
        if score >= thr:
            return g
    return "不及格"


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise ValueError("找不到 frontmatter（文件需以 --- 包裹的 YAML 开头）")
    return m.group(1), text[m.end():]


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


def write_hw(hw_path, fm, feedback_md):
    text = open(hw_path, encoding="utf-8").read()
    _, body = split_fm(text)
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    lines = body.split("\n")
    try:
        idx = next(i for i, l in enumerate(lines) if l.strip().startswith("## 批改反馈"))
    except StopIteration:
        lines.append("## 批改反馈")
        lines.append("")
        idx = len(lines) - 2
    head = lines[: idx + 1]
    out = "---\n" + new_fm + "---\n" + "\n".join(head) + "\n" + feedback_md + "\n"
    open(hw_path, "w", encoding="utf-8").write(out)


def update_syllabus(syllabus, stage_id, mastery):
    if not os.path.exists(syllabus):
        print(f"[warn] 无 syllabus: {syllabus}，跳过 mastery")
        return
    text = open(syllabus, encoding="utf-8").read()
    fm_raw, body = split_fm(text)
    fm = yaml.safe_load(fm_raw)
    hit = False
    for n in fm.get("nodes", []):
        if n.get("id") == stage_id:
            n["mastery"] = mastery
            hit = True
            break
    if not hit:
        print(f"[warn] syllabus 无节点 {stage_id}，跳过 mastery")
        return
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    open(syllabus, "w", encoding="utf-8").write("---\n" + new_fm + "---\n" + body)
    print(f"[ok] syllabus 节点 {stage_id} mastery -> {mastery}")


def build_feedback(result, grade, now):
    lines = [f"> 等级：**{grade}** ｜ 分数：**{result['score']}** ｜ 批改时间：{now} ｜ 第 {result.get('_attempts', 1)} 次批改", ""]
    items = result.get("items", [])
    if items:
        lines += ["### 逐条判定（rubric）", "", "| 要求 | 判定 | 说明 |", "|---|---|---|"]
        for it in items:
            lines.append(f"| {it.get('label','')} | {STATUS_ICON.get(it.get('status','absent'), it.get('status',''))} | {it.get('note','')} |")
        lines.append("")
    if result.get("summary"):
        lines += ["### 总体反馈", "", result["summary"], ""]
    if result.get("next_hint"):
        lines += ["### 改进建议", "", result["next_hint"], ""]
    return "\n".join(lines)


def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)  # 免得子进程日志抢在本脚本之前
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="批改回写工具")
    ap.add_argument("--course", required=True, help="课程实例目录")
    ap.add_argument("--hw", required=True, help="作业 md 路径或 homework/ 下文件名")
    ap.add_argument("--result", required=True, help="评分结果 JSON")
    ap.add_argument("--no-sync", action="store_true", help="批改后不重编译主页（批量批改时用）")
    args = ap.parse_args()

    course = os.path.abspath(args.course)
    hw_path = resolve_hw(course, args.hw)
    syllabus = os.path.join(course, "syllabus.md")

    with open(args.result, encoding="utf-8") as f:
        result = json.load(f)
    score = int(result["score"])
    grade = result.get("grade") or auto_grade(score)
    if grade not in GRADE_MASTERY:
        raise SystemExit(f"[error] grade 非法: {grade}")

    fm = yaml.safe_load(split_fm(open(hw_path, encoding="utf-8").read())[0])
    fm["status"] = "graded"
    fm["score"] = score
    fm["grade"] = grade
    fm["graded_at"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    fm["attempts"] = int(fm.get("attempts", 0)) + 1
    fm["review_count"] = 0
    fm["review_due"] = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    fm.pop("last_reviewed", None)
    result["_attempts"] = fm["attempts"]
    stage_id = fm.get("stage")

    write_hw(hw_path, fm, build_feedback(result, grade, fm["graded_at"]))
    print(f"[ok] 已写回 {os.path.basename(hw_path)}：{grade} / {score} / 第{fm['attempts']}次")

    if stage_id:
        update_syllabus(syllabus, stage_id, GRADE_MASTERY[grade])

    sync = os.path.join(HERE, "sync.py")
    if not args.no_sync and os.path.exists(sync):
        print("[run] 重编译课程主页 ...")
        subprocess.run([sys.executable, sync, "--course", course, "--if-changed"], check=False)
    elif args.no_sync:
        print("[skip] 已跳过重编译（--no-sync）")


if __name__ == "__main__":
    main()
