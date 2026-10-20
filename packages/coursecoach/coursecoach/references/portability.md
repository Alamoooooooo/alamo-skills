# 跨 agent / 跨平台迁移

本 skill 的目标是：**换一个模型、换一个 agent、换一台机器，复制目录就能跑**。
不是「WorkBuddy 专用插件」。下面是迁移时的全部事实。

## 1. 它是什么格式

标准 **Agent Skills** 结构：一个目录，入口是 `SKILL.md`，开头 YAML frontmatter 只要求 `name` + `description`，正文是给 AI 读的说明书。`scripts/` 是可选附件（普通 Python 脚本），`references/` 是按需加载的深文档，`assets/` 是模板，`examples/` 是可运行的真实样例。

```
coursecoach/
├── SKILL.md              # 入口：7 阶段流程 + 分工原则 + 工具等价表
├── scripts/*.py          # 7 个确定性脚本，全部 --course 参数化
├── references/*.md       # data-model / course-design / grading-rubric / parallel-research / delivery / portability
├── assets/*.md           # syllabus / homework 空模板
└── examples/ai-fullstack/ # 跑完一轮的真实课程快照（含已生成的看板）
```

## 2. 装到不同环境

| 环境 | 放到哪 | 触发方式 |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/coursecoach/`（用户级）或 `<项目>/.workbuddy/skills/` | 说「我想学 XX」或 `/coursecoach` |
| Claude Code | `~/.claude/skills/coursecoach/` 或 `<repo>/.claude/skills/` | 自动按 description 匹配；也可 `/coursecoach` |
| 其他支持 Agent Skills 的（Cursor / Windsurf / 各家 IDE agent） | 各自约定的 `skills/` 目录 | 同上 |
| 不支持 skills 的（ChatGPT / 本地模型 / 自写 loop） | 不进目录，**把 `SKILL.md` 全文注入 system prompt 或首条消息** | 用户直接说「按这个流程帮我建课」 |
| 纯命令行（无人值守） | 直接调用 `scripts/*.py`，不依赖任何 AI | `init_course.py` → `sync.py` → `grade.py` |

**不支持 skills 的环境照样能用**：`SKILL.md` 是自然语言，没有神秘语法；脚本是普通 Python，只要能执行就够了。此时 AI 拿不到 `examples/` 和 `references/`，把 `SKILL.md` 里引用的路径改成实际路径一并喂进去即可。

## 3. 依赖

| 依赖 | 必需 | 说明 |
|---|---|---|
| Python 3.8+ | ✅ | 只用标准库 + pyyaml，无第三方框架 |
| `pyyaml` | ✅ | frontmatter 读写。`pip install pyyaml` |
| `python-docx` | 可选 | 仅 `export.py --format docx` 需要 |
| Obsidian | 可选 | 只影响「概念卡可点」与阶段笔记双链；没装时讲义改为主页内弹层阅读，不影响看板主体 |
| 联网搜索 | 可选 | Phase 3 检索资源用；没网就用本地已有资料，标注「待核实」 |

**不需要**：Node、数据库、云服务、任何 API key、浏览器插件。

## 4. 跨平台已处理的差异

| 坑 | 处理方式 |
|---|---|
| `file://` URI 在 Windows / macOS / Linux 拼接不同 | `sync.py` 按 `os.name` 分支：Windows 拼 `file:///D:/…`，类 Unix 拼 `file:///home/…` |
| Windows 控制台 GBK 导致中文乱码 | 所有脚本不 `reconfigure(encoding=...)`，让 Python 自适应 stdout 编码；所有文件读写显式 `encoding="utf-8"` |
| 路径分隔符 | 全程 `os.path.join` / `os.path.abspath`，无手写反斜杠 |
| Word 中文字体 | `export.py` 按平台选字体（Windows `Microsoft YaHei` / macOS `PingFang SC` / 其他 `Noto Sans CJK SC`），并设置 `w:eastAsia` |
| 文件名含中文与空格 | 目录名就是 `课程主页.html` 这类中文名，Python 与主流文件系统均支持；Markdown 链接用 `<>` 包裹 |
| 隐私模式下 `localStorage` 抛异常 | 看板已 try/catch，降级为「不记忆 UI 状态」，不白屏 |

**没有平台锁定的东西**：没写死盘符、没调 Windows API、没依赖 shell 内建命令、没用 `wmic` / `reg` / `powershell`。

## 5. 迁移后自检（5 步，5 分钟）

```bash
# 1) 依赖自检
python -c "import yaml; print(yaml.__version__)"

# 2) 建一门最小课（3 个节点，验证写文件与编译）
python scripts/init_course.py --dir /tmp/smoke-course --title "冒烟测试" \
  --stages '[{"id":"a","title":"第一段"},{"id":"b","title":"第二段","prereqs":["a"]}]'

# 3) 看产物是否齐、有无告警
ls /tmp/smoke-course            # syllabus.md / 课程主页.html / 课程进度.md / homework / resources

# 4) 走一次批改闭环（验证 frontmatter 写回与 mastery 解锁）
#    在 homework/ 手写一份 hw-a.md（参照 assets/homework.template.md），然后：
python scripts/grade.py --course /tmp/smoke-course --hw hw-a --result result.json

# 5) 用浏览器/预览打开 课程主页.html：目录、环形进度、折叠、标签、深链都要能用
```

通不过时按现象定位：

| 现象 | 原因 |
|---|---|
| `ModuleNotFoundError: yaml` | 换了没装 pyyaml 的解释器；换解释器或 `pip install pyyaml` |
| 页面空白 / `NaN` | 节点缺 `weeks`（总周数为 0）；跑 `syllabus.py set-weeks` |
| 深链不展开 | 锚点写错（必须是 `#<node-id>`，不是标题）；或节点 id 有改动未重跑 sync |
| 概念卡点不动 | 课程不在 Obsidian vault 内，探测不到 `.obsidian`；属预期降级 |
| 讲义点开是一堆 `#` 和 `**` | 用的是旧版 `sync.py` 编译的 HTML（没有预渲染）。重跑 `sync.py` 即可，讲义会在页内弹层里正常排版 |
| Word 打不开 | 没装 `python-docx`，或用了 `--format docx` 但环境缺依赖 |

## 6. 打包给别人时

1. **脱敏**：`examples/ai-fullstack/` 若含真实作答，先跑
   `python scripts/reset.py --course examples/ai-fullstack --all`
   （清空作答/反馈、回退 mastery、自动重编译），再删掉生成物。
2. **别带课程数据**：别人的课应该在自己的 `course-dir` 里；skill 目录只留 examples。
3. **别带本机路径**：`SKILL.md` / `references/` 里不要出现具体盘符；示例里的 `file:///` 快照路径在 README 说明即可。
4. **先验证再打包**：跑一遍第 5 节自检，确认在干净目录下也能建课。
5. **定时任务带不走，也不用带**：自动化是宿主状态，不在 zip 里。包里放的是"重建配方"——`scripts/schedule.py`。对方装好后进课程跑一次 `--check` 就能补齐。**别为了"看起来完整"去塞一个假的定时任务文件**，那只会在对方机器上变成静默不执行的垃圾。

## 6.5 宿主没有自动化能力时

有的环境（Claude Code、纯 CLI）没有 `automation_update` 这类原语。此时**降级，不要报错，更不要假装已经排上了**：

| 能力 | 有定时器 | 没有定时器 |
|:--|:--|:--|
| 算出今天该复习什么 | `review.py list` 定时跑 | 进入课程时跑一次，顺带说一句 |
| 主动叫醒用户 | 自动化推送 | **做不到**，只能说清"你需要自己回来看" |
| 周更 | 周一自动跑一遍 | 用户说「周更」时手动跑，流程完全一样 |

唯一诚实的话术：「这个环境没法定时叫你，但每次你进来我都会先查一遍到期的复习」。把不能做的事说清楚，比留一个不会触发的任务好。

## 7. 一句话总结

> `SKILL.md` 是脑子，`scripts/` 是手脚，课程数据在 `course-dir` 里。
> 三者解耦，所以脑子可以换宿主，手脚可以换机器，数据可以换课程。
