# engineering_subagent_workflow_kernel 安装说明

[English](INSTALL.md) | **简体中文**

## 装的是什么

五个各自独立的 skill：

| Skill | 干什么 |
|:--|:--|
| `code-explorer` | 追一条执行路径，讲清代码怎么跑，带源码证据 |
| `code-architect` | 给功能或重构出实现蓝图 |
| `code-reviewer` | 审改动：缺陷、回归、安全风险、测试缺口 |
| `code-simplifier` | 降复杂度，保持可观察行为不变 |
| `pr-test-analyzer` | 找出改动里的测试缺口 |

每个 skill 的角色说明就在自己目录里。**五个都装**——它们是按任务选的，缺一个只是让那类活儿白白退回主会话。

只用 Python 3.8+ 标准库。

## 装到 Codex

```bash
cd packages/engineering_subagent_workflow_kernel
python3 scripts/sync_to_codex_home.py --dry-run
python3 scripts/sync_to_codex_home.py
```

目标目录默认是 `$CODEX_HOME/skills`，`CODEX_HOME` 未设置时用 `~/.codex/skills`。

## 装到任何读 `SKILL.md` 的宿主

```bash
cp -r code-explorer code-architect code-reviewer code-simplifier pr-test-analyzer \
      ~/.workbuddy/skills/
```

## 验证

先从最便宜的那个开始：

> 用 code-explorer 追一下 X 是怎么接起来的，只读。

装对了的话，它会先说准备读什么，产出带文件名和行号的证据，最后给总结而不是补丁。运行时会说明自己是作为原生子代理执行，还是退回了主会话。

## 坑

**不要只装 `SKILL.md`。** 有些第三方 bundle 只发 skill 文件、不带周边资源；这个包里的脚本特意按整目录拷贝，就是为了这个。手工拷的话，拷目录。

**没有原生子代理的宿主照样能用，但不一样。** skill 会在主会话里跑，并报 `fallback_in_session`。结果可用，但它跟父会话共用上下文和轮次预算，一次大范围探索可能把整段对话挤掉。如果当前会话本身就是那个专用子代理，它会直接执行角色并报 `executed_as_native_child`，不会再派生一个。

**这个包从不越过宿主。** 审批、沙箱、模型选择、仓库规则、工具可用性，都由宿主决定。这里没有辅助二进制、没有嵌套 agent 进程、也没有藏在里面的模型选择。

**五个里只有 `code-simplifier` 会改代码**，而且只改给它的范围。如果 `code-explorer` 或 `code-reviewer` 开始写文件，那是调用方式出了问题，不是特性。

## 卸载

```bash
rm -rf ~/.codex/skills/code-explorer ~/.codex/skills/code-architect \
       ~/.codex/skills/code-reviewer ~/.codex/skills/code-simplifier \
       ~/.codex/skills/pr-test-analyzer
```

没有全局状态、没有 Git hook、这些目录之外没有配置文件。
