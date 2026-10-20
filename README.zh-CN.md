# Alamo Skill Hub（技能仓库）

![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
![Packages: 4](https://img.shields.io/badge/packages-4-6f42c1)
![Portable agent skills](https://img.shields.io/badge/agent%20skills-portable-2ea44f)

[English](README.md) | **简体中文**

## 仓库里有什么

| 包 | 装完叫什么 | 解决什么 | 主要入口 |
| :--- | :--- | :--- | :--- |
| [`memory_hotspot_repair_kernel`](packages/memory_hotspot_repair_kernel/) | 4 个 skill | Python 内存热点：找、修、验、复核、停 | `$memory-optimizer-agent` |
| [`github_sync_workflow_kernel`](packages/github_sync_workflow_kernel/) | 1 个 skill | 找对真仓库、查鉴权、圈定提交范围、推送、验证 | `$github-sync-agent` |
| [`engineering_subagent_workflow_kernel`](packages/engineering_subagent_workflow_kernel/) | 5 个 skill | 代码探索、架构、评审、简化、测试缺口，走宿主原生子代理 | `$code-explorer` 等 |
| [`coursecoach`](packages/coursecoach/) | 1 个 skill | 把学习目标变成一门能跑起来的课 | `/coursecoach` |

四个包都是 Apache-2.0，都只依赖 Python 3.8+ 标准库加 `pyyaml`，都不需要后端。

## 四个包

### memory_hotspot_repair_kernel

给这几类问题用：Python 服务的 RSS 一路涨；批处理在 join 或模型打分阶段内存尖峰；号称分了块、实际上还是把整份数据读进内存的流水线。

四个协同的 skill：`memory-check` 检查并给热点排序，`memory-fix` 修价值最高的那个，`memory-review` 独立复核改动，`memory-optimizer-agent` 把四步编成一个带显式停止条件的有界循环。另外三个也可以单独用。

深入读：[包 README](packages/memory_hotspot_repair_kernel/README.md) · [长篇设计说明 Wiki](packages/memory_hotspot_repair_kernel/wiki/memory-skill-suite-wiki.md) · [跨宿主用法](packages/memory_hotspot_repair_kernel/PORTABLE_USAGE.md)

```bash
cd packages/memory_hotspot_repair_kernel
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

### engineering_subagent_workflow_kernel

五个开发用 skill，走宿主自己的子代理机制，不依赖外部 runner 可执行文件：`code-explorer`、`code-architect`、`code-reviewer`、`code-simplifier`、`pr-test-analyzer`。

每个 skill 自带角色说明。它不安装辅助二进制、不派生嵌套的 agent 进程、不替你选模型、也不削弱宿主的审批与沙箱策略。宿主没有原生子代理时会退回当前会话内执行，并显式报告 `fallback_in_session`，让这个差别是可见的。

深入读：[包 README](packages/engineering_subagent_workflow_kernel/README.md) · [跨宿主用法](packages/engineering_subagent_workflow_kernel/PORTABLE_USAGE.md)

```bash
cd packages/engineering_subagent_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

### coursecoach

四个里最不一样的一个——它跟代码无关。给一个主题和每天可投入的时间，它产出一门**跑得起来**的课：按先修关系排出的大纲、双击就能打开的可交互看板、讲义、能批改的作业、以掌握度为门槛的解锁链、间隔复习，以及定期扫一遍前沿进展、避免大纲过期。

大纲是唯一的真相来源。看板是编译产物，禁止手改。只有 `grade.py` 能写分数，所以每个分数都能追到一条评分标准和一个文件里的具体位置。一门课就是一个文件夹：复制即复制课程，压缩即分享。

![课程看板截图：侧栏十四阶段、0% 掌握度环、一个展开的阶段显示九个知识点标签、一行作业与批改按钮、四个动作按钮，后续阶段处于锁定状态](packages/coursecoach/docs/board.png)

![讲义在网页内弹出阅读面板：背景是暗下去的课程主页，中间浮层里是排好版的标题、有序列表、要点框和一段算例——机器上没有装 Obsidian](packages/coursecoach/docs/lesson-reader.png)

深入读：[包 README（英文）](packages/coursecoach/README.md) · [包 README（中文）](packages/coursecoach/README.zh-CN.md) · [安装与 15 分钟试玩](packages/coursecoach/INSTALL.zh-CN.md) · [跨宿主用法](packages/coursecoach/PORTABLE_USAGE.md)

```bash
cp -r packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
pip install pyyaml
```

## 你该从哪个开始

| 你想干的事 | 装这个包 | 然后说 |
| :--- | :--- | :--- |
| 让一个 Python 任务别再 OOM | `memory_hotspot_repair_kernel` | `Use $memory-optimizer-agent to optimize memory hotspots in the current codebase.` |
| 提交并推送，不靠猜 | `github_sync_workflow_kernel` | `Use $github-sync-agent to sync this repository.` |
| 把一个面很宽的任务丢给子代理 | `engineering_subagent_workflow_kernel` | `Use $code-explorer to trace how feature X is wired.` |
| 认真学一门东西 | `coursecoach` | `我想学 X，每天一小时` |

## 安装

### Codex

```bash
git clone https://github.com/Alamoooooooo/alamo_skillhub.git
cd alamo_skillhub/packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py
```

`sync_to_codex_home.py` 会把 skill 复制到 `$CODEX_HOME/skills`；`CODEX_HOME` 没设时用 `~/.codex/skills`。加 `--dry-run` 可预览。三个 kernel 包各自带一份这个脚本，装哪个就进哪个目录跑。

### WorkBuddy / CodeBuddy / Claude Code / 任何读 `SKILL.md` 的宿主

```bash
git clone https://github.com/Alamoooooooo/alamo_skillhub.git
cp -r alamo_skillhub/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
```

可安装单元永远是那个装着 `SKILL.md` 的目录——`coursecoach/coursecoach/`、`memory-optimizer-agent/`、`github-sync-agent/` 等等。`coursecoach` 需要 `pip install pyyaml`；`export.py --format docx` 另外需要 `python-docx`。

既不支持 skill 安装、也不认 `$name` 这类 token 的宿主，直接读对应包的 `PORTABLE_USAGE.md`，里面写了怎么把手册喂进去、怎么手工跑脚本。

## 目录结构

```text
alamo_skillhub/
├── README.md                          英文首页（本文件的中文对应版是下一行）
├── README.zh-CN.md                    简体中文
├── AGENTS.md                          在这个仓库里干活时 agent 该遵守的规范
├── llms.txt                           给 AI 爬虫/检索用的机器可读摘要
├── TODO_codex_plugin_marketplace.md   把内存套件打成 Codex 插件的计划（未做）
├── LICENSE                            Apache-2.0
├── packages/                          ← 产品面
│   ├── memory_hotspot_repair_kernel/
│   │   ├── memory-optimizer-agent/    编排入口（主要入口）
│   │   ├── memory-check/  memory-fix/  memory-review/
│   │   ├── references/  scripts/  wiki/
│   │   └── README.md  PORTABLE_USAGE.md  metadata.json
│   ├── github_sync_workflow_kernel/
│   │   ├── github-sync-agent/
│   │   ├── scripts/  wiki/
│   │   └── README.md  PORTABLE_USAGE.md  metadata.json
│   ├── engineering_subagent_workflow_kernel/
│   │   ├── code-explorer/  code-architect/  code-reviewer/
│   │   ├── code-simplifier/  pr-test-analyzer/
│   │   ├── scripts/
│   │   └── README.md  PORTABLE_USAGE.md  metadata.json
│   └── coursecoach/
│       ├── coursecoach/               skill 本体（SKILL.md、references、scripts、examples）
│       ├── docs/                      board.png、lesson-reader.png
│       └── README.md  README.zh-CN.md  PORTABLE_USAGE.md  INSTALL.zh-CN.md  metadata.json
└── examples/                          ← 可选，安装时完全不需要
    └── memory_hotspot_repair_kernel/
        └── partitioned_batch_pipeline/    一个具体仓库的适配：overlay + 运行配置
```

`packages/` 是产品。`examples/` 演示的是「通用内存包怎样适配到一个具体仓库」；你要自己写 overlay 时它有用，不写就完全无关。

## 其他文件

| 文件 | 是什么 |
| :--- | :--- |
| `AGENTS.md` | 给**在这个仓库里干活**的 AI agent 的规范：怎么区分包和示例、怎么更新文档与安装路径。不属于任何产品。 |
| `llms.txt` | 四个包的扁平摘要，给 AI 爬虫和检索用。内容和这份 README 一致，只是按机器读取优化过。 |
| `TODO_codex_plugin_marketplace.md` | 把内存套件打成 Codex 插件的计划，尚未实施。留作参考，仓库里没有任何东西依赖它。 |
| `metadata.json`（每个包各一份） | 机器可读的包描述：入口、关键词、支持宿主、脚本清单。 |

## 许可

Apache-2.0，见 [LICENSE](LICENSE)。
