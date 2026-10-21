# 参与维护

[English](CONTRIBUTING.md) | **简体中文**

这个仓库是四个 skill 包，加它们周围的文档。没有构建步骤，除了 `pyyaml` 没有依赖要装，也没有服务要起。它有的是几条约定——让四个会各自演化的包始终能被读懂，其中大部分由一个脚本强制。

## 每次提 PR 之前先跑这个

```bash
python3 scripts/check.py
```

它检查七件事：

| 检查项 | 什么情况会失败 |
|:--|:--|
| 包内文件 | 缺 `README.md`、`PORTABLE_USAGE.md` 或 `metadata.json`；或者整个包里找不到 `SKILL.md` |
| 双语配对 | 有 `INSTALL.md` 但没有 `INSTALL.zh-CN.md`；或者任何 `*.zh-CN.md` 找不到英文对应 |
| 相对链接 | markdown 链接指向的文件不存在 |
| 元数据 | JSON 不合法、缺必填字段、协议不是 Apache-2.0 |
| 脚本语法 | 某个 `.py` 编译不过 |
| 两份根 README 对齐 | 中英两版的 `##` 节数不一致 |
| 构建产物 | 提交了 `.pyc`、`.zip`、`.DS_Store` |

绿了，说明下面这些规矩都还成立；红了，它会直接指出文件和原因。退出码非零，所以也能当 pre-push 钩子或 CI 步骤用。

## 分量最重的五条

**一、每份状态只有一个写入口。** 包里凡是能推导出来的东西，都只有一个入口能写它。在 `coursecoach` 里，只有 `grade.py` 能写掌握度、只有 `syllabus.py` 能写节点图——因为一次批改要同时更新作业 frontmatter、反馈区、节点掌握度、解锁状态四处。手改四次，迟早会对不上，而且不会报错。**当你开始手改生成物，说明脚本缺个参数，不是文档缺条警告。**

**二、构建产物不提交。** 编译出来的课程主页、导出的教材、打好的 zip 都不进仓库。有一处例外是有意的：`packages/coursecoach/coursecoach/examples/` 里那份编译好的主页是提交进去的，为的是别人不跑任何东西就能双击看效果。它是产品样品，不是构建产物——当数据处理，只在示例课程本身变了时才重新生成。

**三、双语文件必须成对。** 两份根 README，以及每个包的 `INSTALL.md` / `INSTALL.zh-CN.md`。只改一份，另一半读者手里的说明就是过期的，而仓库表面上一切正常。两版章节顺序保持一致，读者可以按位置对照译文。

**四、改了结构就得改 `packages/README.md`。** 那是唯一解释三层结构、该拷哪个目录、以及 `packages/coursecoach/coursecoach/` 为什么重名的文件。新增文件约定、移动目录、加包，都得在同一个提交里更新它。

**五、没做的计划进 `todo/`。** 不要放根目录。根目录下的 `TODO_*.md` 在每个打开仓库的人眼里都是一句承诺；`todo/` 是「想过，但没承诺」。

## 提交信息

一行标题，祈使句，不加句号。空一行，然后写**为什么**：改之前哪里不对、为什么是这个形状。别复述 diff，审的人自己会看。

```
Point the README at the live demo

Everything in the coursecoach section asked the reader to install something
before they could judge it: two screenshots prove the board renders, but not
that clicking a stage opens a lesson.
```

一个提交一件事。如果信息里需要写「另外」，那就是两个提交。

## 动脚本之前

**跑它。** 不是 `--help`，是真跑一门课。编译通过不算验证：脚本可以编译通过、照样写出一个坏文件，而故障要到三步之后在看板上以一个错误的数字出现。

```bash
cp -r packages/coursecoach/coursecoach/examples/ai-fullstack /tmp/try
python3 packages/coursecoach/coursecoach/scripts/sync.py --course /tmp/try
```

然后去看输出，不要只看退出码。

## 审 PR 时看什么

- 中英两版说的是不是同一件事、顺序是否一致
- 有没有改生成物，而不是重新生成
- 动了包结构却没动 `packages/README.md` 吗
- 提交信息说的是**为什么**，还是只有**是什么**
- 脚本改动：真的对着课程跑过吗

合并用 **Squash**。`main` 上的历史是一件事一条提交；一个 PR 里五条 `fix typo` 不该改变这个。

## 加一个包

1. `packages/<名字>/`，含 `README.md`、`PORTABLE_USAGE.md`、`metadata.json`
2. 每个可安装单元一个目录，各自带 `SKILL.md`
3. 安装有坑要写的话，加 `INSTALL.md` + `INSTALL.zh-CN.md`
4. `metadata.json` 里加 `license` 字段（`"Apache-2.0"`，检查脚本会强制）
5. 两份根 README 各加一处：总表一行、独立小节、目录树

`packages/README.md` 末尾有同一份清单，两边保持一致。

## 会被拒的改动

- 对 `main` 做 force push，或改写已经发布出去的历史
- 提交 `__pycache__`、`.pyc`、zip
- 在根目录新建一个专门用来放计划或草稿的文件
- 以「顺手清理」为名重命名目录——路径是面向用户的，它们在安装命令里，也在别人已经复制走的文字里
- 把不相关的改动塞进同一个提交

## 东西在哪

| 文件 | 回答什么 |
|:--|:--|
| `README.md` | 仓库里有什么、每个包怎么装 |
| `packages/README.md` | 包怎么组织、该拷哪个目录、为什么四个包长得不一样 |
| `<包>/README.md` | 这个包是干什么的、给谁用 |
| `<包>/INSTALL.md` | 怎么装，以及装错一点点会坏在哪 |
| `<包>/PORTABLE_USAGE.md` | 不装 skill 的宿主怎么用 |
| `AGENTS.md` | 在这个仓库里干活的 AI agent 该守的规矩 |
| `todo/` | 想过，但没承诺 |

## 许可

Apache-2.0。提 PR 即视为你的贡献按同样条款授权（协议第 5 条），不需要另签 CLA。任何包含本代码的分发物都必须附带一份 `LICENSE`。
