# Functionality Deep-Dive V3 逐文件实施清单

> **目标**：将 `Functionality Deep-Dive` 独立子工作流拆解到“文件级实施”粒度，便于你确认后直接进入搭建与改造。  
> **范围**：  
> - 子工作流自身目录结构  
> - 每个文件的职责、核心内容、输入输出、依赖关系  
> - 与主工作流的对接点  
> - MVP 必做项与后续增强项  

---

## 一、实施目标

`Functionality Deep-Dive V3` 的目标不是再做一套“普通 RCA”，而是专门处理以下高难业务逻辑问题：

- 偶发功能异常
- 状态机跳转错误
- 多模块联动导致的数据异常
- 并发/竞态问题
- 缓存一致性/脏读/漂移
- 生命周期异步耦合
- Crash 栈落在系统层但根因在业务上层

这条子工作流需要满足 4 个核心要求：

1. 能独立跑完整深度分析链路
2. 能输出重型中间产物
3. 能收敛为 `Primary Root Cause + Contributing Factors`
4. 能把结果回注主工作流，而不是孤立存在

---

## 二、建议目录结构

```text
mobile-qa-workflow/
  functionality-deep-dive/
    core/
      workflow.xml
      workflow-model.yaml
      workflow-status-template.yaml
      default-config.yaml
    phases/
      f1-context-reconstruction.md
      f2-state-topology.md
      f3-temporal-correlation.md
      f4-isolation-debate.md
      f5-defensive-fix-design.md
    agents/
      context-reconstructor.md
      state-analyst.md
      temporal-analyst.md
      challenger.md
      arbiter.md
      defensive-fix-architect.md
    templates/
      environment-factor-report.md
      deep-dive-topology.md
      concurrency-analysis-report.md
      functionality-deep-dive-rca.md
      defensive-fix-design.md
      deep-dive-summary.md
    reference/
      environment-factor-thresholds.md
      analysis-strategies.md
      reasoning-chain.md
      platform-checklist.md
      race-condition-patterns.md
      state-machine-patterns.md
    FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md
```

---

## 三、文件清单总览

### 3.1 必做文件

| 文件 | 优先级 | 说明 |
|------|--------|------|
| `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md` | P0 | 子工作流总设计入口 |
| `core/workflow.xml` | P0 | 子工作流主编排器 |
| `core/workflow-model.yaml` | P0 | 阶段序列 |
| `core/workflow-status-template.yaml` | P0 | 子工作流状态模板 |
| `core/default-config.yaml` | P0 | 子工作流默认配置 |
| `phases/f1-context-reconstruction.md` | P0 | Stage 1 |
| `phases/f2-state-topology.md` | P0 | Stage 2 |
| `phases/f3-temporal-correlation.md` | P0 | Stage 3 |
| `phases/f4-isolation-debate.md` | P0 | Stage 4 |
| `phases/f5-defensive-fix-design.md` | P1 | Stage 5 |
| `templates/deep-dive-summary.md` | P0 | 回注主工作流的关键摘要 |
| `templates/functionality-deep-dive-rca.md` | P0 | 专项 RCA 正式产物 |

### 3.2 强烈建议首批一起做

| 文件 | 优先级 | 说明 |
|------|--------|------|
| `templates/environment-factor-report.md` | P1 | Stage 1 结构化报告 |
| `templates/deep-dive-topology.md` | P1 | Stage 2 结构化报告 |
| `templates/concurrency-analysis-report.md` | P1 | Stage 3 结构化报告 |
| `templates/defensive-fix-design.md` | P1 | Stage 5 附录 |
| `agents/context-reconstructor.md` | P1 | Stage 1 专项 Agent |
| `agents/state-analyst.md` | P1 | Stage 2 专项 Agent |
| `agents/temporal-analyst.md` | P1 | Stage 3 专项 Agent |
| `agents/challenger.md` | P1 | Stage 4 质疑员 |
| `agents/arbiter.md` | P1 | Stage 4 仲裁员 |
| `reference/environment-factor-thresholds.md` | P1 | Stage 1 知识库 |

