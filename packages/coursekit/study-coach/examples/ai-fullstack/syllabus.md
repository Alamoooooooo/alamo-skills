---
title: AI 全栈学习路线
track: 冲刺
start: '2026-10-14'
nodes:
- id: stage0-math
  title: 数学重启（线代优先）
  prereqs: []
  homework:
  - hw-stage0-vec
  mastery: null
  summary: 不重刷教材，只补「看不见的地方」：向量是方向，矩阵是变换，导数就是斜率。
  points:
  - 向量与线性组合
  - 矩阵乘法的几何意义
  - 列空间与秩
  - 特征值直觉
  - 链式法则
  - 矩阵求导
  - 概率与期望
  - 梯度下降直觉
  - 形状心算
  weeks:
    sprint: 3
    standard: 3
    long: 4
- id: stage1-ml
  title: 机器学习速通
  prereqs:
  - stage0-math
  homework: []
  mastery: null
  summary: 先建立「什么问题该用什么模型」的判断力，而不是刷算法。
  points:
  - 过拟合与泛化
  - 偏差-方差权衡
  - 正则化
  - 数据泄漏
  - 交叉验证
  - 树模型 vs 线性模型
  - 评估指标
  - 基线优先
  weeks:
    sprint: 1.5
    standard: 2
    long: 3
- id: stage2-dl
  title: 深度学习速通
  prereqs:
  - stage1-ml
  homework: []
  mastery: null
  summary: 手写一遍反向传播，你就再也不会把框架当黑箱。
  points:
  - 反向传播
  - 计算图
  - SGD 与 AdamW
  - 参数初始化
  - BatchNorm 与 LayerNorm
  - Dropout
  - 学习率调度
  - 训练调试（loss 不降）
  - 过拟合与欠拟合
  weeks:
    sprint: 2
    standard: 2.5
    long: 4
- id: stage3-transformer
  title: Transformer 精读
  prereqs:
  - stage2-dl
  homework: []
  mastery: null
  summary: 精学起点。每个部件都要能回答「为什么这样设计」。
  points:
  - 自注意力
  - QKV
  - 多头注意力
  - 缩放点积
  - 位置编码
  - RoPE
  - 残差与 Pre-LN
  - 因果掩码
  - 从零实现小 GPT
  weeks:
    sprint: 2
    standard: 2.5
    long: 4
- id: stage4-pretrain
  title: 预训练与 Scaling
  prereqs:
  - stage3-transformer
  homework: []
  mastery: null
  summary: 从 tokenizer 到训练成本，理解大模型是怎么被造出来的。
  points:
  - Scaling Laws
  - Chinchilla 配比
  - Tokenizer
  - BPE
  - 数据清洗与去重
  - 数据墙与合成数据
  - nanochat 全链路
  - 训练成本量级
  weeks:
    sprint: 1
    standard: 1.5
    long: 2.5
- id: stage5-post-transformer
  title: 后 Transformer 架构
  prereqs:
  - stage4-pretrain
  homework: []
  mastery: null
  summary: 2026 必补：注意力之后的架构，真正的敌人是 KV Cache。
  points:
  - KV Cache
  - SSM 与 Mamba
  - 线性注意力
  - MLA
  - 稀疏注意力
  - 混合架构
  - 硬件感知实现
  - 注意力失忆
  - 有效上下文长度
  - MoE
  weeks:
    sprint: 1.5
    standard: 2.5
    long: 4
- id: stage6-rl
  title: 强化学习基础
  prereqs:
  - stage5-post-transformer
  homework: []
  mastery: null
  summary: 策略梯度到 PPO，为后训练打地基。
  points:
  - MDP 与回报
  - 策略梯度
  - 优势函数
  - PPO
  - 值函数（critic）
  - 探索与稳定性
  weeks:
    sprint: 1
    standard: 1.5
    long: 2.5
- id: stage7-posttrain
  title: 后训练与对齐
  prereqs:
  - stage6-rl
  homework: []
  mastery: null
  summary: 现代大模型的核心：SFT → 偏好优化 → 可验证奖励。
  points:
  - SFT
  - RLHF
  - DPO
  - GRPO
  - RLVR
  - 奖励模型
  - 推理模型与测试时计算
  - RLCD
  - 置信度校准
  - 后训练的隐藏代价
  weeks:
    sprint: 2
    standard: 3
    long: 5
