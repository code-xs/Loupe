# Deep-Dive V3 拆解清单

> **目标**：把 `DEEP_DIVE_WORKFLOW_V3_ARCHITECTURE_PROPOSAL.md` 进一步拆成可执行层面的两部分：  
> 1. 主工作流需要修改哪些点  
> 2. 两个独立子工作流分别需要哪些文件  
>  
> **范围**：  
> - 主工作流改造点  
> - `Functionality Deep-Dive` 子工作流文件清单  
> - `UI Deep-Dive` 子工作流文件清单  

---

## 一、主工作流改造点

### 1.1 改造目标

主工作流在 V3 中不再承担复杂疑难问题的深度分析本体，而是承担以下职责：

1. 继续完成标准 Intake / Spec / 基础 RCA 分诊
2. 判断是否应进入专项子工作流
3. 路由到 `Functionality Deep-Dive` 或 `UI Deep-Dive`
4. 接收子工作流返回结果
5. 将子工作流结论回注到主产物
6. 驱动后续 `Fix Design / Fix Impl / Verification`

---

### 1.2 主工作流必须修改的文件

| 文件 | 是否必须修改 | 作用 |
|------|--------------|------|
| `mobile-qa-workflow/core/workflow.xml` | 是 | 增加专项子工作流路由与回注控制 |
| `mobile-qa-workflow/core/workflow-status-template.yaml` | 是 | 增加专项子工作流状态字段 |
| `mobile-qa-workflow/core/default-config.yaml` | 是 | 增加专项产物路径字段 |
| `mobile-qa-workflow/phases/p3-root-cause.md` | 是 | 增加专项分诊逻辑，触发子工作流 |
| `mobile-qa-workflow/phases/p4-fix-design.md` | 是 | 消费专项附录产物 |
| `mobile-qa-workflow/phases/p6-verification.md` | 建议 | 增加专项修复验证要求 |
| `mobile-qa-workflow/templates/context-bundle.md` | 是 | 增加专项分析输入引用 |
| `mobile-qa-workflow/templates/rca-report.md` | 是 | 增加专项 RCA 回注区 |
| `mobile-qa-workflow/templates/fix-design.md` | 是 | 增加专项修复附录区 |
| `mobile-qa-workflow/system-prompt.md` | 后置同步 | 把 V3 内联到纯 Prompt 版本 |

---

### 1.3 `core/workflow.xml` 改造点

#### 需要新增的能力

1. **专项路由节点**
   - 在 `qa-root-cause` 阶段内部或其前置路由处，增加：
     - `standard-rca`
     - `functionality-deep-dive`
     - `ui-deep-dive`

2. **子工作流执行节点**
   - 当命中专项路由时，调用对应子工作流入口，而不是继续执行标准深度 RCA。

3. **回注节点**
   - 子工作流完成后，读取其 `summary` 产物
   - 将结果映射回主工作流 `rca-report.md`

4. **失败处理节点**
   - 子工作流失败 / 未收敛 / 产物缺失时，进入：
     - `Human-Review`
     - 或回退标准 RCA

#### 建议新增状态字段使用方式

在主状态机层面可新增：

```yaml
specialized_workflow_mode: null
specialized_workflow_status: null
specialized_artifacts: []
```

语义建议：

- `specialized_workflow_mode`
  - `null`
  - `functionality-deep-dive`
  - `ui-deep-dive`
- `specialized_workflow_status`
  - `pending`
  - `running`
  - `completed`
  - `failed`

---

### 1.4 `core/workflow-status-template.yaml` 改造点

#### 新增字段

建议在保留区追加：

```yaml
specialized_workflow_mode: null
specialized_workflow_status: null
specialized_artifacts: []
specialized_last_summary: null
```

#### 字段职责

- `specialized_workflow_mode`：当前进入了哪个专项工作流
- `specialized_workflow_status`：专项子工作流执行状态
- `specialized_artifacts`：专项产物列表
- `specialized_last_summary`：回注摘要文件路径

---

### 1.5 `core/default-config.yaml` 改造点

#### 新增产物路径字段

建议增加：

```yaml
output_specialized_summary: null
output_functionality_deep_dive_rca: null
output_functionality_defensive_fix: null
output_ui_deep_dive_rca: null
output_ui_fix_addendum: null
```

#### 作用