### 3.3 可延后增强文件

| 文件 | 优先级 | 说明 |
|------|--------|------|
| `agents/defensive-fix-architect.md` | P2 | Stage 5 独立修复架构师 |
| `reference/analysis-strategies.md` | P2 | 专项策略池 |
| `reference/reasoning-chain.md` | P2 | 专项推理链 |
| `reference/platform-checklist.md` | P2 | 平台专项检查 |
| `reference/race-condition-patterns.md` | P2 | 竞态模式库 |
| `reference/state-machine-patterns.md` | P2 | 状态机模式库 |

---

## 四、逐文件实施清单

## 4.1 根入口文件

### 文件：`mobile-qa-workflow/functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`

**优先级**：P0  
**定位**：子工作流的“总说明 + 总契约 + 总阶段定义”。

#### 这个文件必须回答的问题

1. 这个子工作流解决什么问题
2. 什么时候由主工作流触发
3. 输入是什么
4. 五个阶段分别做什么
5. 会输出哪些产物
6. 哪个产物回注主工作流
7. 和主工作流的边界是什么

#### 建议章节结构

1. 背景与目标
2. 适用场景与不适用边界
3. 与主工作流的集成方式
4. 五阶段模型
5. I/O 契约
6. 关键产物说明
7. 与主工作流回注关系

#### 核心输入

- `issue-card.md`
- `spec.md`
- `context-bundle.md`
- 主工作流路由结果

#### 核心输出

- `functionality-deep-dive-rca.md`
- `deep-dive-summary.md`
- 条件输出：`defensive-fix-design.md`

#### 与其他文件依赖

- 依赖 `core/workflow.xml` 执行
- 被主工作流 `p3-root-cause.md` 调用

---

## 4.2 子工作流核心引擎文件

### 文件：`functionality-deep-dive/core/workflow.xml`

**优先级**：P0  
**定位**：子工作流主编排器。

#### 核心职责

1. 读取子工作流状态
2. 根据 `workflow-model.yaml` 判断当前阶段
3. 顺序调度 F1-F5
4. 处理失败、暂停、人工介入
5. 在完成后输出 `deep-dive-summary.md`

#### 必须包含的 step

1. 加载 core-rules
2. 读取/初始化子工作流状态
3. 根据 `workflow-model.yaml` 判断当前阶段
4. 执行当前阶段
5. 阶段完成后更新状态并路由

#### 必须支持的状态

- `DD-Intake`
- `DD-InProgress`
- `DD-LowConfidence`
- `DD-Human-Review`
- `DD-Completed`

#### 必须支持的异常流

- 证据不足 -> 回主工作流补上下文
- 多 Agent 不收敛 -> Human Review
- Stage 3 无法建立时序 -> 降级输出不确定性

#### 输出要求

- 最后必须统一输出：
  - `functionality-deep-dive-rca.md`
  - `deep-dive-summary.md`

---

### 文件：`functionality-deep-dive/core/workflow-model.yaml`

**优先级**：P0  
**定位**：定义五个阶段的顺序。

#### 内容建议

```yaml
workflow_step:
- 1. f1-context-reconstruction
- 2. f2-state-topology
- 3. f3-temporal-correlation
- 4. f4-isolation-debate
- 5. f5-defensive-fix-design
```

#### 注意点

- 不要引入和主工作流同名 phase
- 子工作流内部使用自己命名体系

---

### 文件：`functionality-deep-dive/core/workflow-status-template.yaml`

**优先级**：P0  
**定位**：子工作流状态模板。

#### 建议字段

```yaml
issue_id: null
parent_issue_id: null
current_state: DD-Intake
current_stage: null
stepsCompleted: []
lastStep: null
last_updated: null
confidence: null
primary_root_cause: null
contributing_factor_count: 0
artifacts: []
```

