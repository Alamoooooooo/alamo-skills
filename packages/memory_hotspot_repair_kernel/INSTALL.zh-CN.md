# memory_hotspot_repair_kernel 安装说明

[English](INSTALL.md) | **简体中文**

## 装的是什么

四个 skill，而且必须落在同一个父目录里：

| Skill | 角色 |
|:--|:--|
| `memory-optimizer-agent` | 编排入口 —— 你调用的就是它 |
| `memory-check` | 审查阶段：找内存风险模式和热点路径 |
| `memory-fix` | 修复阶段：给出安全、定向的改动 |
| `memory-review` | 修复后的独立复核 |

所有脚本只用 Python 3.8+ 标准库，没有 `pip install` 这一步。

## 装到 Codex

```bash
cd packages/memory_hotspot_repair_kernel
python3 scripts/sync_to_codex_home.py --dry-run    # 先看它打算拷什么
python3 scripts/sync_to_codex_home.py
```

目标目录默认是 `$CODEX_HOME/skills`，`CODEX_HOME` 未设置时用 `~/.codex/skills`。可以用 `--dest` 指定别处。

## 装到任何读 `SKILL.md` 的宿主

```bash
cp -r memory-optimizer-agent memory-check memory-fix memory-review ~/.workbuddy/skills/
```

分四次拷贝，落到同一个父目录——和脚本产生的布局一致。

## 验证

```bash
ls ~/.codex/skills | grep '^memory-'
```

应该是四个名字。然后随便问一句（比如「看看这个文件有没有内存风险」），确认编排入口在动手之前会报出一个审查阶段。

## 坑

**四个 skill 用兄弟路径互相引用。** `memory-optimizer-agent` 读取 `../memory-check/SKILL.md` 进审查阶段、`../memory-fix/SKILL.md` 进修复、`../memory-review/SKILL.md` 进复核。单独把某一个 skill 装进它自己的目录，这些路径就悬空了——而且**安装时不报错，要跑到中途才断**。

**包级 `references/` 不会被装。** `overlay-pattern.md` 和 `generic-overlay-template.md` 放在包根目录，从 skill 内部用 `../references/...` 访问。这个路径只在你从本仓库 checkout 出来跑的时候存在。装完之后还想写仓库专属 overlay，把这两个文件拷到四个 skill 目录旁边。

**同名目录是被替换，不是合并。** 同步脚本会先删掉同名目标再拷。你在 `~/.codex/skills/memory-*/` 里的本地改动，下次同步就没了；overlay 请放在这个目录树外面。

**`runs/` 会被剥掉。** 脚本忽略 `runs/`、`__pycache__/` 和 `*.pyc`，checkout 里的运行产物不会跟着装过去。

## 卸载

```bash
rm -rf ~/.codex/skills/memory-check ~/.codex/skills/memory-fix \
       ~/.codex/skills/memory-review ~/.codex/skills/memory-optimizer-agent
```

四个一起删。留下一个的话，编排入口仍会顺着兄弟路径找到它，然后以一种很难看懂的方式失败。
