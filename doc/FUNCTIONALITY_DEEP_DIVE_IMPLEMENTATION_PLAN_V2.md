# Functionality Deep-Dive 子工作流 — 详细施工方案（V2，可落地版）

> **编制日期**：2026-04-16  
> **基于**：  
> - `doc/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_REVIEW_REPORT.md`（权威质检报告）  
> - `doc/FUNCTIONALITY_DEEP_DIVE_IMPLEMENTATION_PLAN.md`（V1 施工方案）  
> - `mobile-qa-workflow/` 现有编排器与阶段文件（工程实现事实源）  
> **目标**：把 Deep-Dive 从“设计正确但工程接不上”修到“在现有编排器语义下可被调度、可恢复、产物可消费”的状态。  
> **原则**：Deep-Dive 不是第 7 阶段、也不是新状态机；它是 **Phase 内增强分支**（P2/P3/P4 内部条件触发）。  

---

## 0. V2 关键修正（对应 P0/P1）

### 0.1 修正 P0：触发时序冲突（Step 4.5 放错位置）

**V1 问题**：把 Stage 2/3 放在 `P3 Step 4.5（双层路由之后）`，同时把“快速路径反事实校验失败”作为触发条件之一。但反事实校验失败发生在 `Step 5`，此时 `Step 4.5` 已经过了，导致最关键触发场景无法进入 Deep-Dive。

**V2 决策**：  
- `P3` 不再新增“Step 4.5（全局插入）”。  
- Stage 2/3 改为 **深度路径内部的前置增强块**：放在 `P3 Step 5` 的 `analysis_path == deep` 分支里，且要覆盖两类场景：  
  1. 一开始就被判定为深度路径（P0/P1 + medium/complex 等）。  
  2. 快速路径在 `Step 5` 内升级为深度路径（反事实失败后立即执行 Stage 2/3，再进入深度路径多视角分析）。

### 0.2 修正 P0：Deep-Dive-InProgress 状态不成立

**V1 问题**：试图在 `workflow.xml` 增加 `Deep-Dive-InProgress` 来恢复/续跑，但主编排器实际是按 `stepsCompleted + workflow-model.yaml` 计算下一阶段，不按 `current_state` 执行“同一 Phase 内子状态恢复”。因此新增该分支无法保证续跑语义，反而增加误导和状态分裂风险。

**V2 决策**：  
- **不新增** `current_state = Deep-Dive-InProgress`。  
- Deep-Dive 的恢复语义只通过 `workflow-status.yaml` 的 **元字段**表达（可选），并由 **P2/P3/P4 阶段文件自己识别**：  
  - 若对应产物已存在（如 `deep-dive-topology.md`），则“读取并复用”，避免重复消耗。  

### 0.3 修正 P1：多根因落地方式（与现有模板兼容）

**现状约束**：`templates/rca-report.md` 和 `p4-fix-design.md` 都是以“单根因 + 单因果链”为默认输入模型。强行改成 1-N 根因集合会对 P4/P5/P6 产生连锁改造。

**V2 决策（P1 级落地可控）**：  
- Deep-Dive 阶段允许输出“根因集合（1-N）”，但 `RCA 最终交付`仍保持：  
  - **Primary Root Cause（主根因）**：唯一、可修复、可验证。  
  - **Contributing Factors（贡献因子）**：0-N 个，明确关系（叠加/因果链上游/互斥分支）。  
- `P4` 评估矩阵变体仍可引入“架构鲁棒性提升”，但不强制要求 P4 能消费 N 个根因并生成 N 套方案；默认只对主根因设计方案，同时对贡献因子给防御性兜底/监控建议。

### 0.4 修正 P1：产物从“旁路文件”变成“主产物可消费的附件”

**V2 决策**：对三大主模板增加固定引用位（不改变主结构，只加“可选附件段落”）：  
- `templates/context-bundle.md`：新增 `Deep-Dive Attachments（可选）`，引用 `environment-factor-report.md`、`deep-dive-topology.md`。  
- `templates/rca-report.md`：新增 `Deep-Dive Findings（可选）`，引用 `concurrency-analysis-report.md`，并摘要化关键结论。  
- `templates/fix-design.md`：新增 `Defensive Addendum（可选）`，引用 `defensive-fix-design.md`。  

---

## 1. 施工范围总览（V2）

### 1.1 P0/P1 变更项清单（按落地优先级）

