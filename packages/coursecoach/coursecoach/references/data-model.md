# 数据模型

## 目录约定

```
<course-dir>/
├── syllabus.md          # Skill Graph（frontmatter nodes + 正文）——必需
├── homework/hw-*.md     # 每节点可多份
├── lessons/             # 讲义：<节点id>.md（整章）/ <节点id>--<知识点>.md（单点）
├── resources/资料库.md    # 附录资料库（可选）
├── 课程进度.md           # sync.py 生成，Obsidian 可读（可选产物，勿手改）
├── 课程主页.html         # sync.py 生成，勿手改
└── 教材.md / 教材.docx    # export.py 生成（可选）
```

`lessons/` 的文件名与节点 / 知识点必须精确对应，否则 `sync.py` 挂不上链接：
`stage0-math.md` 对应节点 `stage0-math`，`stage0-math--广播.md` 对应该节点下名为「广播」的知识点。
改名等于断链，但不会报错——只是页面上少一个 📄。

**最小可用课程 = 一个 `syllabus.md` + 一个 `homework/` 目录**。没有资料库、没有 vault、没有 Obsidian 也能编译出完整看板；`resources/`、`概念卡`、`进度页`全部是可选增量，缺了只会少内容，不会报错。

起新课的标准做法是 `init_course.py`（自动建目录、写 syllabus、编译主页），而不是手搓 frontmatter。

## 作业 frontmatter 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | str | 唯一标识，如 `hw-s1-basics` |
| `title` | str | 作业标题 |
| `topic` | str | 知识点 |
| `stage` | str | 所属节点 id（grade.py 据此更新 mastery） |
| `status` | enum | `pending` / `submitted` / `graded` |
| `score` | int/null | 0–100，未批改 null |
| `grade` | str/null | 优秀 / 良好 / 及格 / 不及格 |
| `rubric` | list[str] | 3–6 条可判定要求 |
| `graded_at` | str/null | ISO 时间 |
| `attempts` | int | 批改次数（复核累加） |
| `prereq_ok` | bool | 历史字段，实际解锁由 sync 动态计算 |

## syllabus nodes 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | str | 节点 id，任意字符串（`m1` / `node-intro` / `stage3-transformer`）。主页锚点即此值。仅当写成 `stage<N>` 形式时，才会自动链到 Obsidian 的 `10-阶段/Stage N *.md` 笔记 |
| `title` | str | 节点标题 |
| `prereqs` | list[str] | 先修节点 id |
| `homework` | list[str] | 挂载的作业 id |
| `mastery` | float/null | 0–1；null 表示未开始 |
| `summary` | str | 一句话概述，显示在主页展开区 |
| `points` | list[str] / list[dict] | **知识点标签**，折叠区逐条渲染。写字符串时按同名匹配 `20-概念/` 概念卡；要精确指定写成 `{t: 标签, note: 20-概念/卡片名}` |
| `weeks` | dict / list / number | 计划周数。推荐 `{sprint: 3, standard: 3, long: 4}`（冲刺/标准/长线三档）；也可写 `3` 或 `[3,3,4]` |

**课程级 frontmatter**（`syllabus.md` 顶部，可选）：

| 字段 | 说明 |
|---|---|
| `title` | 课程名，主页 H1 用；缺省取目录名 |
| `track` | 默认节奏档：`sprint` / `standard` / `long`（也接受中文「冲刺/标准/长线」）。改它用 `syllabus.py set-track`，不要手改 |
| `start` | 开课日期 `YYYY-MM-DD`，用于算预计收尾月份 |

## 课程主页（课程主页.html）

`sync.py` 编译的自包含看板，具备：

- **折叠大纲**：每节点一张卡，默认收起（只展开「当前阶段」= 已解锁且未达标的第一个），点击标题展开知识点标签。
- **知识点标签**：命中概念卡的可点，跳 `obsidian://open?vault=…&file=20-概念/…`；未命中的点击即按该词筛选。
- **跳转**：左侧目录、阶段间先修链接、`课程主页.html#<node-id>` 深链（深链会展开并高亮该节点），便于从 Obsidian 跳进来。
- **进度展示**：环形课时进度（按周数×掌握度加权）、已达标阶段数、平均掌握度、作业已批改、待复习数。
- **节奏切换**：冲刺/标准/长线三档，实时重算总周数、每节点起止周与预计收尾月。
- **搜索与筛选**：`/` 聚焦搜索（匹配标题/概述/知识点），筛选 全部 / 进行中 / 已达标 / 未解锁。
- 折叠状态与节奏选择存 `localStorage`（**仅 UI 状态**，进度数据仍只存 frontmatter）。


## mastery 与解锁

- 折算：优秀 0.9 / 良好 0.75 / 及格 0.6 / 不及格 0.0（由 grade.py 写入）。
- 解锁：某节点所有 `prereqs` 的 mastery 均 ≥ 0.6 → 该节点 `unlocked = true`（sync 动态算，不写回）。
- 未达标节点在主页标「未解锁」，但仍可查看，不强锁访问。

## 权威数据 vs 编译产物

- **frontmatter 是唯一权威源**：分数、掌握度、先修关系都只在 md 头部。
- `课程主页.html` 是 `sync.py` 的只读编译产物；每次 grade / syllabus 改动后自动重编译。
- 页面用**自包含内联数据**（非 fetch、非 localStorage），双击可用。
