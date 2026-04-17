# Mobile QA Workflow 架构优化实施蓝图与代码施工文档

本文档基于《复杂问题归因优化整合方案》及其《深度审查报告》，结合 `mobile-qa-workflow` 当前工程目录结构，提供详尽的、可直接落地的代码修改与新增清单。本施工文档将所有功能和改造项转化为明确的研发任务。

---

## 1. 实施策略与分期里程碑

为控制工程风险并验证理论效果，落地分为三个阶段：

*   **P0-A (观测验证期 - 最小可行增量)**：仅增加边界判定元数据标注和 Intake 门禁。不修改现有 RCA 路由。验证判定算法的准确性。
*   **P0-B (核心重构期 - 路由生效)**：引入 Context Curator，重构 p2 时序（收集->策展->分级），正式将边界路由接入 p3 主流程，支持双层路由与策展回溯。
*   **P1 (高价值增强期)**：为 Challenger 增加时效与激活质疑，为 `VERSION_RANGE` 增加 Commit 排序模型，为 `HISTORICAL_UNCLEAR` 增加受控搜索协议。

---

## 2. 新增模块与组件规范 (New Files)

### 2.1 新增 Curator Agent 定义
*   **路径**: `agents/curator.md`
*   **内容要求**:
    *   **Role**: 上下文策展人，负责“让谁进入 RCA”，不做最终归因。
    *   **Capabilities**:
        1. 相似代码候选聚合与去重。
        2. 基于调用关系、日志做存活性校验。
        3. 基于配置快照、Feature Flag 做入口掩码（保守掩码策略）。
        4. 陈旧性识别（git blame）。
    *   **Constraints**: 禁止物理删除无法确认的上下文（必须保留但降级为 Suspect），必须输出结构化报告，误杀保护规则。
    *   **Output**: 严格输出 Markdown 格式的 `context-curation-report.md`。

### 2.2 新增策展报告模板
*   **路径**: `templates/context-curation-report.md`
*   **字段结构**:
    *   `candidate_contexts`: 原始候选
    *   `pruned_contexts`: 被剔除上下文（保留以备回溯）
    *   `keep_reasons` / `prune_reasons`: 审计理由
    *   `unresolved_noise`: 仍未判明的候选（标记为 Suspect）
    *   `curation_confidence`: 策展可信度评分 (>=0.7 正常进入，0.4-0.7 标记 `[Curation-Partial]`，<0.4 回退)

---

## 3. 核心机制改造 (Core Configurations)

### 3.1 核心路由与协议注册 (`core/core-rules.xml`)
*   **修改项**:
    *   在 `<available-agents>` 节点中注册 `<agent name="curator" scenario="策展">上下文净化、存活性校验、配置掩码</agent>`。

### 3.2 状态机重构 (`core/workflow.xml`)
*   **修改项**:
    *   在 `Spec-Defining` (p2) 阶段内新增子状态/中间状态：`Context-Curating`。
    *   在 `RCA-InProgress` (p3) 阶段新增边界精化循环路径：`RCA-InProgress -> Boundary-Refined -> RCA-InProgress`。

### 3.3 工作流状态元数据 (`core/workflow-status-template.yaml`)
*   **修改项**:
    *   新增字段：`Issue_Boundary_Level` (`EXACT_MR` | `VERSION_RANGE` | `HISTORICAL_UNCLEAR`)
    *   新增字段：`Boundary_Confidence` (High | Medium | Low)
    *   新增字段：`Runtime_Anchor_Availability` (Strong | Weak)

---

## 4. 阶段流程代码修改清单 (Phases)

### 4.1 P1 阶段 (`phases/p1-intake.md`)
*   **改造项**:
    *   **新增“问题边界判定与锚点盘点”步骤**。
    *   **定义决策算法**:
        *   有明确 MR/PR/提交 -> `EXACT_MR` (High)
        *   仅有版本起止点 -> `VERSION_RANGE` (宽度决定置信度)
        *   仅有“一直有问题”/历史问题 -> `HISTORICAL_UNCLEAR` (动态锚点决定置信度)
        *   冲突时取**最窄有效边界**为主选，次窄为备选。
    *   **Intake 门禁**: 当判定为 `HISTORICAL_UNCLEAR` 且动态锚点弱时，拒绝直接推入 RCA，强制触发 `Human-Review` 输出最小补证清单。

### 4.2 P2 阶段 (`phases/p2-spec-definition.md`)
*   **改造项**:
    *   **步骤重排（解决时序冲突）**:
        *   将原有的“证据收集与分级”拆分为三步：1. 搜集候选证据 -> 2. Context Curation (调用 Curator Agent 或单对话顺序执行) -> 3. 基于策展结果进行二维证据分级并生成 Context Bundle。
    *   **单对话降级支持**: 当 `env_subagent == false` 时，由主 Agent 顺序执行策展 Checklist，替代调用 Curator 子 Agent。

