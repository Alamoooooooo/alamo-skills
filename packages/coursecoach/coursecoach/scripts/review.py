#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review.py —— 按遗忘曲线管理已批改作业的复习节奏。

间隔序列（天）：1 → 3 → 7 → 16 → 35 → 75。
grade.py 批改后写入 review_due = 明天、review_count = 0。
每次 `mark` 一次复习，间隔推进到下一档。

用法:
  python review.py --course <course-dir> list            # 列出到期（含逾期）
  python review.py --course <course-dir> list --all      # 列出全部已批改
  python review.py --course <course-dir> mark <hw-id>    # 标记已复习，推进下一档
  python review.py --course <course-dir> list --json     # 机器可读（给自动化用）
"""
import os
import re
import sys
import json
import argparse
import datetime

import yaml

INTERVALS = [1, 3, 7, 16, 35, 75]


def sync_page(course, enabled=True):
    """改完 frontmatter 后重编译主页。list 不用调，mark / snooze 必须调。"""
    if not enabled:
        return
    sync = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync.py")
    if os.path.exists(sync):
        import subprocess

        subprocess.run([sys.executable, sync, "--course", course, "--if-changed"], check=False)


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        raise ValueError("找不到 frontmatter")
    return m.group(1), text[m.end():]


def load_hw(path):
    fm_raw, body = split_fm(open(path, encoding="utf-8").read())
    return yaml.safe_load(fm_raw) or {}, body


def save_hw(path, fm, body):
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    open(path, "w", encoding="utf-8").write("---\n" + new_fm + "---\n" + body)


def scan(course):
    hw_dir = os.path.join(course, "homework")
    items = []
    if not os.path.isdir(hw_dir):
        return items
    for fn in sorted(os.listdir(hw_dir)):
        if not (fn.startswith("hw-") and fn.endswith(".md")):
            continue
        path = os.path.join(hw_dir, fn)
        fm, _ = load_hw(path)
        if fm.get("status") != "graded":
            continue
        items.append(
            {
                "id": fm.get("id") or fn[:-3],
                "title": fm.get("title", fn[:-3]),
                "grade": fm.get("grade"),
                "score": fm.get("score"),
                "stage": fm.get("stage"),
                "review_due": str(fm["review_due"])[:10] if fm.get("review_due") else None,
                "review_count": int(fm.get("review_count") or 0),
                "attempts": fm.get("attempts", 0),
                "path": path,
                "fm": fm,
            }
        )
    return items


def due_items(items, today):
    return [it for it in items if it["review_due"] and it["review_due"] <= today.isoformat()]


def cmd_list(course, show_all, as_json):
    today = datetime.date.today()
    items = scan(course)
    due = items if show_all else due_items(items, today)

    if as_json:
        print(
            json.dumps(
                {
                    "today": today.isoformat(),
                    "total_graded": len(items),
                    "due_count": len(due_items(items, today)),
                    "items": [
                        {
                            "id": it["id"],
                            "title": it["title"],
                            "grade": it["grade"],
                            "score": it["score"],
                            "review_due": it["review_due"],
                            "review_count": it["review_count"],
                        }
                        for it in due
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if not items:
        print("[info] 还没有已批改的作业，暂无复习计划。")
        return 0
    if not due:
        nxt = min((it["review_due"] for it in items if it["review_due"]), default=None)
        print(f"[ok] 今天没有到期复习。最近一次：{nxt or '未安排'}")
        return 0

    if show_all:
        print(
            f"[all] {len(due)} 份已批改作业（其中 {len(due_items(items, today))} 份已到期）："
        )
    else:
        print(f"[due] {today.isoformat()} 有 {len(due)} 份到期复习：")
    print(f"{'作业 id':<24} {'标题':<22} {'等级':<6} {'到期':<12} {'已复习'}")
    print("-" * 78)
    for it in due:
        title = (it["title"] or "")[:20]
        print(
            f"{it['id']:<24} {title:<22} {str(it['grade'] or '-'):<6} "
            f"{it['review_due']:<12} {it['review_count']} 次"
        )
    print()
    print("复习方式：不开卷自测 / 讲回来给我听 / 重做错题。完成后：")
    print(f"  python review.py --course <course-dir> mark <作业id>")
    return 0


def cmd_mark(course, hw_id, do_sync=True):
    items = scan(course)
    hit = next((it for it in items if it["id"] == hw_id), None)
    if not hit:
        print(f"[error] 找不到已批改作业: {hw_id}")
        return 1

    fm = hit["fm"]
    count = int(fm.get("review_count") or 0) + 1
    gap = INTERVALS[min(count, len(INTERVALS) - 1)]
    due = datetime.date.today() + datetime.timedelta(days=gap)
    fm["review_count"] = count
    fm["last_reviewed"] = datetime.date.today().isoformat()
    fm["review_due"] = due.isoformat()

    _, body = load_hw(hit["path"])
    save_hw(hit["path"], fm, body)
    print(f"[ok] {hw_id} 复习记为第 {count} 次，下次到期 {due.isoformat()}（间隔 {gap} 天）", flush=True)
    sync_page(course, do_sync)
    return 0


def cmd_snooze(course, hw_id, days, do_sync=True):
    """推迟复习到期日：不推进复习计数，只挪日期（'这周没时间'）。"""
    items = scan(course)
    hit = next((it for it in items if it["id"] == hw_id), None)
    if not hit:
        print(f"[error] 找不到已批改作业: {hw_id}")
        return 1

    today = datetime.date.today()
    base = today
    if hit["review_due"]:
        try:
            base = max(datetime.date.fromisoformat(hit["review_due"]), today)
        except ValueError:
            base = today
    due = base + datetime.timedelta(days=days)

    fm = hit["fm"]
    fm["review_due"] = due.isoformat()
    _, body = load_hw(hit["path"])
    save_hw(hit["path"], fm, body)
    print(
        f"[ok] {hw_id} 复习推迟到 {due.isoformat()}"
        f"（原 {hit['review_due'] or '未排'}，+{days} 天，计数仍为 {fm.get('review_count') or 0}）",
        flush=True,
    )
    sync_page(course, do_sync)
    return 0


def main():
    ap = argparse.ArgumentParser(description="遗忘曲线复习管理")
    ap.add_argument("--course", required=True, help="课程实例目录")
    ap.add_argument(
        "action", choices=["list", "mark", "snooze"], help="list 列到期 / mark 标记已复习 / snooze 推迟"
    )
    ap.add_argument("hw_id", nargs="?", help="mark / snooze 时的作业 id")
    ap.add_argument("--all", action="store_true", help="list 时列出全部已批改")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--days", type=int, default=3, help="snooze 推迟天数，默认 3")
    ap.add_argument("--no-sync", action="store_true", help="改完不重编译主页（批量操作时用）")
    args = ap.parse_args()

    course = os.path.abspath(args.course)
    if not os.path.isdir(course):
        print(f"[error] 课程目录不存在: {course}")
        return 2

    if args.action == "list":
        return cmd_list(course, args.all, args.json)
    if not args.hw_id:
        print(f"[error] {args.action} 需要作业 id")
        return 2
    if args.action == "snooze":
        return cmd_snooze(course, args.hw_id, args.days, do_sync=not args.no_sync)
    return cmd_mark(course, args.hw_id, do_sync=not args.no_sync)


if __name__ == "__main__":
    sys.exit(main())