- 让主工作流后续阶段能通过统一配置拿到专项产物位置
- 避免专项产物只在子工作流内部可见

---

### 1.6 `phases/p3-root-cause.md` 改造点

这是主工作流里最关键的改造文件。

#### 新增内容

1. **专项分诊判定**
   - 在复杂度评估之后，新增一层专项路由：
     - 标准 RCA
     - Functionality Deep-Dive
     - UI Deep-Dive

2. **Functionality Deep-Dive 触发规则**
   - 主分类=功能
   - `complexity_level in {medium, complex}`
   - 且命中：
     - 偶发性
     - 状态机异常
     - 并发/竞态
     - 缓存一致性
     - 生命周期耦合
     - 多模块业务联动

3. **UI Deep-Dive 触发规则**
   - 主分类=UI/UX
   - `complexity_level in {medium, complex}`
   - 且命中：
     - 偶发布局异常
     - 渲染时序异常
     - 异步重排
     - 约束冲突
     - 手势/滚动冲突
     - 适配矩阵问题

4. **调用子工作流**
   - 当命中专项路由时：
     - 更新 `specialized_workflow_mode`
     - 更新 `specialized_workflow_status = running`
     - 调用对应专项工作流

5. **接收 summary**
   - 若子工作流成功：
     - 读取 `deep-dive-summary.md` 或 `ui-deep-dive-summary.md`
     - 生成标准 `rca-report.md`
   - 若失败：
     - 标记 `specialized_workflow_status = failed`
     - 进入 `Human-Review`

---

### 1.7 `templates/context-bundle.md` 改造点

#### 需要新增一个段落

```markdown
### Specialized Workflow Inputs（可选）
- **专项模式**: [functionality-deep-dive / ui-deep-dive / none]
- **专项触发依据**: [简述]
- **补充输入清单**:
  - [APM / Layout Inspector / View Hierarchy / 约束导出 / 时序日志 / Feature Flag 快照]
```

#### 作用

- 明确主工作流向子工作流传了什么
- 方便后续审计“为什么进入了专项分析”

---

### 1.8 `templates/rca-report.md` 改造点

#### 需要新增一个专项回注段落

```markdown
### Specialized Deep-Dive Summary（可选）
- **专项模式**: [functionality-deep-dive / ui-deep-dive]
- **专项总结文件**: [路径]
- **Primary Root Cause**: [...]
- **Contributing Factors**: [...]
- **专项关键证据摘要**: [...]
- **是否建议附录修复方案**: [是/否]
```

#### 作用

- 标准 RCA 仍然存在
- 但其核心结论可来自专项子工作流

---

### 1.9 `templates/fix-design.md` 改造点

#### 需要新增一个专项附录段落

```markdown
### Specialized Fix Addendum（可选）
- **专项模式**: [functionality-deep-dive / ui-deep-dive]
- **附录文件**: [defensive-fix-design.md / ui-fix-design-addendum.md]
- **附录作用**: [防御性修复 / UI 专项修复]
- **是否纳入主方案**: [是/否]
```

---

### 1.10 `phases/p4-fix-design.md` 改造点

#### 需要新增的能力

1. 如果存在 `defensive-fix-design.md`
   - 将其作为功能疑难问题的附录输入

2. 如果存在 `ui-fix-design-addendum.md`
   - 将其作为 UI 疑难问题的附录输入

3. 评估矩阵需要根据专项模式切换
   - 功能疑难：允许“架构鲁棒性提升”
   - UI 疑难：增加“适配矩阵覆盖度”“渲染时序稳定性”维度

---

### 1.11 `phases/p6-verification.md` 改造点

#### 建议新增专项验证要求

1. 功能疑难专项验证
   - 状态机修复后是否消除非法跳转
   - 时序修复后是否关闭竞态窗口
   - 防御性熔断是否可用

2. UI 疑难专项验证
   - 适配矩阵回归
   - 布局树稳定性
   - 渲染时序回归
   - 手势/滚动冲突回归

---

## 二、Functionality Deep-Dive 子工作流文件清单

### 2.1 建议目录结构

```text
mobile-qa-workflow/
  functionality-deep-dive/
    core/
    phases/
    agents/
    templates/
    reference/
    FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md
```

---

### 2.2 核心文件清单

#### A. 入口与核心编排