| 序号 | 变更项 | 类型 | 文件 | 优先级 |
|------|--------|------|------|--------|
| V2-W1 | 修正 Deep-Dive 触发与插入点（覆盖“快速路径升级”） | 修改 | `mobile-qa-workflow/phases/p3-root-cause.md` | P0 |
| V2-W2 | Stage 1 环境因子增强：改为 P2 内“机会性增强”，输出并入 Context Bundle | 修改 | `mobile-qa-workflow/phases/p2-spec-definition.md` | P0 |
| V2-W3 | 状态模板增加 Deep-Dive 元字段（仅用于复用/审计，不作为编排路由） | 修改 | `mobile-qa-workflow/core/workflow-status-template.yaml` | P0 |
| V2-W4 | 设计文档修正 P0 条款（100%复现/唯一根因/禁止关联代码） | 修改 | `mobile-qa-workflow/FUNCTIONALITY_DEEP_DIVE_WORKFLOW.md` | P0 |
| V2-W5 | 产物契约“可消费化”：主模板新增附件引用位 | 修改 | `mobile-qa-workflow/templates/context-bundle.md` 等 | P1 |
| V2-W6 | Agent 能力与质疑协议：以“条件触发扩展”融入现有角色，而非新增角色 | 修改 | `mobile-qa-workflow/agents/investigator.md`, `agents/challenger.md` | P1 |
| V2-W7 | P4 评估矩阵 Deep-Dive 变体（保留，但改为“仅 deep_dive_mode==true 且 defensive addendum 存在”时启用） | 修改 | `mobile-qa-workflow/phases/p4-fix-design.md` | P1 |
| V2-W8 | 新模板（Topology/Concurrency/DefensiveFix） | 新增 | `mobile-qa-workflow/templates/*.md` | P1 |
| V2-W9 | 新参考：环境因子阈值表（供 Stage 1 写报告时引用） | 新增 | `mobile-qa-workflow/reference/environment-factor-thresholds.md` | P1 |

> 说明：V2 **不要求**改 `core/workflow.xml` 的路由状态，也不引入新 phase。`io-contract` 的“conditional output”仅作为文档声明，工程上通过模板附件段落实现消费即可。

---

## 2. Deep-Dive 的 V2 嵌入模型（最终版）

### 2.1 P2（Stage 1）— 机会性增强，不切换 deep_dive_mode

- 触发：`主分类 == 功能` 且问题具备“偶发/并发/缓存一致性/生命周期耦合”任一特征（仅需从 Intake/Spec 侧可判断的信号）。  
- 动作：只做 **增量环境因子采集与关联**，产物写入 `{workspace_folder}/environment-factor-report.md`，并将摘要加入 `context-bundle.md` 的证据清单与附件引用段落。  
- 不在 P2 决定 `deep_dive_mode`，避免 P2 缺少 `complexity_level` 与反事实校验信号导致误触发/误路由。

### 2.2 P3（Stage 2/3/4）— 深度路径内部增强，覆盖“深度路径初始进入”和“快速路径升级”

- Deep-Dive 模式只在 `analysis_path == deep` 时激活。  
- 若 `analysis_path` 从 fast 升级为 deep（反事实失败），则在升级后 **立即执行** Stage 2/3，再进入多视角对抗。  
- Stage 4 不独立出流程，只作为 Challenger 的 **条件扩展维度**（C8/C9/C10）追加执行。

### 2.3 P4（Stage 5）— 防御性修复附录，不替代四重论证

- 仍执行现有四重论证与评估矩阵。  
- Deep-Dive 模式下：  
  - 可以输出 `defensive-fix-design.md` 作为 `fix-design.md` 的附录。  
  - 评估矩阵权重可启用 Deep-Dive 变体，但只在“确实存在防御性附录且涉及并发/状态机/缓存一致性”时启用，避免泛化到所有功能问题。

---

## 3. Phase 1（P0）施工详案

### V2-W1：修正 P3 触发与插入点（核心 P0）

**目标**：让 Deep-Dive Stage 2/3 能覆盖两类深度路径来源：  
- 初始深度路径（双层路由直接选 deep）。  
- 快速路径在 Step 5 内升级 deep（反事实失败）。

**文件**：`mobile-qa-workflow/phases/p3-root-cause.md`  