### 4.3 P3 阶段 (`phases/p3-root-cause.md`)
*   **改造项**:
    *   **双层路由接入**: 原有的 `fast | deep` 降为第二层。第一层依据 `Issue_Boundary_Level` 路由：
        *   `EXACT_MR` -> `Diff Focus Mode`
        *   `VERSION_RANGE` -> `Commit Denoising Mode`
        *   `HISTORICAL_UNCLEAR` -> `Dynamic Anchoring + Bottom-Up Mode`
    *   **双轨低成本验证**: 当 `Boundary_Confidence` 为 Low 时，对主/备选边界同时执行快速路径 (单视角 OVHSC)。一致则采信，不一致则升级人工复核。
    *   **边界回溯与精化**: 如果在推演阶段 (Verify) 发现更精确边界（如锁定了 MR），允许状态机流转回 `Boundary-Refined`，更新路由并重试。
    *   **策展回溯机制**: 当 Investigator 的所有假设均被证伪时，从 `pruned_contexts` 中恢复被 Curator 误杀的上下文重试。

### 4.4 修复与验证阶段 (`phases/p4-fix-design.md`, `p5-fix-impl.md`, `p6-verification.md`)
*   **改造项 (应对远端漂移)**:
    *   `p4-fix-design.md`: 修复策略池新增 `跨端协调/远端修复` (针对服务端契约变更、配置下发变更)。
    *   `p5-fix-impl.md`: 新增非代码修复分支，输出变更服务端配置或协调后端的具体指令。
    *   `p6-verification.md`: 针对远端变更增加相应的验证标准（不能仅靠本地代码走查）。

---

## 5. Agents 及推理策略改造 (Agents & Reference)

### 5.1 Challenger 增强 (`agents/challenger.md`)
*   **改造项**:
    *   将 5 维质疑扩展为“**核心 5 维 + 条件 2 维**”以控制成本：
        *   `Temporal Drift Challenge` (时间漂移): 仅在无近期代码变更或 `HISTORICAL_UNCLEAR` 时触发。质疑是否服务端/系统/依赖变更。
        *   `Activation Challenge` (激活质疑): 仅在存在 AB/Flag/配置代码时触发。质疑当前报错用户/设备是否真的激活了该分支。

### 5.2 证据模型升级 (`reference/reasoning-chain.md`)
*   **改造项**:
    *   **二维权重矩阵算法**: `Reliability(A/B/C) × Liveness(Live/Suspect/Dead)`
        *   `Dead`: 不参与正向得分，仅作为“已排除路径”标注。
        *   `Suspect`: 需附带升级为 `Live` 的条件说明，仅由 `Suspect` 支撑的假设置信度上限为 0.5。

### 5.3 搜索与排序策略 (`reference/analysis-strategies.md`)
*   **改造项**:
    *   **多信号 Commit 排序模型**: 针对 `VERSION_RANGE` 路由，定义 5 维信号打分（结构信号 30% > 动态 25% > 时序 20% > 文本 15% > 责任 10%）。
    *   **受控搜索三层协议**: 针对 `HISTORICAL_UNCLEAR` 路由：
        1. 锚点提取（从 Error/Log/UI 中提炼关键词）。
        2. 候选收集（每锚点限制最多 5 个候选）。
        3. 候选过滤（必须能与调用栈映射或 Flag 激活）。

---

## 6. 模板文件扩展 (Templates)

### 6.1 Issue Card (`templates/issue-card.md`)
*   新增区块记录边界判定结果：`Issue_Boundary_Level`, `Boundary_Confidence`, `Boundary_Evidence`, `Boundary_Alternative`。

### 6.2 Context Bundle (`templates/context-bundle.md`)
*   **新增元数据区块**:
    *   `Context_Noise_Risk`: 评估污染程度。
    *   `Config_Snapshot_Metadata`: 记录案发时的配置掩码理由 (`Mask_Decision_Reason` 为必填，其他尽力而为，取不到标 `[Unavailable]`)。
*   **新增版本对比清单模板** (专供 `VERSION_RANGE` 使用)：对比版本号、代码量、依赖和配置的差异。

### 6.3 Knowledge Card (`templates/knowledge-card.md`)
*   新增字段：`boundary_level`, `curation_patterns` (沉淀噪声模式), `routing_effectiveness`。为以后的边界路由提供历史经验基线。

---

## 7. 系统联调与同步 (System Prompt)

### 7.1 单对话降级模式 (Fallback Strategy)
由于在部分平台 (Web 纯 Chat) 无法支持并发子 Agent，必须在各环节提供内联降级：
*   **Curator 降级**: 在 p2 证据收集后，主 Agent 自行运行策展 Checklist。
*   **Challenger 降级**: 主 Agent 在单对话中必须在推演后强制插入一段 Self-Correction 提示词，自我拷问条件 2 维质疑。

### 7.2 System Prompt 同步 (`system-prompt.md`)
*   **实施要求**: `system-prompt.md` 包含全量内联逻辑，所有上述 1-6 的逻辑（二维证据权重表、三层路由、条件 2 维质疑、策展 Checklist、保守配置掩码原则）都必须在最终完成模块化修改后，手动同步到 `system-prompt.md` 中，并建议在 CI 流程中增加差异比对校验。

---
*本文档为 Mobile QA Workflow 架构优化的唯一执行标准，后续各文件的代码修改均须严格对齐本施工清单。*