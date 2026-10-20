#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync.py —— 把课程 frontmatter 编译成课程主页。

产物：
  1) <course>/课程主页.html  —— 自包含看板（折叠大纲 / 知识点标签 / 锚点跳转 / 节奏切换）
  2) <course>/课程进度.md    —— Obsidian 原生可读的进度页（含看板跳转链接）

数据全部来自 syllabus.md 与 homework/*.md 的 frontmatter；HTML 内联数据，双击可用。

用法: python sync.py --course <course-dir>
"""
import os
import re
import json
import argparse
import datetime
from urllib.parse import quote

import yaml

UNLOCK_PASS = 0.6
GRADE_MASTERY = {"优秀": 0.9, "良好": 0.75, "及格": 0.6, "不及格": 0.0}

# 知识点标签名 -> 概念卡文件名（名字不完全一致时用）
ALIAS = {
    "MLA": "MLA 多头潜在注意力",
    "MoE": "MoE 混合专家",
    "Scaling Laws": "Scaling Law",
    "SSM 与 Mamba": "SSM 与 Mamba",
    "MCP": "MCP 协议",
    "A2A": "A2A 协议",
    "τ-bench": "τ-bench 与 agent 评估",
    "PPO": "PPO",
    "DPO": "DPO",
    "GRPO": "GRPO",
    "RLHF": "RLHF",
    "RLVR": "RLVR",
    "RAG": "RAG",
    "Harness": "Harness",
    "Tokenizer": "Tokenizer",
    "量化（INT8/FP8）": "LoRA 与量化",
}

PACE_LABEL = {"sprint": "冲刺", "standard": "标准", "long": "长线"}


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def load_fm(path):
    return split_fm(open(path, encoding="utf-8").read())[0]


def detect_vault(course):
    """从课程目录向上找含 .obsidian 的目录，即 Obsidian vault 根。"""
    d = course
    for _ in range(10):
        if os.path.isdir(os.path.join(d, ".obsidian")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def stage_notes(vault):
    """vault/10-阶段 下的 Stage N 笔记名映射（N -> 文件名不含扩展）。"""
    out = {}
    d = os.path.join(vault, "10-阶段") if vault else None
    if d and os.path.isdir(d):
        for fn in os.listdir(d):
            m = re.match(r"Stage (\d+) .*\.md$", fn)
            if m:
                out[int(m.group(1))] = fn[:-3]
    return out


def concept_notes(vault):
    d = os.path.join(vault, "20-概念") if vault else None
    if not d or not os.path.isdir(d):
        return {}
    return {fn[:-3]: fn[:-3] for fn in os.listdir(d) if fn.endswith(".md")}


def node_stage_no(nid):
    m = re.match(r"stage(\d+)", str(nid or ""))
    return int(m.group(1)) if m else None


def norm_weeks(w):
    """weeks 允许写成数字或 {sprint,standard,long}。"""
    if isinstance(w, dict):
        return {k: float(w.get(k) or 0) for k in PACE_LABEL}
    if isinstance(w, (int, float)):
        return {"sprint": float(w), "standard": float(w), "long": float(w)}
    if isinstance(w, (list, tuple)) and w:
        vals = [float(x) for x in list(w)[:3]]
        while len(vals) < 3:
            vals.append(vals[-1])
        return dict(zip(PACE_LABEL, vals))
    return {k: 0.0 for k in PACE_LABEL}


def scan_lessons(course):
    """讲义目录：lessons/<node-id>.md = 整章讲义；lessons/<node-id>--<知识点>.md = 单点讲解。"""
    d = os.path.join(course, "lessons")
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".md") and not f.startswith("_"):
            out[f[:-3]] = os.path.join(d, f)
    return out


TRACK_MAP = {
    "sprint": "冲刺", "冲刺": "冲刺",
    "standard": "标准", "标准": "标准",
    "long": "长线", "长线": "长线",
}


def norm_track(v):
    """track 允许写 sprint/standard/long 或 冲刺/标准/长线；统一成中文供模板判断。"""
    return TRACK_MAP.get(str(v or "").strip().lower(), "冲刺")


def collect(course):
    syllabus = os.path.join(course, "syllabus.md")
    hw_dir = os.path.join(course, "homework")
    fm = load_fm(syllabus) if os.path.exists(syllabus) else {}
    nodes = fm.get("nodes", []) or []
    mastery_map = {n["id"]: (n.get("mastery") or 0) for n in nodes}

    vault = detect_vault(course)
    concepts = concept_notes(vault)

    # 知识点标签 -> 概念卡 的别名映射：内置一套默认，课程目录可用 aliases.yaml 覆盖/追加
    alias = dict(ALIAS)
    alias_path = os.path.join(course, "aliases.yaml")
    if os.path.exists(alias_path):
        try:
            extra = yaml.safe_load(open(alias_path, encoding="utf-8").read()) or {}
            if isinstance(extra, dict):
                alias.update({str(k): str(v) for k, v in extra.items()})
        except Exception as e:
            print(f"[warn] aliases.yaml 解析失败，已忽略: {e}")

    for n in nodes:
        w = norm_weeks(n.get("weeks"))
        n["weeks"] = w
        pts = []
        for p in n.get("points") or []:
            if isinstance(p, dict):
                pts.append({"t": p.get("t") or p.get("name"), "note": p.get("note")})
            else:
                note = p if p in concepts else alias.get(p)
                note = note if note in concepts else None
                pts.append({"t": str(p), "note": ("20-概念/" + note) if note else None})
        n["points"] = pts

    lessons = scan_lessons(course)
    for n in nodes:
        n["lesson"] = note_url(lessons[n["id"]], vault) if n["id"] in lessons else None
        for p in n["points"]:
            key = n["id"] + "--" + (p.get("t") or "")
            p["lesson"] = note_url(lessons[key], vault) if key in lessons else None

    homeworks = []
    if os.path.isdir(hw_dir):
        for fn in sorted(os.listdir(hw_dir)):
            if fn.startswith("hw-") and fn.endswith(".md"):
                h = load_fm(os.path.join(hw_dir, fn))
                abspath = os.path.abspath(os.path.join(hw_dir, fn))
                homeworks.append(
                    {
                        "id": h.get("id") or fn[:-3],
                        "title": h.get("title"),
                        "topic": h.get("topic"),
                        "stage": h.get("stage"),
                        "status": h.get("status", "pending"),
                        "score": h.get("score"),
                        "grade": h.get("grade"),
                        "rubric": len(h.get("rubric") or []),
                        "attempts": h.get("attempts", 0),
                        "graded_at": str(h.get("graded_at")) if h.get("graded_at") else None,
                        "review_due": str(h.get("review_due")) if h.get("review_due") else None,
                        "review_count": int(h.get("review_count") or 0),
                        "fileurl": file_url(abspath),
                        "filepath": abspath,
                        "notename": fn[:-3],
                    }
                )

    for n in nodes:
        prereqs = n.get("prereqs", []) or []
        n["unlocked"] = (
            all(mastery_map.get(p, 0) >= UNLOCK_PASS for p in prereqs) if prereqs else True
        )
        n["mastered"] = (n.get("mastery") or 0) >= UNLOCK_PASS

    graded = [h for h in homeworks if h["status"] == "graded"]
    started = [n for n in nodes if (n.get("mastery") or 0) > 0]
    today = datetime.date.today()
    due = [
        h
        for h in homeworks
        if h.get("review_due") and h["status"] == "graded"
        and h["review_due"][:10] <= today.isoformat()
    ]
    stats = {
        "hw_total": len(homeworks),
        "hw_graded": len(graded),
        "avg_mastery": round(sum(n["mastery"] for n in started) / len(started), 3) if started else 0.0,
        "nodes_total": len(nodes),
        "nodes_done": len([n for n in nodes if n["mastered"]]),
        "nodes_open": len([n for n in nodes if n["unlocked"] and not n["mastered"]]),
        "due": len(due),
    }
    return {
        "course": fm.get("title") or os.path.basename(course),
        "track": norm_track(fm.get("track")),
        "start": str(fm.get("start") or ""),
        "dir": _posix_abs(course),
        "vault": os.path.basename(vault) if vault else None,
        "nodes": nodes,
        "homeworks": homeworks,
        "stats": stats,
    }


def esc(t):
    return str(t if t is not None else "").replace("|", "\\|")


def _posix_abs(path):
    """绝对路径转 POSIX 形式，去掉 Windows 盘符前的多余斜杠差异。"""
    return os.path.abspath(path).replace("\\", "/")


def file_url(path):
    """标准 file URI（百分号编码），Windows / macOS / Linux 通用。"""
    p = _posix_abs(path)
    return ("file:///" + quote(p, safe="/:")) if os.name == "nt" else ("file://" + quote(p, safe="/:"))


def note_url(path, vault):
    """讲义/笔记链接：课程在 Obsidian 库里 → obsidian://（点开是排版好的笔记）；
    否则退回 file://（浏览器打开是 Markdown 源码，能用但不好看）。
    两种情况都比"打不开"强，所以任何异常都不抛，只降级。"""
    if vault:
        try:
            rel = os.path.relpath(os.path.abspath(path), vault).replace("\\", "/")
        except ValueError:            # Windows 跨盘符
            rel = None
        if rel and not rel.startswith(".."):
            return ("obsidian://open?vault=" + quote(os.path.basename(vault), safe="")
                    + "&file=" + quote(rel, safe="/"))
    return file_url(path)


def md_file_url(path):
    """给 Markdown 用：不做百分号编码（中文与空格交给 <> 包住），Obsidian/系统更好识别。"""
    p = _posix_abs(path)
    return ("file:///" + p) if os.name == "nt" else ("file://" + p)


def render_md(data, course):
    """生成 Obsidian 原生可读的进度页（Markdown + 双链 + 看板跳转）。"""
    vault = detect_vault(course)
    notes = stage_notes(vault)
    title_of = {n["id"]: n.get("title", n["id"]) for n in data["nodes"]}
    today = datetime.date.today()
    s = data["stats"]
    now = datetime.datetime.now()
    html_path = os.path.join(course, "课程主页.html")
    html_url = md_file_url(html_path)

    L = [
        "---",
        "title: 课程进度",
        "tags:",
        "- 课程/进度",
        f"updated: {now.strftime('%Y-%m-%dT%H:%M')}",
        "---",
        "",
        "# 课程进度",
        "",
        "> [!tip] 可视化看板",
        f"> [🖥 在浏览器打开课程主页](<{html_url}>) —— 可折叠大纲 / 知识点标签 / 点击跳转",
        f"> 若点击无反应，手动打开：`{html_path}`（文件管理器里右键 → 打开方式 → 浏览器）",
        "",
        f"> [!info] 自动生成，请勿手改",
        f"> 由 `sync.py` 从 `syllabus.md` 与 `homework/*.md` 的 frontmatter 编译。改数据源头再重跑同步。",
        "",
        "## 总览",
        "",
        "| 路线节点 | 作业已批改 | 平均掌握度 | 待复习 |",
        "|:--|:--|:--|:--|",
        f"| {s['nodes_done']} / {s['nodes_total']} 已达标 | {s['hw_graded']} / {s['hw_total']} "
        f"| {round(s['avg_mastery'] * 100)}% | {s['due']} |",
        "",
        "## 看板快捷跳转",
        "",
    ]
    links = [f"- [总览](<{html_url}#top>)"]
    for n in data["nodes"]:
        no = node_stage_no(n["id"])
        label = f"{no} {esc(n.get('title', n['id']))}" if no is not None else esc(n.get("title", n["id"]))
        links.append(f"- [{label}](<{html_url}#{n['id']}>)")
    L.append("\n".join(links))

    L += [
        "",
        "## 路线",
        "",
        "| 节点 | 掌握度 | 状态 | 先修 | 作业 |",
        "|:--|:--|:--|:--|:--|",
    ]

    hw_by_stage = {}
    for h in data["homeworks"]:
        hw_by_stage.setdefault(h["stage"], []).append(h)

    for n in data["nodes"]:
        nid = n["id"]
        no = node_stage_no(nid)
        name = esc(n.get("title", nid))
        if no is not None and no in notes:
            name = f"[[{notes[no]}\\|{name}]]"
        m = n.get("mastery")
        mstr = f"{round(m * 100)}%" if m else "—"
        if not n.get("unlocked", True):
            st = "🔒 未解锁"
        elif m and m >= UNLOCK_PASS:
            st = "✅ 已达标"
        else:
            st = "🔓 已解锁"
        pre = "、".join(esc(title_of.get(p, p)) for p in (n.get("prereqs") or [])) or "—"
        hws = hw_by_stage.get(nid, [])
        if hws:
            parts = []
            for h in hws:
                tag = f"{h['grade']} {h['score']}" if h.get("grade") else "待作答"
                parts.append(f"[[{h['notename']}\\|{esc(h['title'])}]] · {tag}")
            hwcell = "<br>".join(parts)
        else:
            hwcell = "—"
        L.append(f"| {name} | {mstr} | {st} | {pre} | {hwcell} |")

    L += [
        "",
        "## 作业清单",
        "",
        "| 作业 | 所属节点 | 状态 | 分数 | 次数 | 下次复习 |",
        "|:--|:--|:--|:--|:--|:--|",
    ]
    if data["homeworks"]:
        for h in data["homeworks"]:
            st = {"graded": "已批改", "submitted": "已提交"}.get(h["status"], "待作答")
            sc = f"{h['grade']} {h['score']}" if h.get("grade") else "—"
            due = (h.get("review_due") or "—")[:10]
            L.append(
                f"| [[{h['notename']}\\|{esc(h['title'])}]] | {esc(title_of.get(h['stage'], h['stage']))} "
                f"| {st} | {sc} | {h.get('attempts', 0)} | {due} |"
            )
    else:
        L.append("| — | — | — | — | — | — |")

    due_list = [
        h
        for h in data["homeworks"]
        if h.get("review_due") and h["status"] == "graded"
        and str(h["review_due"])[:10] <= today.isoformat()
    ]
    L += ["", "## 待复习", ""]
    if due_list:
        for h in due_list:
            L.append(
                f"- [ ] [[{h['notename']}\\|{esc(h['title'])}]] 到期 {str(h['review_due'])[:10]}"
                f"（已复习 {h.get('review_count', 0)} 次）"
            )
    else:
        L.append("暂无到期复习。")

    L += [
        "",
        "## 图例",
        "",
        "- **状态**：🔒 未解锁（先修掌握度 < 0.6）｜🔓 已解锁｜✅ 已达标（掌握度 ≥ 0.6）",
        "- **掌握度折算**：优秀 0.9 · 良好 0.75 · 及格 0.6 · 不及格 0",
        "- **怎么作答**：点开作业笔记 → 在「我的作答」区写 → 回来对我说「批改 <作业 id>」",
        "",
        f"_最后同步：{now.strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]
    return "\n".join(L)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root{
    --bg:#f5f6fa; --card:#fff; --ink:#111827; --ink2:#374151; --muted:#6b7280;
    --line:#e6e8ef; --line2:#eef0f6; --accent:#4f46e5; --accent-soft:#eef2ff; --tag-ink:#4338ca;
    --ok:#16a34a; --ok-soft:#e8f7ee; --warn:#d97706; --warn-soft:#fef4e6;
    --bad:#dc2626; --bad-soft:#fdecec; --lock:#9ca3af; --lock-soft:#f3f4f6;
    --blue:#2563eb; --radius:14px; --shadow:0 1px 2px rgba(16,24,40,.04),0 8px 24px -12px rgba(16,24,40,.12);
  }
  @media (prefers-color-scheme: dark){
    :root{
      --bg:#0f1115; --card:#171a21; --ink:#e8eaef; --ink2:#c9ced9; --muted:#8b93a3;
      --line:#262b36; --line2:#1f242e; --accent:#8b8cf7; --accent-soft:#232746; --tag-ink:#b3b8fb;
      --ok:#4ade80; --ok-soft:#16301f; --warn:#fbbf24; --warn-soft:#33260c;
      --bad:#f87171; --bad-soft:#331a1a; --lock:#6b7280; --lock-soft:#1c212b;
      --blue:#60a5fa; --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -12px rgba(0,0,0,.6);
    }
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth;scroll-padding-top:16px}
  body{margin:0;background:var(--bg);color:var(--ink);line-height:1.65;
       font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
       -webkit-font-smoothing:antialiased}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  code{background:var(--accent-soft);color:var(--ink2);padding:1px 5px;border-radius:5px;font-size:12px}

  .layout{display:grid;grid-template-columns:264px minmax(0,1fr);gap:0;align-items:start}
  /* ---------- 侧栏 ---------- */
  .side{position:sticky;top:0;height:100vh;overflow:auto;padding:24px 18px;
        border-right:1px solid var(--line);background:var(--card)}
  .brand{font-size:14px;font-weight:700;letter-spacing:.02em}
  .brand small{display:block;font-weight:400;color:var(--muted);font-size:11.5px;margin-top:2px}
  .ringbox{display:flex;align-items:center;gap:12px;margin:18px 0 14px}
  .ring{width:64px;height:64px;flex:0 0 64px;position:relative}
  .ring svg{transform:rotate(-90deg)}
  .ring .pct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
             font-size:14px;font-weight:700}
  .ringtxt{font-size:12px;color:var(--muted);line-height:1.5}
  .ringtxt b{display:block;color:var(--ink);font-size:12.5px}
  .toc{list-style:none;margin:0;padding:0;border-top:1px solid var(--line2)}
  .toc li{margin:0}
  .toc a{display:flex;gap:8px;align-items:flex-start;padding:7px 8px;border-radius:8px;
         font-size:12.5px;color:var(--ink2);line-height:1.4;transition:background .12s}
  .toc a:hover{background:var(--accent-soft);text-decoration:none}
  .toc a.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
  .toc .n{color:var(--muted);font-variant-numeric:tabular-nums;font-size:11px;padding-top:1px;min-width:15px}
  .toc .dot{width:7px;height:7px;border-radius:50%;margin-left:auto;margin-top:5px;flex:0 0 7px;background:var(--line)}
  .toc .dot.ok{background:var(--ok)} .toc .dot.cur{background:var(--accent)} .toc .dot.lock{background:var(--lock)}
  .side-foot{margin-top:14px;padding-top:12px;border-top:1px solid var(--line2);
             font-size:11px;color:var(--muted);line-height:1.6}

  /* ---------- 主区 ---------- */
  main{padding:28px 32px 72px;max-width:1000px}
  .hero h1{margin:0;font-size:26px;letter-spacing:-.01em}
  .hero .sub{margin:6px 0 0;color:var(--muted);font-size:13px}
  .row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
  .hero .row{margin-top:16px}
  .chip{border:1px solid var(--line);background:var(--card);color:var(--ink2);border-radius:999px;
        padding:5px 12px;font-size:12.5px;cursor:pointer;transition:.13s;user-select:none}
  .chip:hover{border-color:var(--accent);color:var(--accent)}
  .chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
  .chip.ghost{background:transparent}
  .sep{width:1px;height:20px;background:var(--line);margin:0 4px}
  .search{flex:1;min-width:180px;display:flex;align-items:center;gap:6px;background:var(--card);
          border:1px solid var(--line);border-radius:10px;padding:7px 11px}
  .search input{border:0;outline:0;background:transparent;color:var(--ink);font-size:13px;width:100%}
  .search kbd{font-size:10px;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 4px}

  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin:20px 0 6px}
  .stat{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
        padding:14px 16px;box-shadow:var(--shadow)}
  .stat b{display:block;font-size:23px;line-height:1.2;letter-spacing:-.02em}
  .stat b small{font-size:12px;font-weight:500;color:var(--muted)}
  .stat span{color:var(--muted);font-size:12px}

  .timeline{margin-top:18px;position:relative}
  .stage{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
         margin-bottom:10px;box-shadow:var(--shadow);overflow:hidden;transition:border-color .15s,box-shadow .15s}
  .stage:hover{border-color:#d6d9e6}
  .stage.locked{background:linear-gradient(0deg,var(--lock-soft),var(--lock-soft)) , var(--card);opacity:.86}
  .stage.flash{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
  .shead{display:flex;align-items:center;gap:12px;width:100%;padding:14px 16px;border:0;
         background:transparent;color:inherit;cursor:pointer;text-align:left;font:inherit;transition:background .12s}
  .shead:hover{background:var(--accent-soft)}
  .idx{font-size:11px;font-variant-numeric:tabular-nums;color:var(--muted);font-weight:700;
       min-width:22px;letter-spacing:.04em}
  .stitle{font-size:15px;font-weight:650;flex:1;min-width:0}
  .stitle em{font-style:normal;font-weight:400;color:var(--muted);font-size:12px;margin-left:7px}
  .meta{display:flex;align-items:center;gap:10px;flex:0 0 auto}
  .pill{font-size:11px;padding:2px 9px;border-radius:999px;white-space:nowrap;font-weight:600}
  .pill.ok{color:var(--ok);background:var(--ok-soft)}
  .pill.cur{color:var(--accent);background:var(--accent-soft)}
  .pill.lock{color:var(--lock);background:var(--lock-soft)}
  .pill.wk{color:var(--muted);background:transparent;border:1px solid var(--line);font-weight:500}
  .mb{width:56px;height:5px;border-radius:999px;background:var(--line2);overflow:hidden;flex:0 0 56px}
  .mb i{display:block;height:100%;background:var(--accent);border-radius:999px}
  .mb.full i{background:var(--ok)}
  .chev{color:var(--muted);transition:transform .2s,color .15s;font-size:13px;opacity:.55}
  .shead:hover .chev{opacity:1;color:var(--accent)}
  .stage.open .chev{transform:rotate(90deg);opacity:.9}

  .sbody{display:none;padding:0 16px 16px 50px;border-top:1px solid var(--line2)}
  .stage.open .sbody{display:block;animation:fade .18s ease-out}
  @keyframes fade{from{opacity:0;transform:translateY(-3px)}to{opacity:1;transform:none}}
  .sum{margin:12px 0 12px;color:var(--ink2);font-size:13px}
  .kw{font-size:11px;color:var(--muted);letter-spacing:.08em;margin:0 0 7px;font-weight:600}
  .tags{display:flex;flex-wrap:wrap;gap:6px}
  .tag{font-size:12px;padding:3px 10px;border-radius:7px;background:var(--accent-soft);
       color:var(--tag-ink);border:1px solid transparent;cursor:default;transition:.12s;font-weight:500}
  .tag.link{cursor:pointer}
  .tag.link:hover{border-color:var(--accent);transform:translateY(-1px);box-shadow:0 2px 8px -4px var(--accent)}
  .tag.link::after{content:"↗";font-size:9px;opacity:.6;margin-left:4px}
  .tag.dim{opacity:.35}
  .tag.hit{background:var(--warn-soft);color:var(--warn)}
  .tag.picked{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 0 0 2px var(--accent-soft)}
  .tag.haslesson::before{content:"📄";font-size:9px;margin-right:4px;opacity:.8}
  .hwlist{margin-top:14px;border-top:1px dashed var(--line);padding-top:12px}
  .hw{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:6px 0}
  .hw .t{font-weight:600;font-size:13px}
  .hw .sub{font-size:11.5px;color:var(--muted)}
  .g{font-size:11px;padding:2px 9px;border-radius:999px;font-weight:700;letter-spacing:.01em}
  .g.优秀{background:var(--ok-soft);color:var(--ok)} .g.良好{background:var(--accent-soft);color:var(--blue)}
  .g.及格{background:var(--warn-soft);color:var(--warn)} .g.不及格{background:var(--bad-soft);color:var(--bad)}
  .g.pending{background:var(--lock-soft);color:var(--muted)}
  .linkbtn{font-size:12px;padding:3px 10px;border:1px solid var(--line);border-radius:8px;
           color:var(--ink2);white-space:nowrap}
  .linkbtn:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
  .due{color:var(--bad);font-size:11.5px;font-weight:600}
  .empty{color:var(--muted);font-size:12.5px;margin-top:12px}
  .nores{color:var(--muted);font-size:13px;padding:28px;text-align:center;
         border:1px dashed var(--line);border-radius:var(--radius);display:none}
  footer{margin-top:26px;font-size:11.5px;color:var(--muted);line-height:1.8;
         border-top:1px solid var(--line);padding-top:14px}
  .legend{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}

  /* ---------- 动作按钮 ---------- */
  .act{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:4px 10px;border-radius:8px;
       border:1px solid var(--line);background:var(--card);color:var(--ink2);cursor:pointer;font-family:inherit;
       transition:.13s;white-space:nowrap;line-height:1.5}
  .act:hover{border-color:var(--accent);color:var(--accent);transform:translateY(-1px)}
  .act:active{transform:none}
  .act.on{background:var(--accent);border-color:var(--accent);color:#fff}
  .act.mini{padding:2px 7px;font-size:11px;border-radius:6px;gap:3px}
  .actrow{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px;padding-top:12px;border-top:1px dashed var(--line)}
  .actrow .hint{font-size:11.5px;color:var(--muted);margin-left:auto;align-self:center}

  /* ---------- 知识点浮动菜单 ---------- */
  .pop{position:fixed;z-index:80;background:var(--card);border:1px solid var(--line);border-radius:11px;
       box-shadow:0 14px 36px -14px rgba(16,24,40,.4);padding:5px;display:none;min-width:196px}
  .pop.show{display:block;animation:fade .12s ease-out}
  .pop .ttl{font-size:11px;color:var(--muted);padding:6px 10px 4px;letter-spacing:.04em;
            max-width:230px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .pop button{display:flex;gap:8px;align-items:center;width:100%;text-align:left;border:0;background:transparent;
              color:var(--ink2);font:inherit;font-size:12.5px;padding:7px 10px;border-radius:7px;cursor:pointer}
  .pop button:hover{background:var(--accent-soft);color:var(--accent)}
  .pop .hr{height:1px;background:var(--line2);margin:4px 6px}

  /* ---------- 动作篮 ---------- */
  /* 动作篮：整体固定右下角；只有中间的列表滚动，标题条与底部按钮永不移动 */
  .dock{position:fixed;right:20px;bottom:20px;z-index:70;width:min(380px,calc(100vw - 32px));
        display:none;flex-direction:column;max-height:calc(100vh - 40px)}
  .dock.show{display:flex}
  .dock .bar{flex:0 0 auto;display:flex;align-items:center;gap:8px;background:var(--accent);color:#fff;
             border-radius:999px;padding:9px 12px 9px 15px;
             box-shadow:0 10px 30px -10px rgba(79,70,229,.7);cursor:pointer;
             font-size:13px;font-weight:600;user-select:none}
  .dock .bar .n{background:rgba(255,255,255,.26);border-radius:999px;padding:1px 8px;font-size:12px}
  .dock .bar .arw{margin-left:auto;transition:transform .18s}
  .dock.open .bar .arw{transform:rotate(180deg)}
  .dock .panel{display:none;margin-top:8px;background:var(--card);border:1px solid var(--line);
               border-radius:14px;box-shadow:var(--shadow);padding:12px;
               flex-direction:column;min-height:0;max-height:min(62vh,calc(100vh - 110px));overflow:hidden}
  .dock.open .panel{display:flex}
  /* 列表单独滚动：按钮区固定，不必滚到面板最底部 */
  .dock .list{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;
              margin:0 -2px;padding:0 2px;scrollbar-width:thin}
  .dock .list::-webkit-scrollbar{width:7px}
  .dock .list::-webkit-scrollbar-thumb{background:var(--line);border-radius:99px}
  .dock .item{display:flex;gap:8px;align-items:flex-start;padding:6px 2px;border-bottom:1px dashed var(--line2);
              font-size:12.5px;color:var(--ink2);line-height:1.5}
  .dock .item:last-of-type{border-bottom:0}
  .dock .item .k{font-size:10.5px;font-weight:700;padding:1px 6px;border-radius:5px;flex:0 0 auto;
                 background:var(--accent-soft);color:var(--tag-ink)}
  .dock .item .t{flex:1;min-width:0;word-break:break-word}
  .dock .item .x{border:0;background:transparent;color:var(--muted);cursor:pointer;font-size:13px;padding:0 3px;line-height:1}
  .dock .item .x:hover{color:var(--bad)}
  .dock .foot{flex:0 0 auto;display:flex;gap:6px;flex-wrap:wrap;margin-top:10px;padding-top:10px;border-top:1px solid var(--line2)}
  .dock .foot .act.primary{background:var(--accent);border-color:var(--accent);color:#fff}
  .dock .foot .act.primary:hover{color:#fff;filter:brightness(1.06)}
  .dock .bulk{flex:0 0 auto;display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
  .dock .cmd{flex:0 0 auto;width:100%;height:96px;margin-top:8px;display:none;
             font-family:ui-monospace,Consolas,"Courier New",monospace;
             font-size:11px;line-height:1.55;border:1px solid var(--line);border-radius:9px;padding:8px;
             background:var(--bg);color:var(--ink2);resize:vertical}
  .dock .cmd.show{display:block}
  .dock .tip{flex:0 0 auto;font-size:11px;color:var(--muted);margin-top:8px;line-height:1.6}

  @media (max-width:900px){
    .layout{grid-template-columns:1fr}
    .side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:16px}
    .toc{display:none}
    main{padding:20px 16px 56px}
    .sbody{padding-left:16px}
    .mb{display:none}
  }
  @media print{
    .side,.chev,.search,.row.ctrl,.dock,.pop,.actrow{display:none!important}
    .layout{grid-template-columns:1fr}
    .sbody{display:block!important;padding-left:0}
    .stage{break-inside:avoid;box-shadow:none}
    body{background:#fff}
  }
</style>
</head>
<body>
<div id="top"></div>
<div class="layout">
  <aside class="side">
    <div class="brand" id="brand"></div>
    <div class="ringbox">
      <div class="ring">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="27" fill="none" stroke="var(--line)" stroke-width="6"/>
          <circle id="ringArc" cx="32" cy="32" r="27" fill="none" stroke="var(--accent)"
                  stroke-width="6" stroke-linecap="round" stroke-dasharray="169.6" stroke-dashoffset="169.6"/>
        </svg>
        <div class="pct" id="ringPct">0%</div>
      </div>
      <div class="ringtxt"><b>课时进度</b><span id="ringSub">—</span></div>
    </div>
    <ul class="toc" id="toc"></ul>
    <div class="side-foot">
      作业写在 <code>homework/hw-*.md</code> 的「我的作答」区<br>
      点页内按钮进「动作篮」→ 复制指令 → 发给我执行
    </div>
  </aside>

  <main>
    <header class="hero">
      <h1 id="h1"></h1>
      <p class="sub" id="sub"></p>
      <div class="row ctrl">
        <span class="chip ghost" style="cursor:default;border-style:dashed">节奏</span>
        <button class="chip" data-pace="sprint">冲刺</button>
        <button class="chip" data-pace="standard">标准</button>
        <button class="chip" data-pace="long">长线</button>
      </div>
      <div class="row ctrl">
        <span class="chip ghost" style="cursor:default;border-style:dashed">筛选</span>
        <button class="chip on" data-filter="all">全部</button>
        <button class="chip" data-filter="open">进行中</button>
        <button class="chip" data-filter="done">已达标</button>
        <button class="chip" data-filter="lock">未解锁</button>
        <span class="sep"></span>
        <button class="chip" id="expandAll">全部展开</button>
        <button class="chip" id="collapseAll">全部收起</button>
      </div>
      <div class="row ctrl">
        <label class="search">
          <span style="color:var(--muted)">🔍</span>
          <input id="q" placeholder="搜索章节或知识点…（按 / 聚焦）">
          <kbd>/</kbd>
        </label>
      </div>
    </header>

    <section class="stats" id="stats"></section>
    <section class="timeline" id="timeline"></section>
    <div class="nores" id="nores">没有匹配的章节 / 知识点</div>

    <footer>
      <div class="legend">
        <span>✅ 已达标（掌握度 ≥ 60%）</span>
        <span>🔓 已解锁</span>
        <span>🔒 未解锁（先修未达标）</span>
      </div>
      本页由 <code>sync.py</code> 从 <code>syllabus.md</code> 与作业 frontmatter 编译，数据内联、双击可用、无需联网。<br>
      大纲与知识点在 <code>syllabus.md</code> 维护；分数与掌握度由 <code>grade.py</code> 回写。<br>
      页面按钮只负责「攒动作 + 生成指令」，真正执行交给 AI —— 纯静态页不假装能批改。
      <span id="stamp"></span>
    </footer>
  </main>
</div>

<!-- 知识点浮动菜单 -->
<div class="pop" id="pop"></div>

<!-- 动作篮：选中 → 复制指令 → 粘贴到对话里执行 -->
<div class="dock" id="dock">
  <div class="bar" id="dockBar">
    <span>动作篮</span><span class="n" id="dockN">0</span>
    <span class="arw">▲</span>
  </div>
  <div class="panel">
    <div class="bulk">
      <button class="act mini" id="bulkAllPoints" type="button">全选知识点</button>
      <button class="act mini" id="bulkUngraded" type="button">全选待批改</button>
      <button class="act mini" id="bulkOutdated" type="button">全选无作业章节</button>
    </div>
    <div class="list" id="dockList"></div>
    <div class="foot">
      <button class="act primary" id="dockCopy" type="button">复制指令</button>
      <button class="act" id="dockClear" type="button">清空</button>
    </div>
    <textarea class="cmd" id="dockCmd" readonly></textarea>
    <div class="tip" id="dockTip">勾选后点「复制指令」，把结果粘贴到对话框发给我，我来执行。</div>
  </div>
</div>

<script>
const DATA = __DATA__;
const LS = "study-coach:" + DATA.course;
/* 隐私模式 / 禁存储环境下 localStorage 会抛异常，这里降级为「不记忆 UI 状态」，绝不白屏 */
const saved = (function(){ try { return JSON.parse(localStorage.getItem(LS) || "{}") || {}; } catch(e){ return {}; } })();
const store = {
  pace: saved.pace || (DATA.track === "标准" ? "standard" : DATA.track === "长线" ? "long" : "sprint"),
  open: new Set(saved.open || []),
  acts: Array.isArray(saved.acts) ? saved.acts : [],
  filter: "all",
  q: ""
};
function saveLS(){
  try { localStorage.setItem(LS, JSON.stringify({pace: store.pace, open: [...store.open], acts: store.acts})); } catch(e){}
}
const el = (t, h) => { const e = document.createElement(t); if (h != null) e.innerHTML = h; return e; };
const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const wk = n => (n.weeks && n.weeks[store.pace]) || 0;
const totalWeeks = p => DATA.nodes.reduce((a, n) => a + ((n.weeks && n.weeks[p]) || 0), 0);
const fmtW = w => (Math.round(w * 10) / 10).toString().replace(/\.0$/, "");
const obs = (rel) => DATA.vault ? "obsidian://open?vault=" + encodeURIComponent(DATA.vault) + "&file=" + encodeURIComponent(rel) : null;
/* 讲义按协议分流：obsidian:// 交给协议处理器（当前页不跳走）；file:// 开新标签，别把看板顶掉 */
function openLesson(u){
  if (!u) return;
  if (u.startsWith("obsidian://")) window.location.href = u;
  else window.open(u, "_blank", "noopener");
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-lessonfile]");
  if (b) { e.preventDefault(); openLesson(b.dataset.lessonfile); }
});

/* ---------- 头部 ---------- */
document.getElementById("h1").textContent = DATA.course;
document.getElementById("brand").innerHTML = esc(DATA.course) + "<small>自适应学习助教 · 课程主页</small>";
document.title = DATA.course + " · 课程主页";

function startDates(){
  // 每个节点在当前节奏下的起始周
  let acc = 1; const map = {};
  DATA.nodes.forEach(n => { map[n.id] = acc; acc += wk(n); });
  return map;
}
function renderHero(){
  const start = startDates(), tot = totalWeeks(store.pace);
  const s = DATA.nodes.length;
  const doneN = DATA.nodes.filter(n => n.mastered).length;
  let endTxt = "";
  if (DATA.start && tot) {
    const d = new Date(DATA.start + "T00:00:00");
    d.setDate(d.getDate() + Math.round(tot * 7));
    endTxt = " · 预计 " + d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + " 收尾";
  }
  document.getElementById("sub").innerHTML =
    esc(s + " 个阶段 · " + fmtW(tot) + " 周 · " + ({"sprint":"冲刺","standard":"标准","long":"长线"}[store.pace]) + "档") +
    (DATA.start ? " · 起点 " + esc(DATA.start) : "") + esc(endTxt) +
    " · 已达标 " + doneN + "/" + s;
  document.querySelectorAll("[data-pace]").forEach(b => b.classList.toggle("on", b.dataset.pace === store.pace));
}

/* ---------- 统计卡 ---------- */
function renderStats(){
  const s = DATA.stats, tot = totalWeeks(store.pace) || 1;
  let got = 0;
  DATA.nodes.forEach(n => { got += wk(n) * (n.mastery || 0); });
  const pct = Math.round(got / tot * 100);
  const arc = document.getElementById("ringArc");
  arc.style.strokeDashoffset = (169.6 * (1 - pct / 100)).toFixed(1);
  arc.style.stroke = pct >= 100 ? "var(--ok)" : "var(--accent)";
  document.getElementById("ringPct").textContent = pct + "%";
  document.getElementById("ringSub").textContent = "约 " + fmtW(got) + " / " + fmtW(tot) + " 周";

  document.getElementById("stats").innerHTML = [
    ["<b>" + s.nodes_done + "<small> / " + s.nodes_total + "</small></b><span>已达标阶段</span>", ""],
    ["<b>" + Math.round((s.avg_mastery || 0) * 100) + "<small>%</small></b><span>平均掌握度（已学）</span>", ""],
    ["<b>" + s.hw_graded + "<small> / " + s.hw_total + "</small></b><span>作业已批改</span>", ""],
    ["<b style=\"color:" + (s.due ? "var(--bad)" : "inherit") + "\">" + s.due + "</b><span>待复习</span>", ""]
  ].map(([inner]) => '<div class="stat">' + inner + "</div>").join("");
}

/* ---------- 章节 ---------- */
function statusOf(n){
  if (!n.unlocked) return ["lock", "🔒 未解锁"];
  if (n.mastered) return ["ok", "✅ 已达标"];
  return ["cur", (n.mastery ? "进行中" : "🔓 可开始")];
}
function hwRows(nid){
  const list = DATA.homeworks.filter(h => h.stage === nid);
  if (!list.length) {
    return '<div class="empty">本节点暂未布置作业 —— 点下面的「给这一章出作业」。</div>';
  }
  const today = new Date().toISOString().slice(0, 10);
  return '<div class="hwlist">' + list.map(h => {
    const grade = h.grade
      ? '<span class="g ' + esc(h.grade) + '">' + esc(h.grade) + " " + esc(h.score) + "</span>"
      : '<span class="g pending">未批改</span>';
    const st = h.status === "graded" ? "已批改 · 第 " + h.attempts + " 次" : (h.status === "submitted" ? "已提交" : "待作答");
    const due = (h.review_due && h.status === "graded" && h.review_due.slice(0, 10) <= today)
      ? '<span class="due">⚠ 复习到期 ' + esc(h.review_due.slice(0, 10)) + "</span>" : "";
    const rb = h.rubric ? '<span class="sub">rubric ' + h.rubric + " 条</span>" : "";
    const btn = '<button class="act mini" type="button" data-act="grade" data-hw="' + esc(h.id) + '">' +
      (h.status === "graded" ? "✎ 重批" : "✎ 批改") + "</button>";
    return '<div class="hw">' + grade + '<span class="t">' + esc(h.title) + "</span>" +
      '<span class="sub">' + esc(st) + "</span>" + rb + due +
      '<a class="linkbtn" href="' + h.fileurl + '" target="_blank" rel="noopener">打开作业 ↗</a>' + btn + '</div>';
  }).join("") + "</div>";
}
function tagsHtml(n){
  const q = store.q.trim().toLowerCase();
  return '<div class="kw">知识点</div><div class="tags">' + n.points.map((p, pi) => {
    const hit = q && p.t.toLowerCase().includes(q);
    const cls = "tag" + (p.note ? " link" : "") + (p.lesson ? " haslesson" : "") + (hit ? " hit" : "");
    const attrs = (p.note ? ' data-note="' + esc(p.note) + '"' : "") +
                  (p.lesson ? ' data-lesson="' + esc(p.lesson) + '"' : "") +
                  ' data-term="' + esc(p.t) + '" data-nid="' + esc(n.id) + '" data-pt="' + pi + '"';
    return '<span class="' + cls + '"' + attrs + ' title="点击：生成讲解 / 出题 / 筛选相关章节">' + esc(p.t) + "</span>";
  }).join("") + "</div>";
}
function actRow(n){
  return '<div class="actrow">' +
    (n.lesson ? '<button class="act on" type="button" data-lessonfile="' + esc(n.lesson) + '">📄 打开本章讲义</button>' : "") +
    '<button class="act" type="button" data-act="lesson" data-nid="' + esc(n.id) + '">' +
      (n.lesson ? "📖 重写这一章讲解" : "📖 补这一章讲解") + '</button>' +
    '<button class="act" type="button" data-act="hw" data-nid="' + esc(n.id) + '">📝 给这一章出作业</button>' +
    '<button class="act" type="button" data-act="research" data-nid="' + esc(n.id) + '">🔗 补资料</button>' +
    '<button class="act" type="button" data-act="selall" data-nid="' + esc(n.id) + '">☑ 本章全部知识点</button>' +
    '<span class="hint">点按加入动作篮，可多选</span></div>';
}
function renderNodes(){
  const tl = document.getElementById("timeline");
  const start = startDates();
  let shown = 0;
  tl.innerHTML = "";
  DATA.nodes.forEach((n, i) => {
    const [cls, label] = statusOf(n);
    const m = n.mastery || 0;
    const w = wk(n);
    const wkTxt = w ? ("第 " + fmtW(start[n.id]) + " 周起 · " + fmtW(w) + " 周") : "持续";
    const stageNo = (n.id.match(/stage(\d+)/) || [])[1];
    const art = el("article", "");
    art.className = "stage" + (n.unlocked ? "" : " locked") + (store.open.has(n.id) ? " open" : "");
    art.id = n.id;
    art.dataset.state = cls;
    art.dataset.search = (n.title + " " + (n.summary || "") + " " + n.points.map(p => p.t).join(" ")).toLowerCase();

    const head = el("button", "");
    head.className = "shead";
    head.innerHTML =
      '<span class="idx">' + String(i + 1).padStart(2, "0") + "</span>" +
      '<span class="stitle">' + esc(n.title) + (stageNo ? "<em>Stage " + stageNo + "</em>" : "") + "</span>" +
      '<span class="meta">' +
        '<span class="mb' + (m >= 0.6 ? " full" : "") + '"><i style="width:' + Math.round(m * 100) + '%"></i></span>' +
        '<span class="pill ' + cls + '">' + label + "</span>" +
        '<span class="pill wk">' + wkTxt + "</span>" +
        '<span class="chev">❯</span>' +
      "</span>";
    head.addEventListener("click", () => {
      if (art.classList.contains("open")) { art.classList.remove("open"); store.open.delete(n.id); }
      else { art.classList.add("open"); store.open.add(n.id); }
      saveLS();
    });
    art.appendChild(head);

    const body = el("div", "");
    body.className = "sbody";
    body.innerHTML =
      (n.summary ? '<p class="sum">' + esc(n.summary) + "</p>" : "") +
      tagsHtml(n) +
      ((n.prereqs && n.prereqs.length)
        ? '<p class="sum" style="font-size:12px;color:var(--muted);margin:10px 0 0">先修：' +
          n.prereqs.map(pid => {
            const p = DATA.nodes.find(x => x.id === pid);
            return '<a href="#' + esc(pid) + '" class="pre">' + esc(p ? p.title : pid) + "</a>";
          }).join(" → ") + "</p>"
        : "") +
      hwRows(n.id) + actRow(n);
    art.appendChild(body);
    tl.appendChild(art);
    if (matches(art)) shown++;
  });
  document.getElementById("nores").style.display = shown ? "none" : "block";
  bindTags();
  bindPre();
  bindActions();
  renderDock();
}
function matches(art){
  const q = store.q.trim().toLowerCase();
  const f = store.filter;
  if (f !== "all" && art.dataset.state !== f) return false;
  if (q && !art.dataset.search.includes(q)) return false;
  return true;
}
function applyFilters(){
  let shown = 0;
  document.querySelectorAll(".stage").forEach(art => {
    const ok = matches(art);
    art.style.display = ok ? "" : "none";
    if (ok) shown++;
    if (ok && store.q.trim()) { art.classList.add("open"); }
  });
  document.getElementById("nores").style.display = shown ? "none" : "block";
}
function bindTags(){
  document.querySelectorAll(".tag").forEach(t => {
    t.addEventListener("click", e => {
      e.stopPropagation();
      /* Ctrl / ⌘ + 点击 = 直接开概念卡，省一次点击 */
      if ((e.ctrlKey || e.metaKey) && t.dataset.note) {
        const u = obs(t.dataset.note);
        if (u) window.location.href = u;
        return;
      }
      openPop(t);
    });
  });
}
function bindPre(){
  document.querySelectorAll("a.pre").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      const id = a.getAttribute("href").slice(1);
      jump(id);
    });
  });
}

/* ---------- 动作：选中 → 拼指令 ---------- */
const KNAME = {grade: "批改", lesson: "讲解", hw: "出题", research: "补资料"};
const nodeOf = id => DATA.nodes.find(n => n.id === id);
const hwOf = id => DATA.homeworks.find(h => h.id === id);
const actKey = a => a.k + "|" + (a.hw || a.nid || "") + "|" + (a.term || "");
const hasAct = a => store.acts.some(x => actKey(x) === actKey(a));

function actDesc(a){
  if (a.k === "grade") { const h = hwOf(a.hw); return h ? h.title + "（" + a.hw + "）" : a.hw; }
  const n = nodeOf(a.nid), nt = n ? n.title : a.nid;
  if (a.term) return nt + " · 「" + a.term + "」";
  return nt + (a.k === "hw" ? "（整章出题）" : a.k === "research" ? "（整章资料）" : "（整章讲解）");
}
function paintActs(){
  document.querySelectorAll("[data-act]").forEach(b => {
    const k = b.dataset.act;
    if (k === "selall") {
      const n = nodeOf(b.dataset.nid);
      const all = n && n.points.length && n.points.every(p => hasAct({k: "lesson", nid: n.id, term: p.t}));
      b.classList.toggle("on", !!all);
      return;
    }
    const a = k === "grade" ? {k: "grade", hw: b.dataset.hw} : {k: k, nid: b.dataset.nid};
    b.classList.toggle("on", hasAct(a));
  });
  document.querySelectorAll(".tag[data-nid]").forEach(t => {
    const on = store.acts.some(x => x.nid === t.dataset.nid && x.term === t.dataset.term);
    t.classList.toggle("picked", on);
  });
}
const DEF_TIP = "勾选后点「复制指令」，把结果粘贴到对话框发给我，我来执行。";
/* 动作一改，上一次生成的指令就作废：清掉文本、收回复选框、恢复提示语 */
function resetCmd(){
  const ta = document.getElementById("dockCmd");
  if (ta) { ta.value = ""; ta.classList.remove("show"); }
  const tip = document.getElementById("dockTip");
  if (tip) tip.textContent = DEF_TIP;
}
function commit(){
  resetCmd(); saveLS(); renderDock(); paintActs();
}
function toggleAct(a){
  const k = actKey(a);
  store.acts = hasAct(a) ? store.acts.filter(x => actKey(x) !== k) : store.acts.concat([a]);
  commit();
}
function addMany(list){
  let n = 0;
  list.forEach(a => { if (!hasAct(a)) { store.acts.push(a); n++; } });
  if (n) commit();
  return n;
}
function bindActions(){
  document.querySelectorAll("[data-act]").forEach(b => {
    if (b.dataset.bound) return;
    b.dataset.bound = "1";
    b.addEventListener("click", e => {
      e.stopPropagation();
      const k = b.dataset.act, nid = b.dataset.nid;
      if (k === "selall") {
        const n = nodeOf(nid);
        if (!n) return;
        const all = n.points.length && n.points.every(p => hasAct({k: "lesson", nid: nid, term: p.t}));
        if (all) {
          store.acts = store.acts.filter(x => !(x.nid === nid && x.term));
          commit();
        } else addMany(n.points.map(p => ({k: "lesson", nid: nid, term: p.t})));
        return;
      }
      if (k === "grade") toggleAct({k: "grade", hw: b.dataset.hw});
      else toggleAct({k: k, nid: nid});
    });
  });
}

/* ---------- 知识点浮动菜单 ---------- */
const pop = document.getElementById("pop");
let popTag = null;
function openPop(t){
  popTag = t;
  const note = t.dataset.note, term = t.dataset.term;
  pop.innerHTML =
    '<div class="ttl">' + esc(term) + "</div>" +
    (t.dataset.lesson ? '<button type="button" data-p="lessonfile">📄 打开已生成的讲义</button>' : "") +
    '<button type="button" data-p="lesson">📖 生成讲解</button>' +
    '<button type="button" data-p="hw">📝 出题</button>' +
    '<button type="button" data-p="research">🔗 补资料</button>' +
    '<div class="hr"></div>' +
    (note ? '<button type="button" data-p="note">↗ 打开概念卡</button>' : "") +
    '<button type="button" data-p="filter">🔎 筛选相关章节</button>';
  pop.classList.add("show");
  const r = t.getBoundingClientRect();
  const pw = pop.offsetWidth, ph = pop.offsetHeight;
  let left = Math.min(r.left, window.innerWidth - pw - 12);
  let top = r.bottom + 6;
  if (top + ph > window.innerHeight - 12) top = Math.max(12, r.top - ph - 6);
  pop.style.left = Math.max(12, left) + "px";
  pop.style.top = top + "px";
}
function closePop(){ pop.classList.remove("show"); popTag = null; }
pop.addEventListener("click", e => {
  const b = e.target.closest("[data-p]");
  if (!b || !popTag) return;
  const p = b.dataset.p, nid = popTag.dataset.nid, term = popTag.dataset.term;
  if (p === "note") {
    const u = obs(popTag.dataset.note);
    if (u) window.location.href = u;
  } else if (p === "lessonfile") {
    openLesson(popTag.dataset.lesson);
  } else if (p === "filter") {
    store.q = term; document.getElementById("q").value = term; applyFilters();
  } else {
    toggleAct({k: p, nid: nid, term: term});
  }
  closePop();
});
document.addEventListener("click", e => { if (!pop.contains(e.target)) closePop(); });
window.addEventListener("scroll", () => { if (pop.classList.contains("show")) closePop(); }, {passive: true});
window.addEventListener("resize", () => closePop());

/* ---------- 动作篮 ---------- */
let dockPrev = -1;
function renderDock(){
  const dock = document.getElementById("dock");
  const n = store.acts.length;
  dock.classList.toggle("show", n > 0);
  if (n === 0) {
    dock.classList.remove("open");
  } else if (dockPrev <= 0) {
    // 从空到有（含清空后再选）：自动展开，让「复制指令」立刻可见
    dock.classList.add("open");
  }
  dockPrev = n;
  document.getElementById("dockN").textContent = n;
  const list = document.getElementById("dockList");
  list.innerHTML = store.acts.length ? store.acts.map((a, i) =>
    '<div class="item"><span class="k">' + KNAME[a.k] + '</span><span class="t">' + esc(actDesc(a)) +
    '</span><button class="x" type="button" data-i="' + i + '" title="移除">×</button></div>').join("")
    : '<div class="item" style="color:var(--muted)">还没选动作。点章节里的按钮，或点知识点标签。</div>';
}
function buildCommand(){
  const L = ["/study-coach 执行动作", "课程：" + DATA.course];
  if (DATA.dir) L.push("目录：" + DATA.dir);
  const order = ["grade", "lesson", "hw", "research"];
  const head = {grade: "批改作业", lesson: "生成/补充讲解", hw: "出作业", research: "补资料"};
  L.push("共 " + store.acts.length + " 项，按类型分组：");
  let i = 0;
  order.forEach(k => {
    const grp = store.acts.filter(a => a.k === k);
    if (!grp.length) return;
    L.push("");
    L.push("【" + head[k] + "】" + grp.length + " 项");
    grp.forEach(a => {
      i++;
      let s;
      if (k === "grade") s = a.hw;
      else if (a.term) s = a.nid + " · 知识点「" + a.term + "」";
      else s = a.nid + "（整章）";
      L.push(i + ") " + s);
    });
  });
  return L.join("\n");
}
function cmdTip(){
  const n = store.acts.length;
  return n > 25
    ? "共 " + n + " 项，量较大：建议先复制让 AI 分批做，或只留最需要的几项。"
    : "已复制，粘贴到对话框发给我即可。";
}
function copyCmd(){
  const ta = document.getElementById("dockCmd");
  const tip = document.getElementById("dockTip");
  if (!store.acts.length) {
    ta.value = ""; ta.classList.remove("show");
    tip.textContent = "动作篮是空的，先点章节按钮或知识点标签选几项。";
    return;
  }
  const txt = buildCommand();
  ta.value = txt; ta.classList.add("show");
  // 生成的框始终可见：面板变高时把列表压一压，不把按钮挤出视口
  try { ta.scrollIntoView({block: "nearest"}); } catch (e) {}
  const done = () => { tip.textContent = cmdTip(); };
  const fallback = () => {
    try {
      ta.removeAttribute("readonly"); ta.focus(); ta.select();
      const ok = document.execCommand("copy");
      ta.setAttribute("readonly", "readonly");
      tip.textContent = ok ? cmdTip() : "自动复制被拦，请手动全选上面文本复制。";
    } catch (e) { tip.textContent = "自动复制被拦，请手动全选上面文本复制。"; }
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(txt).then(done, fallback);
  } else fallback();
}

/* ---------- 目录 ---------- */
function renderToc(){
  const toc = document.getElementById("toc");
  toc.innerHTML = "";
  DATA.nodes.forEach((n, i) => {
    const [cls] = statusOf(n);
    const li = el("li", "");
    li.innerHTML = '<a href="#' + n.id + '"><span class="n">' + String(i + 1).padStart(2, "0") +
      "</span><span>" + esc(n.title) + '</span><span class="dot ' + (cls === "lock" ? "lock" : cls === "cur" ? "cur" : "ok") + '"></span></a>';
    li.querySelector("a").addEventListener("click", e => { e.preventDefault(); jump(n.id); });
    toc.appendChild(li);
  });
}

/* ---------- 跳转 ---------- */
function jump(id){
  const art = document.getElementById(id);
  if (!art) return;
  art.style.display = "";
  art.classList.add("open"); store.open.add(id); saveLS();
  art.classList.add("flash");
  try { art.scrollIntoView({behavior: "smooth", block: "start"}); } catch (e) {}
  setTimeout(() => art.classList.remove("flash"), 1400);
  try { history.replaceState(null, "", "#" + id); } catch (e) {}
}

/* ---------- 交互绑定 ---------- */
document.getElementById("dockBar").addEventListener("click", () => {
  document.getElementById("dock").classList.toggle("open");
});
document.getElementById("dockList").addEventListener("click", e => {
  const x = e.target.closest(".x");
  if (!x) return;
  store.acts.splice(+x.dataset.i, 1);
  commit();
});
document.getElementById("dockCopy").addEventListener("click", copyCmd);
document.getElementById("dockClear").addEventListener("click", () => {
  store.acts = [];
  commit();                       // 内部会收起面板、清掉旧指令与提示、隐藏动作篮
});
function bulkSay(n){
  const tip = document.getElementById("dockTip");
  if (n) tip.textContent = "已加入 " + n + " 项，共 " + store.acts.length + " 项。点「复制指令」即可。";
  else if (!store.acts.length) tip.textContent = "没有符合条件的项目。";
  else tip.textContent = "这些都已在篮子里（共 " + store.acts.length + " 项），直接点「复制指令」。";
}
document.getElementById("bulkAllPoints").addEventListener("click", () => {
  const list = [];
  DATA.nodes.forEach(nd => nd.points.forEach(p => list.push({k: "lesson", nid: nd.id, term: p.t})));
  bulkSay(addMany(list));
});
document.getElementById("bulkUngraded").addEventListener("click", () => {
  bulkSay(addMany(DATA.homeworks.filter(h => h.status !== "graded").map(h => ({k: "grade", hw: h.id}))));
});
document.getElementById("bulkOutdated").addEventListener("click", () => {
  bulkSay(addMany(DATA.nodes.filter(nd => !DATA.homeworks.some(h => h.stage === nd.id)).map(nd => ({k: "hw", nid: nd.id}))));
});

document.querySelectorAll("[data-pace]").forEach(b => b.addEventListener("click", () => {
  store.pace = b.dataset.pace; saveLS(); renderHero(); renderStats(); renderNodes(); applyFilters(); setActive();
}));
document.querySelectorAll("[data-filter]").forEach(b => b.addEventListener("click", () => {
  store.filter = b.dataset.filter;
  document.querySelectorAll("[data-filter]").forEach(x => x.classList.toggle("on", x === b));
  applyFilters();
}));
document.getElementById("expandAll").addEventListener("click", () => {
  DATA.nodes.forEach(n => store.open.add(n.id));
  document.querySelectorAll(".stage").forEach(a => a.classList.add("open"));
  saveLS();
});
document.getElementById("collapseAll").addEventListener("click", () => {
  store.open.clear();
  document.querySelectorAll(".stage").forEach(a => a.classList.remove("open"));
  saveLS();
});
const q = document.getElementById("q");
q.addEventListener("input", () => { store.q = q.value; applyFilters(); renderNodes(); applyFilters(); });
document.addEventListener("keydown", e => {
  if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); }
  if (e.key === "Escape" && document.activeElement === q) { q.value = ""; store.q = ""; applyFilters(); }
});