#### 关键点

- `parent_issue_id`：明确这是从主工作流分诊过来的子问题
- `artifacts`：记录已生成产物
- `confidence`：保存当前专项 RCA 置信度

---

### 文件：`functionality-deep-dive/core/default-config.yaml`

**优先级**：P0  
**定位**：子工作流输出路径和能力开关。

#### 建议字段

```yaml
parent_issue_id: null
workspace_folder: null
output_environment_factor_report: null
output_topology_report: null
output_concurrency_report: null
output_deep_dive_rca: null
output_defensive_fix_design: null
output_deep_dive_summary: null
env_subagent: true
```

#### 用途

- 让每个阶段统一写入输出路径
- 便于主工作流后续读取 summary / 附录

---

## 4.3 五个阶段文件

### 文件：`functionality-deep-dive/phases/f1-context-reconstruction.md`

**优先级**：P0  
**定位**：环境与上下文重构。

#### 核心职责

1. 重建极端环境因素
2. 检查生命周期/系统干预
3. 标记环境因素与代码位置的关联
4. 输出环境因子报告

#### 输入

- `issue-card.md`
- `spec.md`
- `context-bundle.md`
- `reference/environment-factor-thresholds.md`

#### 输出

- `environment-factor-report.md`

#### 必须包含的动作

- LMK / 内存水位
- Thermal State
- 网络抖动 / 丢包
- 前后台切换
- 权限撤销 / 配置变更
- CPU / 磁盘 / GPU 压力

#### 必须遵守的约束

- 禁止给修复方案
- 允许标注环境因子与代码位置关联

---

### 文件：`functionality-deep-dive/phases/f2-state-topology.md`

**优先级**：P0  
**定位**：状态机拓扑与数据流还原。

#### 核心职责

1. 状态机逆向绘制
2. 数据流污点追踪
3. 不可变性审查
4. 输出状态拓扑报告

#### 输入

- `spec.md`
- `context-bundle.md`
- `environment-factor-report.md`（如存在）

#### 输出

- `deep-dive-topology.md`

#### 必须包含的内容

- 状态定义表
- Mermaid 状态图
- 孤岛状态
- 非法跳转
- 数据模型流转路径
- 脏写点/不可变性破坏点

#### 注意点

- 行号无法确定时必须允许 `[Line-Uncertain]`
- 这个文件不放时序轴

---

### 文件：`functionality-deep-dive/phases/f3-temporal-correlation.md`

**优先级**：P0  
**定位**：时序对齐与竞态剖析。

#### 核心职责

1. 建立统一时间轴
2. 扫描共享资源读写点
3. 识别竞态窗口
4. 给出高概率复现路径
5. 输出并发分析报告

#### 输入

- `deep-dive-topology.md`
- `context-bundle.md`
- 相关日志 / APM / 生命周期记录

#### 输出

- `concurrency-analysis-report.md`

#### 必须包含的内容

- 线程/队列模型
- 共享资源清单
- 时序轴
- 竞态窗口
- 复现概率（High/Medium/Low）
- 强制复现建议

#### 注意点

- 不要求 100% 自然复现
- 必须支持“时间精度降级策略”

---

### 文件：`functionality-deep-dive/phases/f4-isolation-debate.md`

**优先级**：P0  
**定位**：隔离诊断与多 Agent 对抗。

#### 核心职责

1. 基于控制变量做隔离推演
2. 启动多 Agent 深度对抗
3. 收敛为主根因 + 贡献因子
4. 输出正式专项 RCA

#### 输入

- `environment-factor-report.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`

#### 输出

- `functionality-deep-dive-rca.md`
- 中间对抗记录

#### 必须回答的问题

- 主根因是什么
- 是否存在多个贡献因子
- 贡献因子之间是什么关系
- 哪些假设被 Challenger 否决
- 哪些不确定性仍残留

#### 多 Agent 建议

- `state-analyst`
- `temporal-analyst`
- `challenger`
- `arbiter`

