# github_sync_workflow_kernel 安装说明

[English](INSTALL.md) | **简体中文**

## 装的是什么

一个 skill：`github-sync-agent`。它的 `agents/` 和 `references/` 就在自己目录里，所以整个目录就是可安装单元。

只用 Python 3.8+ 标准库，没有依赖要装。

## 装到 Codex

```bash
cd packages/github_sync_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

目标目录默认是 `$CODEX_HOME/skills`，`CODEX_HOME` 未设置时用 `~/.codex/skills`。

## 装到任何读 `SKILL.md` 的宿主

```bash
cp -r github-sync-agent ~/.workbuddy/skills/github-sync-agent
```

拷目录，不要只拷 `SKILL.md`：它会从自己旁边的子目录加载角色说明和工作流笔记。

## 验证

先用一个只读问题试：

> 这个工作区实际指向哪个仓库？有哪些还没推上去？

跑对了的话，它会先报出选中的仓库、分支、远端和未提交的改动，**然后**才谈提交。如果它上来就 `git add -A`，立刻停——这正是这个 skill 存在的意义所在。

## 坑

**它不装也不配 Git。** skill 假定 `git` 能跑、认证已经配好（SSH key 或凭据助手）。认证坏了它会陪你一步步查，但它不持有凭据，也不安装任何二进制。

**工作区根目录通常不是仓库。** 如果你打开的是一个装着好几个仓库的父目录，这个 skill 会先做仓库发现。你已经知道要动哪个目录的话直接说，能省一轮。

**提交不是默认结局。** 它会先给你看改动范围再停下等你确认；当改动看着不像故意的、混了生成产物、或者大部分是换行符噪音时尤其如此。这个停顿是特性——不看范围就一路点同意，等于把这个 skill 关掉。

**换行符和生成文件是被有意过滤的。** 如果某个你以为会出现在提交里的文件不见了，那是被判定成噪音了；看它给出的理由是哪种，别硬塞进去。

## 卸载

```bash
rm -rf ~/.codex/skills/github-sync-agent
```

这个目录之外什么都不动：没有 hook、不改 Git 配置、不加全局别名。