1. `functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
   - 子工作流总说明
   - 阶段定义
   - I/O 契约
   - 与主工作流的集成关系

2. `functionality-deep-dive/core/workflow.xml`
   - 子工作流主编排器
   - 阶段路由与恢复

3. `functionality-deep-dive/core/workflow-model.yaml`
   - F1 ~ F5 阶段序列

4. `functionality-deep-dive/core/workflow-status-template.yaml`
   - 子工作流状态模板

5. `functionality-deep-dive/core/default-config.yaml`
   - 子工作流默认配置

---

#### B. 阶段文件

1. `functionality-deep-dive/phases/f1-context-reconstruction.md`
   - 环境与上下文重构
   - 极端环境因子、生命周期、系统干预

2. `functionality-deep-dive/phases/f2-state-topology.md`
   - 状态机拓扑
   - 数据流污点追踪
   - 不可变性审查

3. `functionality-deep-dive/phases/f3-temporal-correlation.md`
   - 时序对齐
   - 并发漏洞扫描
   - 复现概率分析

4. `functionality-deep-dive/phases/f4-isolation-debate.md`
   - 逻辑隔离诊断
   - 多 Agent 对抗
   - 主根因 / 贡献因子归并

5. `functionality-deep-dive/phases/f5-defensive-fix-design.md`
   - 防御性修复与架构演进建议
   - 附录修复方案输出

---

#### C. Agent 文件

1. `functionality-deep-dive/agents/context-reconstructor.md`
   - 环境重构专家

2. `functionality-deep-dive/agents/state-analyst.md`
   - 状态机与数据流分析专家

3. `functionality-deep-dive/agents/temporal-analyst.md`
   - 时序与竞态分析专家

4. `functionality-deep-dive/agents/challenger.md`
   - 功能疑难专项质疑员

5. `functionality-deep-dive/agents/arbiter.md`
   - 专项仲裁员

6. `functionality-deep-dive/agents/defensive-fix-architect.md`
   - 防御性修复设计专家

---

#### D. 模板文件

1. `functionality-deep-dive/templates/environment-factor-report.md`
2. `functionality-deep-dive/templates/deep-dive-topology.md`
3. `functionality-deep-dive/templates/concurrency-analysis-report.md`
4. `functionality-deep-dive/templates/functionality-deep-dive-rca.md`
5. `functionality-deep-dive/templates/defensive-fix-design.md`
6. `functionality-deep-dive/templates/deep-dive-summary.md`

---

#### E. 参考知识文件

1. `functionality-deep-dive/reference/environment-factor-thresholds.md`
2. `functionality-deep-dive/reference/analysis-strategies.md`
3. `functionality-deep-dive/reference/reasoning-chain.md`
4. `functionality-deep-dive/reference/platform-checklist.md`
5. `functionality-deep-dive/reference/race-condition-patterns.md`
6. `functionality-deep-dive/reference/state-machine-patterns.md`

---

### 2.3 Functionality 子工作流最小必需文件集

如果要先做 MVP，最少先落这些文件：

1. `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
2. `core/workflow.xml`
3. `core/workflow-model.yaml`
4. `phases/f1-context-reconstruction.md`
5. `phases/f2-state-topology.md`
6. `phases/f3-temporal-correlation.md`
7. `phases/f4-isolation-debate.md`
8. `templates/deep-dive-summary.md`
9. `templates/functionality-deep-dive-rca.md`

---

## 三、UI Deep-Dive 子工作流文件清单

### 3.1 建议目录结构

```text
mobile-qa-workflow/
  ui-deep-dive/
    core/
    phases/
    agents/
    templates/
    reference/
    UI_DEEP_DIVE_WORKFLOW_V3.md
```

---

### 3.2 核心文件清单

#### A. 入口与核心编排

1. `ui-deep-dive/UI_DEEP_DIVE_WORKFLOW_V3.md`
   - 子工作流总说明
   - 阶段定义
   - I/O 契约
   - 与主工作流集成方式

2. `ui-deep-dive/core/workflow.xml`
   - UI 专项子工作流编排器

3. `ui-deep-dive/core/workflow-model.yaml`
   - U1 ~ U5 阶段序列

4. `ui-deep-dive/core/workflow-status-template.yaml`
   - UI 子工作流状态模板

5. `ui-deep-dive/core/default-config.yaml`
   - UI 子工作流默认配置

