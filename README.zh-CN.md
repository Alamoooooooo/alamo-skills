# Alamo Skills（技能仓库）

![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
![Packages: 4](https://img.shields.io/badge/packages-4-6f42c1)
![Portable agent skills](https://img.shields.io/badge/agent%20skills-portable-2ea44f)

[English](README.md) | **简体中文**

## 仓库里有什么

| 包 | 装完叫什么 | 解决什么 | 主要入口 | 开发时间 |
| :--- | :--- | :--- | :--- | :--- |
| [`coursecoach`](packages/coursecoach/) | 1 个 skill | 把学习目标变成一门能跑起来的课 | `/coursecoach` | 2026-10-20 |
| [`engineering_subagent_workflow_kernel`](packages/engineering_subagent_workflow_kernel/) | 5 个 skill | 代码探索、架构、评审、简化、测试缺口，走宿主原生子代理 | `$code-explorer` 等 | 2026-10-20 |
| [`github_sync_workflow_kernel`](packages/github_sync_workflow_kernel/) | 1 个 skill | 找对真仓库、查鉴权、圈定提交范围、推送、验证 | `$github-sync-agent` | 2026-07-21 → 07-22 |
| [`memory_hotspot_repair_kernel`](packages/memory_hotspot_repair_kernel/) | 4 个 skill | Python 内存热点：找、修、验、复核、停 | `$memory-optimizer-agent` | 2026-07-03 → 07-22 |

四个包都是 Apache-2.0，都只依赖 Python 3.8+ 标准库加 `pyyaml`，都不需要后端。

## 四个包

### coursecoach

四个里最不一样的一个——它跟代码无关，是个学习助教。给一个主题和每天能投入多久，它产出一门**跑得起来**的课：按先修关系排出的大纲、双击就能打开的可交互看板、讲义、能批改的作业、以掌握度为门槛的解锁链、间隔复习。

它不限学科——编程、外语、乐器、会计、考证都能用。它跟「让 AI 写一份学习计划」的差别在于计划之后的事：分数、解锁状态、复习日期都写在文件里，所以课程跨会话还在，换个模型接手也能继续，打包发给别人对方双击就能用。

**六个动作**，全部说人话触发；主页上也有一一对应的按钮，点一下就把这句话拼好放进动作篮：

- **生成一门课** —— 说「我想学 XX，每天 1 小时」。它先问清目标、现有基础和每周能投入多少，给三档进度方案（冲刺 / 标准 / 长线）让你选，再联网调研、按先修关系排出十来个节点、编译出看板。产物：`syllabus.md`（唯一数据源）、`课程主页.html`、`resources/资料库.md`。
- **生成讲义** —— 主页每章底部点「📖 补这一章讲解」，或点某个知识点标签选「生成讲解」。可以整章写，也可以只写一个知识点。产物：`lessons/stage3.md` 或 `lessons/stage3--梯度下降.md`，重编译后主页上出现 📄，点开就能读（没装 Obsidian 也是排版好的）。
- **出作业** —— 说「给 stage3 出一道作业」，或点「📝 给这一章出作业」。写题目 + 3–6 条评分标准，作答区留空。产物：`homework/hw-*.md`，固定三段结构「题目要求 / 我的作答 / 批改反馈」。
- **批改作业** —— 你写完答案后说「批改 hw-stage3-xxx」。它逐条判定 present / partial / absent 并给理由（判分标准固定，不因你写得多就给高分），折算成掌握度写回文件，达标就解锁后继节点，同时把这份作业排进复习队列。
- **更新薄弱知识点** —— 说「stage3 老是在 XXX 上错」。它去看这个节点上反复 partial / absent 的是哪些知识点，判断该补资料、拆节点还是加节点，必要时再出一份只针对这个点的作业。改动只走 `syllabus.py`，不手改文件。
- **复习与导出** —— 说「今天该复习什么」，按 1 / 3 / 7 / 16 / 35 / 75 天报到期项（可以推迟，推迟不推进计数）；说「导成 Word」就得到一份完整教材。

![课程看板截图：侧栏十四阶段、0% 掌握度环、一个展开的阶段显示九个知识点标签、一行作业与批改按钮、四个动作按钮，后续阶段处于锁定状态](packages/coursecoach/docs/board.png)

![讲义在网页内弹出阅读面板：背景是暗下去的课程主页，中间浮层里是排好版的标题、有序列表、要点框和一段算例——机器上没有装 Obsidian](packages/coursecoach/docs/lesson-reader.png)

**什么都不想装，只想先点两下？** [在线 demo](https://coursecoach-demo.app.workbuddy.host/?sharecode=DGYMO3ZV3W) 是一份真实课程的编译产物（示例课程 + 5 篇讲义内联），能展开章节、点开讲义、试搜索，不用装任何东西。

**装它**（三步，约 1 分钟）：

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
pip install pyyaml
```

- 可安装单元是装着 `SKILL.md` 的那一层，也就是 `coursecoach/coursecoach/`；拷过去之后**目录名必须叫 `coursecoach`**（与 skill 同名），否则斜杠命令对不上。
- Windows 上目标是 `C:\Users\<你的用户名>\.workbuddy\skills\coursecoach\`；也可以放在项目里的 `.workbuddy/skills/`，只对该项目生效。
- Codex 走 `$CODEX_HOME/skills`；不认 skill 的宿主把 `SKILL.md` 加 `references/` 直接喂进上下文即可，脚本照跑。
- 需要 Python 3.8+，且**那个解释器能 `import yaml`**；导出 Word 另需 `pip install python-docx`。
- 装完**重开一个会话**才认得到。之后说「我想学 XX」或直接 `/coursecoach`。

装完先别上真课——[安装与 15 分钟试玩](packages/coursecoach/INSTALL.zh-CN.md) 里有一门试玩课，跑完就知道整套东西长什么样。

深入读：[包 README（英文）](packages/coursecoach/README.md) · [包 README（中文）](packages/coursecoach/README.zh-CN.md) · [安装与 15 分钟试玩](packages/coursecoach/INSTALL.zh-CN.md) · [跨宿主用法](packages/coursecoach/PORTABLE_USAGE.md)

### engineering_subagent_workflow_kernel

五个开发用 skill，走宿主自己的子代理机制，不依赖外部 runner 可执行文件：`code-explorer`、`code-architect`、`code-reviewer`、`code-simplifier`、`pr-test-analyzer`。

每个 skill 自带角色说明。它不安装辅助二进制、不派生嵌套的 agent 进程、不替你选模型、也不削弱宿主的审批与沙箱策略。宿主没有原生子代理时会退回当前会话内执行，并显式报告 `fallback_in_session`，让这个差别是可见的。

深入读：[包 README](packages/engineering_subagent_workflow_kernel/README.md) · [跨宿主用法](packages/engineering_subagent_workflow_kernel/PORTABLE_USAGE.md)

```bash
cd packages/engineering_subagent_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

### github_sync_workflow_kernel

给这一步用——几乎每个人都会错一次的那步：哪个目录才是真仓库、远端和鉴权是不是真的通、哪些改动该进这次提交、哪些是换行符噪音、以及推上去到底成没成。

`github-sync-agent` 把仓库发现、鉴权与远端检查、提交范围评审、提交、推送、推送后验证串成一条流程。那份 Wiki 记录的就是它针对的失败模式。

深入读：[包 README](packages/github_sync_workflow_kernel/README.md) · [Wiki](packages/github_sync_workflow_kernel/wiki/github-sync-workflow-wiki.md) · [跨宿主用法](packages/github_sync_workflow_kernel/PORTABLE_USAGE.md)

```bash
cd packages/github_sync_workflow_kernel
python3 scripts/sync_to_codex_home.py
```

### memory_hotspot_repair_kernel

给这几类问题用：Python 服务的 RSS 一路涨；批处理在 join 或模型打分阶段内存尖峰；号称分了块、实际上还是把整份数据读进内存的流水线。

四个协同的 skill：`memory-check` 检查并给热点排序，`memory-fix` 修价值最高的那个，`memory-review` 独立复核改动，`memory-optimizer-agent` 把四步编成一个带显式停止条件的有界循环。另外三个也可以单独用。

深入读：[包 README](packages/memory_hotspot_repair_kernel/README.md) · [长篇设计说明 Wiki](packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md) · [跨宿主用法](packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md)

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

## 你该从哪个开始

| 你想干的事 | 装这个包 | 然后说 |
| :--- | :--- | :--- |
| 认真学一门东西 | `coursecoach` | `我想学 X，每天一小时` |
| 把一个面很宽的任务丢给子代理 | `engineering_subagent_workflow_kernel` | `Use $code-explorer to trace how feature X is wired.` |
| 提交并推送，不靠猜 | `github_sync_workflow_kernel` | `Use $github-sync-agent to sync this repository.` |
| 让一个 Python 任务别再 OOM | `memory_hotspot_repair_kernel` | `Use $memory-optimizer-agent to optimize memory hotspots in the current codebase.` |

## 安装

### Codex

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
cd alamo-skills/packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

`sync_to_codex_home.py` 会把 skill 复制到 `$CODEX_HOME/skills`；`CODEX_HOME` 没设时用 `~/.codex/skills`。加 `--dry-run` 可预览。三个 kernel 包各自带一份这个脚本，装哪个就进哪个目录跑。

### WorkBuddy / CodeBuddy / Claude Code / 任何读 `SKILL.md` 的宿主

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
```

可安装单元永远是那个装着 `SKILL.md` 的目录——`coursecoach/coursecoach/`、`memory-optimizer-agent/`、`github-sync-agent/` 等等。`coursecoach` 需要 `pip install pyyaml`；`export.py --format docx` 另外需要 `python-docx`。

既不支持 skill 安装、也不认 `$name` 这类 token 的宿主，直接读对应包的 `PORTABLE_USAGE.md`，里面写了怎么把手册喂进去、怎么手工跑脚本。

## 目录结构

```text
alamo-skills/
├── README.md                          英文首页
├── README.zh-CN.md                    简体中文首页（本文件）
├── CONTRIBUTING.md                    怎么改这个仓库：自检、提交规范、审 PR
├── CONTRIBUTING.zh-CN.md              简体中文
├── AGENTS.md                          在这个仓库里干活时 agent 该遵守的规范
├── llms.txt                           给 AI 爬虫/检索用的机器可读摘要
├── LICENSE                            Apache-2.0
├── scripts/check.py                   仓库自检：双语配对、死链、元数据、脚本语法
├── .github/pull_request_template.md   PR 打开时自带的检查清单
├── packages/                          ← 产品面
│   ├── README.md                      包的约定：三层结构、必备文件、references 与 wiki 的区别
│   ├── coursecoach/
│   │   ├── coursecoach/               skill 本体（SKILL.md、references、scripts、examples）
│   │   ├── docs/                      board.png、lesson-reader.png
│   │   └── README.md  README.zh-CN.md  PORTABLE_USAGE.md  INSTALL.md  INSTALL.zh-CN.md  metadata.json
│   ├── engineering_subagent_workflow_kernel/
│   │   ├── code-explorer/  code-architect/  code-reviewer/
│   │   ├── code-simplifier/  pr-test-analyzer/
│   │   ├── scripts/
│   │   └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
│   ├── github_sync_workflow_kernel/
│   │   ├── github-sync-agent/
│   │   ├── scripts/  wiki/
│   │   └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
│   └── memory_hotspot_repair_kernel/
│       ├── memory-optimizer-agent/    编排入口（主要入口）
│       ├── memory-check/  memory-fix/  memory-review/
│       ├── references/  scripts/  wiki/
│       └── README.md  INSTALL.md  INSTALL.zh-CN.md  PORTABLE_USAGE.md  metadata.json
├── examples/                          ← 可选，安装时完全不需要
│   ├── coursecoach/
│   │   └── quick-trial/stages.json    造一门 3 节点课的最小输入
│   └── memory_hotspot_repair_kernel/
│       └── partitioned_batch_pipeline/    一个具体仓库的适配：overlay + 运行配置
└── todo/                              ← 未实施的计划，没有任何东西依赖它
    └── codex-plugin-packaging.md
```

`packages/` 是产品，`examples/` 可选，`todo/` 是没做的计划。包的内部约定——三层结构、每个包必备哪些文件、`references/` 和 `wiki/` 有什么不同、安装到底该拷哪一层——都写在 **[`packages/README.md`](packages/README.md)**。

## 其他文件

| 文件 | 是什么 |
| :--- | :--- |
| `CONTRIBUTING.md` | 改这个仓库的规范：五条硬规矩、提交信息怎么写、审 PR 看什么、动脚本之前必须怎么验证。中英双语。 |
| `scripts/check.py` | 七项自检（双语配对、死链、元数据、脚本语法等）。提 PR 前跑一遍，退出码非零，可以直接当 CI 步骤。 |
| `AGENTS.md` | 给**在这个仓库里干活**的 AI agent 的规范：怎么区分包和示例、怎么更新文档与安装路径。不属于任何产品。 |
| `llms.txt` | 四个包的扁平摘要，给 AI 爬虫和检索用。内容和这份 README 一致，只是按机器读取优化过。 |
| `todo/` | 未实施的计划，先从 `codex-plugin-packaging.md` 看起。放在这里是「想过但没承诺」，仓库里没有任何东西依赖它。 |
| `metadata.json`（每个包各一份） | 机器可读的包描述：入口、关键词、支持宿主、脚本清单。 |

## 许可

Apache-2.0，见 [LICENSE](LICENSE)。
