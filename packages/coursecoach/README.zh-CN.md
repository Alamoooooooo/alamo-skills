# CourseCoach（课程教练）

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](../../LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](PORTABLE_USAGE.md#dependencies)
[![Backend: none](https://img.shields.io/badge/backend-none-2ea44f)](#它跟让-ai-写个学习计划有什么不同)
[![Portable agent skill](https://img.shields.io/badge/agent%20skill-portable-6f42c1)](PORTABLE_USAGE.md)

[English](README.md) | **简体中文**

![课程看板截图：侧栏十四阶段、0% 掌握度环、一个展开的阶段显示九个知识点标签、一行作业与批改按钮、四个动作按钮，后续阶段处于锁定状态](docs/board.png)

`coursecoach` 是一个可安装、可迁移的 agent skill 包。它把"我想学 X"变成一门**真正跑得起来**的课：
按先修关系排出的大纲、双击就能打开的可交互看板、讲义、能批改的作业、以掌握度为门槛的解锁链、
按遗忘曲线安排的复习，以及定期把新进展并入大纲的前沿周更。

你只需要给一个主题和一个每天可投入的时长。它会先跟你确认目标，起草大纲，编译看板，写讲义，
出作业并按写好的评分标准批改，把分数写回，解锁下一节，再排好复习时间。

> **名字说明**：包名和 skill 名是同一个词 `coursecoach`——搜到的、装上的、敲的是同一个名字。
> 整包没有第二份拷贝：那个目录就是 skill 本体加一层包元数据。

## 它跟"让 AI 写个学习计划"有什么不同

大多数学习助手是一段提示词，产出一份计划。计划随后就烂掉：没人执行它、没人给它打分，
领域变了也没人通知你。这里有四条机制在真正起作用。

**一、大纲是唯一数据源。** 进度、先修、周数预算、作业挂载、掌握度和复习日期全在
`syllabus.md` 的 frontmatter 里。同一文件中的正文只给人看，解析器永远不读。不存在第二个
可能跟它打架的文件。

**二、看板是编译产物，不是文档。** `课程主页.html` 由 `sync.py` 从大纲编译出来，**不许手改**，
skill 里把这条写成了硬禁令。所以每次改完重编译都不会漂移，页面上每个数字都能追溯到某一个
YAML 字段。

**三、分数只有一个写入口。** 只有 `grade.py` 能写 `mastery`。AI 决定"该给几分"，脚本决定
"这个分写到哪、解锁哪些后继"。一次评分因此是可审计的：每个分数都有对应的评分条目、理由，
以及在文件里的物理位置。

**四、一门课就是一个文件夹。** 复制文件夹＝复制一门课，打包 zip＝分享一门课，挪个位置重跑
`sync.py`＝页面里所有路径自动更新。没有数据库，没有服务端，没有账号。

## 它产出什么

| 产物 | 谁生成 | 能不能手改 |
|:--|:--|:--|
| `syllabus.md` | `init_course.py` / `syllabus.py` | 可以，它是唯一数据源 |
| `课程主页.html` | `sync.py` | **不行**，每次同步全量重编译 |
| `课程进度.md` | `sync.py` | **不行**，是给 Obsidian 看的镜像 |
| `lessons/<节点>.md` | AI | 可以，整章或单点各一份 |
| `homework/<名字>.md` | AI | 作答可以，分数不行 |
| `resources/资料库.md` | AI | 可以，每条都带"代价"说明 |
| 两条定时任务 | `schedule.py` 出配方 + 宿主执行 | 不行，属宿主状态，按需重建 |

## 一次批改到底发生了什么

```
目标 → 澄清 → 大纲（YAML）→ sync → 看板
                              │
       讲义 ← 动作篮 ← 看板   （页面只攒动作，不假装自己是后端）
                              │
       作业 → 作答 → grade.py → 掌握度 → 解锁链
                              │
                     review.py → 1 / 3 / 7 / 16 / 35 / 75 天
```

看板是**故意做笨的**：静态 HTML、数据内联，双击 `file://` 就能开，不需要服务器。它从不假装
自己能批改、能保存、能调模型。它只把勾选的动作拼成一条可复制的指令，等 AI 粘贴回来后执行。

确定性的事（编译、解锁、排期、写 YAML）留在脚本里；判断类的事（讲什么、这题该给几分）
留给模型。这条界线一旦挪动，系统就开始出问题。

## 九个确定性脚本

全部按 `--course` 参数化，只用标准库加 `pyyaml`。

| 脚本 | 职责 |
|:--|:--|
| `init_course.py` | 按阶段规格建课，顺手编译看板 |
| `syllabus.py` | 加节点、设掌握度、改先修、改知识点、改周数、换档位、改开课日 |
| `sync.py` | 编译看板与进度镜像 |
| `grade.py` | **唯一**能写 `mastery` 的入口，同时算解锁链 |
| `review.py` | 复习队列；`mark` 推进间隔，`snooze` 只挪日期不改计数 |
| `export.py` | 导出可读教材，可加 `--format docx` |
| `reset.py` | 清空作答与分数，用于分享或重来 |
| `pack.py` | 把**一门课**打成自包含 zip |
| `schedule.py` | 生成两条定时任务的**配方**（它自己从不建任务） |

## 它不做什么

- **不保证跨模型判分一致。** 模型更强，批改更准。脚本保证的是分数可审计、位置正确，
  不是客观上正确。
- **不核实自己引用的资料。** 检索到的链接、免费额度、考试要求都会标"待核实"，
  要你自己点一遍。
- **不自带定时任务。** 自动化是宿主状态，换台机器就没有，也不该在包里塞一个假的。
  `schedule.py` 负责出配方，落地时重建；宿主根本没有定时能力时，它会把这句话说明白。
- **不处理纯审美类目标。** "我想有品味"得先翻译成可观察行为，否则没有东西可批改。

## 安装

装到 skill 目录（WorkBuddy / CodeBuddy / 任何读 `SKILL.md` 的宿主）：

```bash
git clone https://github.com/Alamoooooooo/alamo_hub.git
cp -r alamo_hub/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
pip install pyyaml
```

然后说一句"我想学 XXX，每天一小时"，或直接 `/coursecoach`。

非 Codex 类宿主见 [`PORTABLE_USAGE.md`](PORTABLE_USAGE.md)，逐步试玩见
[`INSTALL.zh-CN.md`](INSTALL.zh-CN.md)。

## 目录结构

```
packages/coursecoach/
├── README.md               英文说明
├── README.zh-CN.md         中文说明（本文件）
├── PORTABLE_USAGE.md       跨宿主用法与降级说明
├── INSTALL.zh-CN.md        安装与 15 分钟试玩
├── metadata.json           机器可读的包描述
├── docs/board.png          课程看板截图
└── coursecoach/            skill 本体（安装时用这个名字）
    ├── SKILL.md            7 个阶段、动作协议、批改口径、脚本参数
    ├── references/         8 份分册，按需加载
    ├── scripts/            9 个确定性脚本
    ├── assets/             大纲与作业空白模板
    └── examples/ai-fullstack/   一份真实课程快照（作答已清空，掌握度全 null）
```

## 从这里开始

1. [`coursecoach/SKILL.md`](coursecoach/SKILL.md) —— AI 按这份说明书干活。
2. `coursecoach/examples/ai-fullstack/课程主页.html` —— 双击它，看一门课跑一段时间后长什么样。
3. [`coursecoach/references/portability.md`](coursecoach/references/portability.md) —— 搬到别的
   agent 或操作系统。

## 许可

Apache-2.0，与仓库一致。