---

### 文件：`functionality-deep-dive/phases/f5-defensive-fix-design.md`

**优先级**：P1  
**定位**：防御性修复与架构演进建议。

#### 核心职责

1. 根据专项 RCA 输出防御性修复建议
2. 形成附录设计，回注主工作流 `fix-design.md`

#### 输入

- `functionality-deep-dive-rca.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`

#### 输出

- `defensive-fix-design.md`
- `deep-dive-summary.md` 中的 fix 建议摘要

#### 必须包含的内容

- 修复前/后状态拓扑
- 熔断器/断言点
- 生命周期感知处理点
- 渐进式落地路径
- 过度设计审查

#### 注意点

- 不替代主工作流 P4
- 只作为附录与增强输入

---

## 4.4 Agent 文件

### 文件：`functionality-deep-dive/agents/context-reconstructor.md`

**优先级**：P1  
**职责**：

- 专注环境与上下文重构
- 不给修复建议
- 输出环境因子关联结论

---

### 文件：`functionality-deep-dive/agents/state-analyst.md`

**优先级**：P1  
**职责**：

- 负责 Stage 2
- 输出状态机图、数据流、不可变性问题

---

### 文件：`functionality-deep-dive/agents/temporal-analyst.md`

**优先级**：P1  
**职责**：

- 负责 Stage 3
- 建立时序轴、竞态窗口、复现路径

---

### 文件：`functionality-deep-dive/agents/challenger.md`

**优先级**：P1  
**职责**：

- 对专项分析结果做深度质疑
- 重点质疑：
  - 因果充分性
  - 因果必要性
  - 生命周期盲区
  - 缓存一致性
  - 并发时序漏洞

---

### 文件：`functionality-deep-dive/agents/arbiter.md`

**优先级**：P1  
**职责**：

- 汇总多 Agent 结论
- 收敛为：
  - Primary Root Cause
  - Contributing Factors
- 给出最终置信度

---

### 文件：`functionality-deep-dive/agents/defensive-fix-architect.md`

**优先级**：P2  
**职责**：

- 负责 Stage 5 的防御性修复设计
- 输出架构加固建议

---

## 4.5 模板文件

### 文件：`functionality-deep-dive/templates/environment-factor-report.md`

**优先级**：P1  
**必须包含**

- 环境因子清单
- 异常阈值
- 关联代码位置
- 证据等级
- 不确定性说明

---

### 文件：`functionality-deep-dive/templates/deep-dive-topology.md`

**优先级**：P1  
**必须包含**

- 状态定义表
- Mermaid 图
- 孤岛状态
- 非法跳转
- 数据流
- 脏写点

**不要包含**

- 时序轴
- 竞态窗口

---

### 文件：`functionality-deep-dive/templates/concurrency-analysis-report.md`

**优先级**：P1  
**必须包含**

- 时序轴
- 共享资源
- 竞态窗口
- 高概率复现路径
- 强制复现建议
- 缓存一致性结论

---

### 文件：`functionality-deep-dive/templates/functionality-deep-dive-rca.md`

**优先级**：P0  
**必须包含**

- Primary Root Cause
- Contributing Factors
- 完整因果链
- 证据映射
- 对抗摘要
- 置信度

---

### 文件：`functionality-deep-dive/templates/defensive-fix-design.md`

**优先级**：P1  
**必须包含**

- 修复前/后拓扑
- 熔断器
- 生命周期感知点
- 渐进式落地路径
- 过度设计审查

---

### 文件：`functionality-deep-dive/templates/deep-dive-summary.md`

**优先级**：P0  
**定位**：回注主工作流的最重要摘要文件。

#### 必须包含的字段

- `Primary Root Cause`
- `Contributing Factors`
- `Top Evidence`
- `Confidence`
- `Need Defensive Fix`
- `Need Human Review`
- `Recommended Attachments`

#### 这个文件的作用

