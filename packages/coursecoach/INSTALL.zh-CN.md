# CourseCoach · 安装与试玩

[English](INSTALL.md) | **简体中文**

把 AI 从"讲一遍就完事"变成**会出题、会批改、会排复习**的助教：给一个主题，它先跟你确认目标与
节奏，然后生成带先修链的大纲、可双击打开的课程看板、讲义、作业与评分标准；批改后写回掌握度，
再按遗忘曲线安排复习。

全部是本地文件。**不需要联网、不需要数据库、不需要注册。**

> **名字说明**：包名和 skill 名是同一个词 `coursecoach`——搜到的、装上的、敲的是同一个名字。
> 目录 `coursecoach/` 就是 skill 本体，整包没有第二份拷贝。

---

## 一、装上（1 分钟）

**从仓库取：**

```bash
git clone https://github.com/Alamoooooooo/alamo-skills.git
cp -r alamo-skills/packages/coursecoach/coursecoach ~/.workbuddy/skills/coursecoach
pip install pyyaml
```

Windows 上目标路径是 `C:\Users\<你的用户名>\.workbuddy\skills\coursecoach\`。
也可以放到项目内的 `<项目>/.workbuddy/skills/`，只对该项目生效。

放好后重开一个会话，说「我想学 XXX」或直接 `/coursecoach` 即可触发。

**在别的 agent / 模型里**（Claude Code、Cursor、自建 pipeline 都行）：
`SKILL.md` 是一份纯 Markdown 说明书，`references/` 是它的附件。把它们喂进 system prompt
或上下文即可复用整套流程，脚本照跑。细节见 [PORTABLE_USAGE.md](PORTABLE_USAGE.md)。

## 二、环境

- 需要 **Python 3.8+** 和 `pyyaml`：`pip install pyyaml`
- 只有导出 Word 时才需要 `python-docx`：`pip install python-docx`
- 脚本只用标准库 + pyyaml，Windows / macOS / Linux 通用，无平台锁定
- **唯一要求是那个解释器能 `import yaml`**。装过依赖的解释器不一定叫 `python`，
  换一个试 `python3` 或它的绝对路径即可

## 三、第一次跑：造一门 15 分钟的试玩课

**推荐**：在支持 skill 的 agent 里直接说「我想学 XX，每天 1 小时」。
它会走完澄清 → 大纲 → 看板 → 作业，你不用碰命令行。

想手动跑一遍（不经过 agent），先写一个 `stages.json`，描述节点、知识点标签、三档周数：

```json
[
  {"id":"s1","title":"基本概念","points":["定义","三个例子","常见误解"],"weeks":[1,1.5,3]},
  {"id":"s2","title":"核心方法","prereqs":["s1"],"points":["方法A","方法B"],"weeks":[1,1.5,3]},
  {"id":"s3","title":"动手实战","prereqs":["s2"],"points":["小项目","复盘"],"weeks":[2,2,4]}
]
```

然后建课（`python` 换成那个能 `import yaml` 的解释器）：

```bash
python <skill>/scripts/init_course.py --dir ./demo --title "试玩课" --stages stages.json
```

它会顺手编译出主页，**双击 `demo/课程主页.html`** 就能看到：
可折叠大纲、环形进度、知识点标签，每章底部一排按钮——补讲解 / 出作业 / 补资料 / 本章全部知识点。

点按钮 → 勾选 → 右下角动作篮「复制指令」→ 把复制的文本粘回对话框发给 AI。
AI 按指令写讲义、出作业、批改，再重跑 `sync.py`，页面上就长出新东西。
**这是整套设计的核心**：静态页不假装自己是后端，只负责攒动作、拼指令，
真正的判断与写作交给 AI，确定性的计算交给脚本。

想看"学了一段时间之后"长什么样，双击 `coursecoach/examples/ai-fullstack/课程主页.html`
（一份真实课程快照，作答已清空）。

日常三条命令：

```bash
python <skill>/scripts/sync.py     --course ./demo        # 改完任何 md 后重编译
python <skill>/scripts/syllabus.py --course ./demo next   # 下一步该学什么
python <skill>/scripts/review.py   --course ./demo list   # 按遗忘曲线到期的复习
```

## 四、定时任务不跟着文件走（别以为丢了）

skill 包**不含**任何定时任务，这是设计而非疏漏：自动化是宿主状态，换台机器就没有。
所以包里带的是"重建配方"，落地后补一次即可：

```bash
python <skill>/scripts/schedule.py --course <课程目录> --check    # 值不值得建
python <skill>/scripts/schedule.py --course <课程目录> --json     # 完整规格
```

把 `--json` 的输出交给 agent，它调宿主的自动化接口建两条（**先问你要不要**）：

| 任务 | 时间 | 作用 |
|:--|:--|:--|
| 每日复习提醒 | 20:00 | 报到期的作业，**绝不自动推进**复习 |
| 前沿周更 | 周一 09:00 | 只在这门课涉及快速演进的领域时才建 |

宿主没有定时能力时（例如纯 CLI 环境）**降级不报错**：`review.py list` 照样算得出来，
只是没人主动叫你。详见 `coursecoach/references/portability.md`。

## 五、目录里都是什么

| 路径 | 作用 |
|:--|:--|
| `coursecoach/SKILL.md` | 主说明书：7 个阶段、动作协议、批改口径、脚本参数 |
| `coursecoach/references/` | 8 份分册：数据模型 / 课程设计 / 评分标准 / 并行调研 / 交付面 / 可移植性 / 动作篮协议 / 前沿周更 |
| `coursecoach/scripts/` | 9 个确定性脚本：建课、改大纲、编译主页、批改、复习队列、导出、清空、打包、排期配方 |
| `coursecoach/assets/` | 大纲与作业的空白模板 |
| `coursecoach/examples/ai-fullstack/` | 一份真实课程快照（作答已清空），可直接双击看效果 |

## 五点五、讲义怎么读（不装 Obsidian 也行）

`lessons/*.md` 是纯 Markdown，四种读法随便挑：

1. **在课程主页里点** —— 章节底部的「📄 打开 / 阅读本章讲义」。装了 Obsidian 就在库里打开；
   没装就在网页里弹出阅读面板，标题、表格、代码块都是排好版的。
2. **用 Markdown 编辑器** —— VS Code / Typora / Obsidian 打开 `lessons/xxx.md`，适合批注做笔记。
3. **导出成教材** —— `python scripts/export.py --course <课程目录> [--format docx]`，
   一次读完整门课，或打印、发给别人。
4. **任何文本编辑器** —— 记事本也能打开，只想搜个词、抄段代码时最省事。

阅读面板是编译时预渲染进 HTML 的：**不联网、不装任何软件**。把课程文件夹发给别人，
对方双击 `课程主页.html` 就能读到排版好的讲义。Obsidian 额外给的是双链、图谱、概念卡跳转，
不是"能不能读讲义"。

## 六、边界（先说清楚，免得期待过高）

- **不替你判断**。知识点怎么拆、题目出得好不好、批改给几分，都是 AI 的判断，
  脚本只负责把这些判断可靠地落盘。所以换更强的模型，效果会明显更好。
- **资料库需要核实**。AI 检索到的链接、免费额度、考试要求都可能过期，
  生成时会标「待核实」，请自己点一遍再信。
- **必须有可验证的环节**。目标要能落到"画出来 / 做出来 / 讲回来 / 通过测试"。
  纯鉴赏类目标（"想有品味"）得先翻译成可观察行为，否则批改无从下手。
- **示例里的路径是占位符**（`你的课程目录` 之类）。换成你自己的课以后跑一次
  `sync.py`，页面里所有路径就自动更新成真实位置。

## 七、出问题先看这

| 症状 | 原因 |
|:--|:--|
| `ModuleNotFoundError: yaml` | 换解释器，或 `pip install pyyaml` |
| 主页打不开 / 白屏 | 直接双击 html 文件；`file://` 被浏览器拦时换 Chrome |
| 页面数字是 `NaN` | 某节点缺 `weeks`，用 `syllabus.py set-weeks` 补 |
| 复制的指令里目录不对 | 课程被移动过，重跑 `sync.py --course <新位置>` |
| 点讲义没反应 | 旧版 `sync.py` 编译的页面；重跑 `sync.py`，讲义会预渲染进主页 |
| 讲义点开是一堆 `#` 和 `**` | 同上，重跑 `sync.py`。或直接用 Markdown 编辑器打开 `lessons/*.md` |
| 改了 `课程主页.html` 又变回去了 | 它是编译产物，下次 `sync.py` 会全量覆盖；改 `syllabus.md` |

---

协议细节在 `coursecoach/SKILL.md`，实现取舍在 `coursecoach/references/`。
改动脚本前先读一遍，里面有若干"看起来可以简化、其实一改就退化"的地方。
