---
nodes:
- id: s1
  title: 阶段一标题
  prereqs: []
  homework: []
  mastery: null
- id: s2
  title: 阶段二标题
  prereqs: [s1]
  homework: [hw-s2-topic]
  mastery: null
---
# 课程标题

> 课程定位：一句话说明这门课解决什么问题、面向什么目标。
> 目标程度：了解 / 能动手 / 能教。周期档位：冲刺 / 标准 / 长线。

## 课程目标

- 学完能达到：……
- 不追求（明确边界）：……

## 阶段说明（可逐节点展开）

### s1 · 阶段一标题
- 核心知识点：
- 主资源：
- 验收标准（可验证）：能画出来 / 跑通 / 解释设计动机

### s2 · 阶段二标题
- 先修：s1
- 核心知识点：
- 主资源：
- 验收标准：

## 使用说明

- 做作业：`homework/hw-*.md` 的「我的作答」区。
- 看进度：运行 `scripts/sync.py --course <本目录>` 生成主页。
- 演化大纲：`scripts/syllabus.py --course <本目录> add-node / set-prereqs`。