- 主工作流 `rca-report.md` 直接消费它
- 主工作流 `fix-design.md` 判断是否需要附录

---

## 4.6 参考知识文件

### 文件：`functionality-deep-dive/reference/environment-factor-thresholds.md`

**优先级**：P1  
**内容**

- Android / iOS 阈值表
- 时间精度降级策略

---

### 文件：`functionality-deep-dive/reference/analysis-strategies.md`

**优先级**：P2  
**内容**

- 状态拓扑策略
- 污点追踪策略
- 时序对齐策略
- 隔离诊断策略

---

### 文件：`functionality-deep-dive/reference/reasoning-chain.md`

**优先级**：P2  
**内容**

- 专项版 OVHSC 推理链
- 如何消费 topology / concurrency 两份重型产物

---

### 文件：`functionality-deep-dive/reference/platform-checklist.md`

**优先级**：P2  
**内容**

- Android / iOS 的功能疑难专项检查清单

---

### 文件：`functionality-deep-dive/reference/race-condition-patterns.md`

**优先级**：P2  
**内容**

- 常见协程竞态
- 生命周期竞态
- 缓存更新竞态

---

### 文件：`functionality-deep-dive/reference/state-machine-patterns.md`

**优先级**：P2  
**内容**

- 状态机常见异常模式
- 孤岛状态 / 非法跳转 / 缺守卫条件模式

---

## 五、与主工作流的对接清单

### 主工作流必须能给它什么

1. `issue-card.md`
2. `spec.md`
3. `context-bundle.md`
4. `specialized_workflow_mode = functionality-deep-dive`
5. 工作区路径

### 子工作流必须回给主工作流什么

1. `deep-dive-summary.md`
2. `functionality-deep-dive-rca.md`
3. 条件返回：
   - `defensive-fix-design.md`

### 主工作流如何消费

1. `p3-root-cause.md`
   - 读 `deep-dive-summary.md`
   - 生成标准 `rca-report.md`

2. `p4-fix-design.md`
   - 若存在 `defensive-fix-design.md`，作为附录输入

3. `p6-verification.md`
   - 验证状态机/竞态修复效果

---

## 六、MVP 实施建议

### 第一批必须落地

1. `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
2. `core/workflow.xml`
3. `core/workflow-model.yaml`
4. `core/workflow-status-template.yaml`
5. `core/default-config.yaml`
6. `phases/f1-context-reconstruction.md`
7. `phases/f2-state-topology.md`
8. `phases/f3-temporal-correlation.md`
9. `phases/f4-isolation-debate.md`
10. `templates/functionality-deep-dive-rca.md`
11. `templates/deep-dive-summary.md`

### 第二批建议同步做

12. `templates/environment-factor-report.md`
13. `templates/deep-dive-topology.md`
14. `templates/concurrency-analysis-report.md`
15. `agents/context-reconstructor.md`
16. `agents/state-analyst.md`
17. `agents/temporal-analyst.md`
18. `agents/challenger.md`
19. `agents/arbiter.md`
20. `reference/environment-factor-thresholds.md`

### 第三批增强项

21. `phases/f5-defensive-fix-design.md`
22. `templates/defensive-fix-design.md`
23. `agents/defensive-fix-architect.md`
24. 其余 `reference/*.md`

---

## 七、确认建议

你在确认这份清单时，建议重点看 4 个决策点：

1. `Functionality Deep-Dive` 是否只聚焦业务逻辑，不再混入 UI 疑难
2. `deep-dive-summary.md` 是否作为唯一回注主工作流的核心摘要
3. Stage 5 是否先作为 P1/P2 增强项，而不是首批必做
4. Agent 是否采用专项角色，而不是复用主工作流的 `investigator`

---

## 八、一句话总结

> **这份逐文件清单的核心，是先把 Functionality Deep-Dive 建成一条能独立完成“环境重构 -> 状态拓扑 -> 时序竞态 -> 对抗收敛 -> 回注主工作流”的完整专项分析链。**