- id: stage8-inference
  title: 推理 / 测试时计算 / 效率
  prereqs:
  - stage7-posttrain
  homework: []
  mastery: null
  summary: 推理为什么贵、怎么便宜，全在 KV Cache 与内存带宽里。
  points:
  - KV Cache
  - PagedAttention
  - 投机解码
  - 量化（INT8/FP8）
  - 批处理与吞吐
  - 显存-带宽-算力
  - 测试时计算
  weeks:
    sprint: 1
    standard: 1.5
    long: 3
- id: stage9-rag
  title: RAG 与检索
  prereqs:
  - stage8-inference
  homework: []
  mastery: null
  summary: 检索不是外挂，是把「不知道」变成「查得到」。
  points:
  - 切分与嵌入
  - 向量检索
  - 混合检索与重排
  - 查询改写
  - 忠实度与召回评估
  - 长上下文 vs RAG
  weeks:
    sprint: 1
    standard: 1.5
    long: 2.5
- id: stage10-agent
  title: Agent 开发
  prereqs:
  - stage9-rag
  homework: []
  mastery: null
  summary: Agent = Model + Harness。循环、工具、记忆、评估。
  points:
  - Agent 循环
  - ReAct
  - 上下文工程
  - 工具设计
  - MCP
  - A2A
  - 多智能体
  - 记忆与状态
  - τ-bench
  - 轨迹准确率
  - 可观测性
  weeks:
    sprint: 2.5
    standard: 3.5
    long: 6
- id: stage11-harness
  title: Harness 工程
  prereqs:
  - stage10-agent
  homework: []
  mastery: null
  summary: harness 决定行为，而不是单个 prompt。
  points:
  - Agent = Model + Harness
  - 五功能闭环
  - 工具工效学
  - 沙箱与权限
  - 错误恢复
  - 压缩（compaction）
  - 子 agent 调度
  - 内层与外层 harness
  - 决策层分离
  weeks:
    sprint: 1.5
    standard: 2
    long: 3.5
- id: stage12-loopgraph
  title: Loop 与 Graph 工程
  prereqs:
  - stage11-harness
  homework: []
  mastery: null
  summary: 从「跑一次」到「跑得住」：循环与图的手艺。
  points:
  - Self-Improvement Loop
  - Self-Correction Loop
  - 验证器与外部检查
  - 停止条件
  - 反馈设计
  - Loop 工程
  - Graph 工程
  - 共享状态与冲突
  - 确定性 vs 概率性控制
  weeks:
    sprint: 1.5
    standard: 2
    long: 3
- id: stage13-frontier
  title: 前沿追踪 + Capstone
  prereqs:
  - stage12-loopgraph
  homework: []
  mastery: null
  summary: 每周 1–2 小时：读论文 + 写三句话 + 做一个 Capstone。
  points:
  - 论文三句话摘要
  - 多模态与空间感知
  - 具身智能四条路线
  - 世界模型
  - Agentic RL
  - 可解释性
  - Capstone 项目
  weeks:
    sprint: 0
    standard: 0
    long: 0
---

# AI 学习路线图（Skill Graph）

> 这是「自适应学习助教」的大纲总纲。**每个节点 = 一个学习模块**，含先修（prereqs）、对应作业（homework）、掌握度（mastery，由批改回写 0–1）。
> 节点按先修链串联：前驱 mastery < 0.6 时，后继在课程主页标「未解锁」。
> 内容母版见 `../AI学习方案.md`，概念卡片见 `../AI-Vault/`。

## 使用说明

- **做作业**：打开 `homework/` 下对应 `hw-*.md`，在「我的作答」区写，写完让我「批改」。
- **看进度**：跑 `tools/sync.py` 生成 `课程主页.html`（自包含，双击看）。
- **动态演化**：发现薄弱点 → 我会据错题在图谱里加节点 / 调先修（阶段 3 能力）。

## 阶段链

```
stage0-math → stage1-ml → stage2-dl → stage3-transformer → stage4-pretrain
   → stage5-post-transformer → stage6-rl → stage7-posttrain → stage8-inference
   → stage9-rag → stage10-agent → stage11-harness → stage12-loopgraph → stage13-frontier
```

当前只有 `stage0-math` 挂了第一份作业 `hw-stage0-vec`，其余节点的作业会在对应阶段开启时由助教生成。
