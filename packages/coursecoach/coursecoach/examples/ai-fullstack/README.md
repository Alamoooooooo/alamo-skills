# 示例课程：AI 全栈（真实产出快照）

这不是模板，是 `coursecoach` **真实跑完一整轮**之后的产物，用来给人和 AI 各看一眼：

- **人**：直接双击 `课程主页.html`，看「可交互课程」最终长什么样。
- **AI**：想知道每个文件该写多细、字段怎么填、主页该有哪些交互，照这个抄，而不是照空模板猜。

> 快照时间 2026-10-18。原课程在 `你的课程目录`（Obsidian vault 内），
> 因此本目录里的 `file:///` 链接与概念卡双链仍指回原路径——复制出去后请重跑 `sync.py` 重建。

## 文件清单

| 文件 | 类型 | 说明 |
|---|---|---|
| `syllabus.md` | 权威数据 | 14 节点 Skill Graph。每个节点含 `id / title / prereqs / homework / mastery` + `summary / points / weeks{sprint,standard,long}` |
| `homework/hw-stage0-vec.md` | 权威数据 | 向量与线性组合小测：frontmatter 记分，正文三段「题目要求 / 我的作答 / 批改反馈」 |
| `resources/资料库.md` | 权威数据 | 按课程 / 书 / 论文 / 工具分类，每条注明用途与代价 |
| `课程主页.html` | **编译产物** | `sync.py` 生成，36 KB 自包含，双击即用，勿手改 |
| `课程进度.md` | **编译产物** | Obsidian 原生可读的进度页（进度表 + 主页跳转 + 逐节点深链） |
| `教材.md` | **导出产物** | `export.py` 生成（大纲 + 全部作业 + 资料库附录）；加 `--format docx` 出 Word |

## 看板能做什么（打开 html 自己试）

- 左侧目录树，点击跳转到章节
- 环形课时进度：按 Σ(周数 × mastery) 加权，不是数节点个数
- 折叠大纲：默认只展开「当前阶段」，可一键全展开 / 全收起
- 知识点标签：有概念卡时 Ctrl/⌘ + 点击直达 Obsidian；普通点击弹出「生成讲解 / 出题 / 补资料 / 筛选」
- **动作按钮 + 动作篮**：章节里「补讲解 / 出作业 / 补资料 / 本章全部知识点」，作业行「批改」，知识点菜单里也有同类项。选中项进右下角动作篮（刷新不丢），点「复制指令」得到一段结构化文本，粘回对话框即可让 AI 执行 —— 纯静态页不冒充后端
- 锚点深链：`课程主页.html#stage1-tensor` 进来只展开该节点并高亮
- 三档节奏切换（冲刺 / 标准 / 长线），周次与总周期实时重算
- 搜索 + 状态筛选（未解锁 / 进行中 / 已达标）
- 深浅双主题；UI 状态存 localStorage，**分数与进度只存在 frontmatter 里**
- 批改状态徽章：及格 / 良好 / 优秀，复习到期提醒
- 生成过讲义（`lessons/`）后，章节底部出现「📄 打开本章讲义」，知识点标签前显示 📄

## 用它起一门新课

```bash
# 方式 A：完全从零（推荐，任意主题）
python scripts/init_course.py --dir 你的课程根目录/rust \
  --title "Rust 系统编程" --stages stages.json

# 方式 B：拿本示例当骨架改（只适合同为「阶段制长课」的目标）
cp -r examples/ai-fullstack 你的课程根目录/我的课
# 改 syllabus.md 的 nodes，删掉 homework/ 里的旧作业，重跑 sync.py
```

**改完必须重跑**：

```bash
python scripts/sync.py --course 你的课程根目录/我的课
```

## 规模参考

| 指标 | 本示例 |
|---|---|
| 节点数 | 14 |
| 每个节点知识点标签 | 5–10 个 |
| 节点周数（冲刺档） | 1–2 周 |
| 主页体积 | 约 36 KB（自包含，无外链、无 CDN） |
| 单份作业 rubric | 3–6 条 |
| 一轮流程耗时 | 澄清 + 方案确认 + 检索 + 落盘 + 编译 |

## 不要照搬的部分

- 具体阶段名、周数、资料条目 —— 换主题必须重新检索，别复制旧结论。
- `mastery` 数值 —— 示例里 0.75 是实测批改结果，新课程从 `null` 起步。
- 绝对路径 —— 全机通用性靠 `--course` 参数，不写死。

## 本示例已脱敏

本示例的作答与批改记录**已经清空**（`status: pending` / `score: null` / 节点 mastery 全 `null`），可以放心当模板或分享。
自己课程要脱敏时跑：

```bash
python scripts/reset.py --course <course-dir> --all              # 清空全部作业的作答与批改，并回退 mastery
python scripts/reset.py --course <course-dir> --hw hw-xxx        # 只清一份
python scripts/reset.py --course <course-dir> --all --keep-mastery  # 只清文字，保留掌握度
```

`reset.py` 会保留「题目要求」与 `rubric`（那是题目设计），只清「我的作答」「批改反馈」两区，并自动重编译主页。

分享整门课（含脚本，解压即用）：

```bash
python scripts/pack.py --course <course-dir>          # 先自检，再打成 zip
python scripts/pack.py --course <course-dir> --check  # 只自检
```

`pack.py` 会拦下「作业里还留着你的作答 / 批改记录」，避免把答案一起发出去。