---

#### B. 阶段文件

1. `ui-deep-dive/phases/u1-context-matrix.md`
   - 视觉上下文与适配矩阵重构

2. `ui-deep-dive/phases/u2-layout-topology.md`
   - 布局树与约束系统还原

3. `ui-deep-dive/phases/u3-render-timeline.md`
   - 渲染时序与异步重排剖析

4. `ui-deep-dive/phases/u4-interaction-debate.md`
   - 手势/滚动/动画冲突与多 Agent 对抗

5. `ui-deep-dive/phases/u5-ui-fix-design.md`
   - UI 修复设计与防回归方案

---

#### C. Agent 文件

1. `ui-deep-dive/agents/ui-context-analyst.md`
   - 适配矩阵与视觉上下文专家

2. `ui-deep-dive/agents/layout-analyst.md`
   - 布局树与约束分析专家

3. `ui-deep-dive/agents/render-timing-analyst.md`
   - 渲染时序专家

4. `ui-deep-dive/agents/gesture-interaction-analyst.md`
   - 手势与交互冲突分析专家

5. `ui-deep-dive/agents/challenger.md`
   - UI 专项质疑员

6. `ui-deep-dive/agents/arbiter.md`
   - UI 专项仲裁员

7. `ui-deep-dive/agents/ui-fix-architect.md`
   - UI 修复设计专家

---

#### D. 模板文件

1. `ui-deep-dive/templates/ui-context-matrix-report.md`
2. `ui-deep-dive/templates/layout-topology-report.md`
3. `ui-deep-dive/templates/render-timeline-report.md`
4. `ui-deep-dive/templates/ui-deep-dive-rca.md`
5. `ui-deep-dive/templates/ui-fix-design-addendum.md`
6. `ui-deep-dive/templates/ui-deep-dive-summary.md`

---

#### E. 参考知识文件

1. `ui-deep-dive/reference/ui-adaptation-matrix.md`
2. `ui-deep-dive/reference/layout-debug-strategies.md`
3. `ui-deep-dive/reference/render-timing-patterns.md`
4. `ui-deep-dive/reference/gesture-conflict-patterns.md`
5. `ui-deep-dive/reference/platform-ui-checklist.md`
6. `ui-deep-dive/reference/ui-regression-test-patterns.md`

---

### 3.3 UI 子工作流最小必需文件集

如果先做 MVP，最少先落这些文件：

1. `UI_DEEP_DIVE_WORKFLOW_V3.md`
2. `core/workflow.xml`
3. `core/workflow-model.yaml`
4. `phases/u1-context-matrix.md`
5. `phases/u2-layout-topology.md`
6. `phases/u3-render-timeline.md`
7. `phases/u4-interaction-debate.md`
8. `templates/ui-deep-dive-summary.md`
9. `templates/ui-deep-dive-rca.md`

---

## 四、V3 建议实施顺序

### Phase A：主工作流先具备专项路由能力

优先改：

1. `core/workflow.xml`
2. `core/workflow-status-template.yaml`
3. `core/default-config.yaml`
4. `phases/p3-root-cause.md`
5. `templates/context-bundle.md`
6. `templates/rca-report.md`

### Phase B：先落 Functionality Deep-Dive

原因：

- 和现有积累最接近
- 业务逻辑疑难收益最高

### Phase C：再落 UI Deep-Dive

原因：

- UI 体系更独立
- 适合后续专项建设

### Phase D：最后打通 P4 / P6

完成：

1. `fix-design.md` 消费专项附录
2. `p4-fix-design.md` 切换专项评估矩阵
3. `p6-verification.md` 增加专项回归验证

---

## 五、最终建议

### 5.1 主工作流层面最关键的改造点

如果只看“架构成败”，最关键的是这 3 个：

1. `p3-root-cause.md` 必须具备专项分诊能力
2. `workflow.xml` 必须支持调用独立子工作流并回注
3. `rca-report.md` / `fix-design.md` 必须能消费专项产物

### 5.2 两个子工作流的建设优先级

建议优先级：

1. `Functionality Deep-Dive`
2. `UI Deep-Dive`

### 5.3 一句话总结

> **V3 的关键不是把 Deep-Dive 写成一份更复杂的文档，而是让主工作流真正学会“分诊、调用专项子工作流、再把专项结论带回主闭环”。**

