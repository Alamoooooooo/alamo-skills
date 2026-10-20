#!/usr/bin/env python3
"""课程包：自包含检查 + 一键打包分享。

课程实例本身就是一个自包含文件夹（syllabus + homework + resources + 三个生成页），
复制这个目录 = 复制整门课，删掉这个目录 = 删掉整门课，没有别处依赖。

用法：
    python pack.py --course <dir>              # 检查 + 打包成 zip
    python pack.py --course <dir> --check      # 只检查，不打包
    python pack.py --course <dir> --out x.zip  # 指定输出位置
    python pack.py --course <dir> --allow-answers   # 明确允许带作答记录打包

退出码：0 正常；1 检查发现需要处理的问题（仍会给出报告）。
"""
import argparse
import datetime
import os
import re
import sys
import zipfile

CORE = [
    ("syllabus.md", "Skill Graph 大纲（必需，唯一数据源）"),
    ("课程主页.html", "可交互看板（由 sync.py 生成）"),
    ("课程进度.md", "Obsidian 内可读的进度页（由 sync.py 生成）"),
]
OPTIONAL = [
    ("homework", "作业目录"),
    ("lessons", "讲义目录（AI 生成的章节 / 知识点讲解）"),
    ("resources", "资料库目录"),
    ("教材.md", "导出的教材（export.py 生成）"),
    ("教材.docx", "导出的 Word 教材（export.py --format docx 生成）"),
]
SKIP_DIRS = {".obsidian", ".git", "__pycache__", ".trash", "node_modules"}
ABS_PATH = re.compile(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|/Users/|/home/|/Volumes/)[^\s\"'`<>\])|,]+")
ANSWER_HEAD = re.compile(r"^##\s*我的作答\s*$", re.M)
FEEDBACK_HEAD = re.compile(r"^##\s*批改反馈\s*$", re.M)
PLACEHOLDER = re.compile(r"^\s*(?:<!--.*?-->\s*)?(?:[（(]\s*(?:在此作答|待作答|略|空|留空)[^）)]*[）)])?\s*$")
PLACEHOLDER_HINT = re.compile(r"批改前为空|待批改|自动写回|在此作答|待作答|尚未作答|请在此|留空")


def posix(path):
    return os.path.abspath(path).replace("\\", "/")


def walk(course):
    out = []
    for root, dirs, files in os.walk(course):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(files):
            p = os.path.join(root, f)
            out.append((os.path.relpath(p, course).replace("\\", "/"), os.path.getsize(p)))
    return out


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return ""


def section(text, head_re):
    """取出某个二级标题下的正文。"""
    m = head_re.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def meaningful(body):
    """判断一段正文里是否真有内容（排除占位符、注释、空行）。"""
    if body is None:
        return False
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = []
    for line in body.splitlines():
        s = line.strip().strip(">").strip()
        if not s:
            continue
        if re.fullmatch(r"[（(][^）)]{0,160}[）)]", s):      # 形如（在此作答）/（批改前为空）
            continue
        if re.fullmatch(r"[-_*~=·。.\s]{0,6}", s):
            continue
        lines.append(s)
    if not lines:
        return False
    joined = " ".join(lines)
    # 短且带"待批改 / 自动写回 / 留空"这类提示语 → 仍视为空区
    if len(joined) < 200 and PLACEHOLDER_HINT.search(joined):
        return False
    return True


def check(course):
    """返回 (problems, warns, info)。problems 会阻断分享。"""
    problems, warns, info = [], [], {}
    files = walk(course)
    names = {rel for rel, _ in files}

    for rel, desc in CORE:
        if rel not in names:
            problems.append(f"缺少核心文件 {rel}（{desc}）")

    has_hw = [r for r in names if r.startswith("homework/") and r.endswith(".md")]
    if not has_hw:
        warns.append("没有作业文件：课程能看不能考。用 study-coach 出作业后再分享。")

    # 作答 / 批改残留（分享前最该查的东西）
    answered, graded = [], []
    for rel in sorted(has_hw):
        t = read(os.path.join(course, rel))
        if meaningful(section(t, ANSWER_HEAD)):
            answered.append(rel)
        if meaningful(section(t, FEEDBACK_HEAD)):
            graded.append(rel)
    if answered:
        problems.append(
            "以下作业含真实作答（分享会泄露你的答案）：" + "、".join(answered) +
            "。清空用：reset.py --course <dir> --all"
        )
    if graded:
        problems.append(
            "以下作业含批改记录（含分数与评语）：" + "、".join(graded) +
            "。清空用：reset.py --course <dir> --all"
        )

    # 绝对路径：换台机器就断，但不致命
    hits = []
    for rel, _ in files:
        if rel.endswith((".md", ".html", ".json", ".yaml", ".yml")):
            t = read(os.path.join(course, rel))
            for m in ABS_PATH.finditer(t):
                hits.append((rel, m.group(0)))
    if hits:
        uniq = sorted({h[0] for h in hits})
        sample = hits[0][1]
        warns.append(
            f"{len(uniq)} 个文件里写死了本机绝对路径（如 {sample}）："
            "换机器后主页按钮里的「目录」提示会失效，重跑 sync.py 即可修正"
            f"；涉及文件：{'、'.join(uniq[:5])}{' 等' if len(uniq) > 5 else ''}"
        )

    info["files"] = len(files)
    info["bytes"] = sum(s for _, s in files)
    info["homework"] = len(has_hw)
    info["generated"] = [r for r, _ in files if r in ("课程主页.html", "课程进度.md", "教材.md")]
    return problems, warns, info