**改造要点（建议实现方式）**：
1. 在 `Step 4` 末尾只计算一个布尔值（不新增 Step 4.5）：  
   - `deep_dive_candidate = (主分类=='功能' && complexity_level=='complex' && 表现命中 {偶发/竞态/状态机/缓存一致性/系统底层栈疑似上层})`  
   - 注意：`快速路径反事实失败` 不在这里判断。
2. 在 `Step 5` 的 `analysis_path == deep` 分支内，在加载 `analysis-strategies.md` 之前插入：  
   - `if deep_dive_candidate == true then run Stage 2 + Stage 3`  
   - 若对应产物文件已存在（上一轮或人工补产物），则“读取并复用”，不重生成。
3. 在 `analysis_path == fast` 分支中，当发生 `反事实校验失败 → 升级到 deep` 时，紧跟着执行：  
   - `deep_dive_candidate` 若满足则执行 Stage 2/3，再进入 deep 分支逻辑。

**Stage 2/3 产物与注入**：  
- 输出：  
  - `{workspace_folder}/deep-dive-topology.md`（只含状态机拓扑 + 数据流污点追踪 + 不可变性审查，避免塞时序表）  
  - `{workspace_folder}/concurrency-analysis-report.md`（专注时序/竞态/隔离推演/复现概率与强制复现建议）  
- 注入：将两者的“关键结论摘要”追加到 `context-bundle.md` 的证据清单，并在模板新增段落中引用附件文件（见 V2-W5）。

### V2-W2：P2 增加 Stage 1（环境因子增强）但不切换 deep_dive_mode（核心 P0）

**文件**：`mobile-qa-workflow/phases/p2-spec-definition.md`  

**插入位置**：`Step 7（上下文策展）` 之后、`Step 8（二维证据分级）` 之前。  

**与 V1 的差异**：  
- V1 用 `deep_dive_stage = 1` 标记；V2 不做该标记，只产出报告并合入 Context Bundle。  
- V1 “严禁任何代码修复建议”在 Stage 1 过度约束；V2 允许“环境因子与代码位置关联”，但禁止“修复方案”。

**输出**：  
- `{workspace_folder}/environment-factor-report.md`  
- 在 `context-bundle.md` 增加：  
  - 证据清单新增条目（Reliability 通常为 B/C，按数据源可升级）。  
  - 附件引用段落指向文件路径。

### V2-W3：状态模板增加 Deep-Dive 元字段（核心 P0）

**文件**：`mobile-qa-workflow/core/workflow-status-template.yaml`  

**新增字段（放在 PRESERVE_FORMAT 区块末尾）**：
```yaml
deep_dive_mode: false            # 是否在 P3 深度路径中启用 Deep-Dive 增强
deep_dive_candidate: false       # 是否命中 Deep-Dive 候选（由 P3 双层路由输出，或由证据推断）
deep_dive_stage: null            # 仅用于审计：最后一次执行到 Stage(1-5) 的编号
deep_dive_artifacts: []          # 产物文件名列表（用于复用与审计）
```

> 约束：这些字段 **不参与** 主编排器路由（仍由 stepsCompleted 驱动），只用于阶段内复用与审计。

### V2-W4：修正文档的 4 个 P0 条款（与质检报告对齐）

**文件**：`mobile-qa-workflow/FUNCTIONALITY_DEEP_DIVE_WORKFLOW.md`  

**必须修正项**：  
1. Stage 3：`100% 复现脚本` → `高概率复现描述 + 复现概率估计 + 强制时序注入建议`  
2. Stage 4：`唯一根因` → `根因集合(1-N) + 关系类型`（但最终交付仍选主根因）  
3. Stage 1：`严禁任何修复建议` → `禁止修复方案，但允许关联到代码位置`  
4. Stage 2：`必须精确到行号` → `行号可不确定，标 [Line-Uncertain] 并说明依据`

---

## 4. Phase 2（P1）施工详案

### V2-W5：主模板新增“Deep-Dive 附件引用位”（产物可消费化）

**目标**：让 Deep-Dive 不再是旁路文件，保证下游阶段“看得见、用得上、可审计”。  

**文件与建议增量段落**：
1. `templates/context-bundle.md`：新增段落 `### Deep-Dive Attachments（可选）`  
   - `environment-factor-report.md`（如存在）  
   - `deep-dive-topology.md`（如存在）  