/* ---------- 高亮当前章节 ---------- */
function setActive(){
  const links = [...document.querySelectorAll("#toc a")];
  let cur = null, best = -1e9;
  DATA.nodes.forEach(n => {
    const art = document.getElementById(n.id);
    if (!art || art.style.display === "none") return;
    const top = art.getBoundingClientRect().top;
    if (top - 80 <= 0 && top > best) { best = top; cur = n.id; }
  });
  links.forEach(a => a.classList.toggle("active", a.getAttribute("href") === "#" + cur));
}
window.addEventListener("scroll", () => { if (window.innerWidth > 900) setActive(); }, {passive: true});

/* ---------- 启动 ---------- */
renderHero(); renderStats(); renderToc(); renderNodes();
const hasHash = location.hash.length > 1;
if (!store.open.size && !hasHash) {
  const cur = DATA.nodes.find(n => n.unlocked && !n.mastered) || DATA.nodes[0];
  if (cur) { store.open.add(cur.id); saveLS(); }
  const art = cur && document.getElementById(cur.id);
  if (art) art.classList.add("open");
}
document.getElementById("stamp").innerHTML = "<br>最后同步：__STAMP__";
// 深链：课程主页.html#stage3-transformer
if (location.hash.length > 1) setTimeout(() => jump(decodeURIComponent(location.hash.slice(1))), 60);
setActive();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="frontmatter -> 课程主页")
    ap.add_argument("--course", required=True, help="课程实例目录")
    args = ap.parse_args()
    course = os.path.abspath(args.course)
    if not os.path.isdir(course):
        raise SystemExit(f"[error] 课程目录不存在: {course}")

    data = collect(course)
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    now = datetime.datetime.now()
    html = (
        TEMPLATE.replace("__DATA__", payload)
        .replace("__TITLE__", data["course"].replace("<", "&lt;"))
        .replace("__STAMP__", now.strftime("%Y-%m-%d %H:%M"))
    )
    out = os.path.join(course, "课程主页.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[ok] 已生成主页: {out}")

    mdp = os.path.join(course, "课程进度.md")
    with open(mdp, "w", encoding="utf-8") as f:
        f.write(render_md(data, course))
    print(f"[ok] 已生成进度页: {mdp}")
    s = data["stats"]
    print(
        f"     节点 {s['nodes_total']}（达标 {s['nodes_done']}）| 作业 {s['hw_total']}"
        f"（已批改 {s['hw_graded']}）| 待复习 {s['due']}"
    )


if __name__ == "__main__":
    main()