def make_readme(course, title, node_count, hw_count):
    return f"""# {title} · 课程包

这是一个 **study-coach** 课程实例，整门课就是一个文件夹：读完、考完、改完都只发生在这里，
删掉这个文件夹就等于删掉整门课，没有别的目录残留。

## 里面有什么

| 路径 | 作用 | 能不能手改 |
|:--|:--|:--|
| `syllabus.md` | Skill Graph 大纲（节点 / 先修 / 掌握度） | 可以，但建议用 `syllabus.py` |
| `homework/hw-*.md` | 作业：题目 + 我的作答 + 批改反馈 | 「我的作答」区由你写 |
| `lessons/<节点>.md` | AI 生成的章节讲义 / 知识点讲解 | 可以，跟着讲义补充笔记 |
| `resources/资料库.md` | 参考资料 | 可以 |
| `课程主页.html` | 可交互看板，双击即可打开 | 不要手改，由 `sync.py` 生成 |
| `课程进度.md` | Obsidian 内可读的进度页 | 不要手改 |
| `教材.md` / `教材.docx` | 导出的整门课教材 | 不要手改 |

大纲节点 {node_count} 个，作业 {hw_count} 份。

## 怎么继续学

课程主页右上角/章节内有一排按钮：**补讲解 / 出作业 / 批改 / 补资料**。
点按会进「动作篮」，再点「复制指令」，把复制到的文本粘回对话框 —— 交给 AI 执行。
这样纯静态页也能驱动真实的批改与出题，不需要后端。

也可以直接用命令行（需要 Python 3 + pyyaml）：

```bash
python scripts/sync.py     --course .              # 重编译主页与进度页
python scripts/syllabus.py --course . next         # 看下一步该学什么
python scripts/grade.py    --course . --hw hw-xxx --result r.json
python scripts/review.py   --course . list         # 遗忘曲线复习队列
```

> 注意：主页「复制指令」里带的课程目录，是打包时那台机器的路径。
> 换机器后先跑一次 `sync.py --course .`，路径就会更新成当前实际位置。

## 换到别的 agent / 模型

skill 正文（`SKILL.md`）是说明书，脚本是确定性工具，两者都不依赖特定平台。
把 `SKILL.md` 与 `references/` 交给对方的 agent，或直接注入 system prompt，即可复用整套流程。
细节见 skill 内的 `references/portability.md`。
"""


def main():
    ap = argparse.ArgumentParser(description="课程包：检查 + 打包")
    ap.add_argument("--course", required=True, help="课程实例目录")
    ap.add_argument("--out", help="zip 输出路径（默认放在课程目录旁边）")
    ap.add_argument("--check", action="store_true", help="只检查，不打包")
    ap.add_argument("--allow-answers", action="store_true", help="允许带作答/批改记录打包")
    ap.add_argument("--no-scripts", action="store_true", help="不把运行脚本一起打进包")
    args = ap.parse_args()

    course = os.path.abspath(args.course)
    if not os.path.isdir(course):
        raise SystemExit(f"[error] 课程目录不存在: {course}")

    problems, warns, info = check(course)
    title = os.path.basename(course)
    syl = read(os.path.join(course, "syllabus.md"))
    m = re.search(r"^title:\s*(.+)$", syl, re.M)
    if m:
        title = m.group(1).strip().strip("\"'")
    node_count = len(re.findall(r"^\s{2,}- id:", syl, re.M)) or len(re.findall(r"^- id:", syl, re.M))
    hw_count = info["homework"]

    print(f"[课程] {title}")
    print(f"[目录] {posix(course)}")
    print(f"       {info['files']} 个文件 · {info['bytes'] / 1024:.0f} KB · 节点 {node_count} · 作业 {hw_count}")
    print()
    for p in problems:
        print(f"  [!] {p}")
    for w in warns:
        print(f"  [~] {w}")
    if not problems and not warns:
        print("  [ok] 自包含检查通过：可安全分享")
    elif not problems:
        print("  [ok] 没有阻断项")

    if args.check:
        sys.exit(1 if problems else 0)

    if problems and not args.allow_answers:
        print()
        print("[中止] 检查未通过，未打包。处理完再跑，或加 --allow-answers 强行打包。")
        sys.exit(1)

    safe = re.sub(r'[\\/:*?"<>|]', "_", title)
    out = args.out or os.path.join(
        os.path.dirname(course),
        safe + "-课程包-" + datetime.date.today().strftime("%Y%m%d") + ".zip",
    )
    out = os.path.abspath(out)
    base = safe

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, _ in walk(course):
            z.write(os.path.join(course, rel), f"{base}/{rel}")
        if not args.no_scripts:
            here = os.path.dirname(os.path.abspath(__file__))
            for f in sorted(os.listdir(here)):
                if f.endswith(".py"):
                    z.write(os.path.join(here, f), f"{base}/scripts/{f}")
        z.writestr(f"{base}/README.md", make_readme(course, title, node_count, hw_count))

    print()
    print(f"[ok] 已打包：{out}（{os.path.getsize(out) / 1024:.0f} KB）")
    print(f"     解压后即可独立使用；删除整门课只需删掉「{base}」这一个文件夹。")


if __name__ == "__main__":
    main()