2. `templates/rca-report.md`：新增段落 `### Deep-Dive Findings（可选）`  
   - 引用 `concurrency-analysis-report.md`  
   - 摘要：竞态窗口、复现概率、强制复现注入点、缓存一致性结论  
3. `templates/fix-design.md`：新增段落 `### Defensive Addendum（可选）`  
   - 引用 `defensive-fix-design.md`  
   - 标注启用条件：仅 deep_dive_mode==true 且涉及并发/状态机/缓存一致性

### V2-W6：Agent 协议融入现有角色（不新增角色）

**文件**：  
- `agents/investigator.md`：新增 “Deep-Dive 增强能力（条件触发）” 与 “输出格式补丁段落”。  
- `agents/challenger.md`：新增 Deep-Dive 条件扩展维度 C8/C9/C10（生命周期盲区/内存泄露/缓存一致性），并修改 `M(5~7)` 为 `M(5~10)` 的描述。

**关键约束（保持与 core-rules.xml 一致）**：  
- 任何 Deep-Dive 输出仍必须遵循“证据来源必须来自 Context Bundle”原则。  
- Deep-Dive 的拓扑/时序结论属于“可审计推断”，必须把证据等级写清楚，避免“图画得很美但无证据”。

### V2-W7：P4 评估矩阵变体（Deep-Dive 条件启用）

**文件**：`phases/p4-fix-design.md`  

**启用条件（V2）**：  
- `deep_dive_mode == true` 且存在 `defensive-fix-design.md`（或修复方案明确属于防御性修复/架构加固）。  
- 否则仍使用标准矩阵，避免权重泛化污染。

**权重建议（沿用 V1 思路，但加启用条件）**：  
- 长期可维护性上调、变更最小性下调、新增架构鲁棒性维度。  

### V2-W8：新增三份模板（Topology/Concurrency/Defensive）

**新增文件**：  
- `templates/deep-dive-topology.md`  
- `templates/concurrency-analysis-report.md`  
- `templates/defensive-fix-design.md`

**V2 额外约束**：  
- `deep-dive-topology.md` 不再包含“时序对齐轴”（避免与 concurrency 报告重复）；时序内容统一写入 `concurrency-analysis-report.md`。  
- 所有 Mermaid 块必须给出一份最小可渲染示例，避免语法不一致导致不可读。

### V2-W9：新增环境因子阈值表（Stage 1 引用）

**新增文件**：`reference/environment-factor-thresholds.md`  
- 给出 Android/iOS 常见阈值与降级策略（微秒/毫秒/顺序对齐）。  

---

## 5. 验收标准（V2，P0/P1）

### 5.1 P0 验收（必须通过）

| 验收项 | 方法 | 通过标准 |
|--------|------|----------|
| 快速路径升级也能触发 Stage 2/3 | 构造一个 fast→deep 升级场景（反事实失败） | 升级后仍生成 `deep-dive-topology.md`/`concurrency-analysis-report.md` 或复用既有文件 |
| 不引入 Deep-Dive-InProgress 状态也能恢复 | 中断后重进对话恢复 | 通过“文件存在即复用 + workflow-status 元字段”保证不重复生成且可审计 |
| Stage 1 报告可进入 Context Bundle | 触发 P2 机会性增强 | `context-bundle.md` 中出现证据条目与附件引用 |
| 设计文档 P0 条款修正生效 | 审核文档条款 | 4 项 P0 修正全部落地 |

### 5.2 P1 验收（强烈建议通过）

| 验收项 | 方法 | 通过标准 |
|--------|------|----------|
| 主模板可消费 Deep-Dive 产物 | 生成一套 Deep-Dive 产物 | `context-bundle/rca-report/fix-design` 都有固定引用位 |
| Challenger 深度质疑维度条件触发 | deep_dive_mode==true | 输出包含 C8/C9/C10 且不破坏原 5+2 协议 |
| 多根因“主根因+贡献因子”可落地 | 模拟多根因案例 | `rca-report.md` 保持主根因唯一，同时列出贡献因子与关系 |

---

## 6. 实施建议（V2 的工程化优先序）

1. 先做 `V2-W1/W2/W3/W4`，确保“能触发、能跑通、能审计”。  
2. 再做 `V2-W5`，把产物消费打通，否则 Deep-Dive 价值难以沉淀到后续阶段。  
3. 最后做 `V2-W6/W7/W8/W9`，完善角色契约、评估矩阵与模板体系。

