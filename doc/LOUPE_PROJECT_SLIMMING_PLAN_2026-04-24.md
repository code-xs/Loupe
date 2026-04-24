# Loupe B2C Workflow 工程瘦身方案

> **日期**：2026-04-24
> **范围**：全工程全模块分析，覆盖 doc/、eval-cases/、eval-framework/、mobile-qa-workflow/ 及其所有子目录
> **目标**：大幅精简冗繁提示词、历史文档、废弃逻辑和不必要的测试/占位文件，同时确保工作流核心能力不受损

---

## 一、全局统计与瘦身预期

| 指标 | 当前 | 瘦身后（预估） | 缩减 |
|------|------|---------------|------|
| 文件总数 | ~210+ | ~110 | **-100+ 文件 (~48%)** |
| doc/ 顶层文档 | 33 | 6 | -27 |
| archive/ + construction-plans/ | 53 | 0 | -53 |
| 占位/空文件 | 20+ | 0 | -20 |
| 审计/施工文档（移出运行时目录） | 2 | 0（移入 doc/） | -2 |
| 估算总字符数缩减 | — | — | **~150 万字符 (80%+)** |

---

## 二、分模块瘦身方案

### 2.1 doc/ 目录（33 个顶层文档 + 22 个 ADR）

#### P0 - 可直接删除的历史文档（27 个，约 ~383K 字符）

这些文件是已完成的一次性审查报告、QA 报告、施工清单、PR 描述，其核心结论已被后续版本或代码实现吸收，保留价值为零。

**历史审查/QA 报告（18 个）**：

| 文件 | 大小(字符) | 删除理由 |
|------|-----------|---------|
| `B2C_WORKFLOW_ARCHITECTURE_REVIEW_2026-04-18.md` | 4,931 | 结论已被后续优化方案吸收 |
| `B2C_WORKFLOW_COMPREHENSIVE_REVIEW_2026-04-18.md` | 19,193 | 与 RIGOROUS_ANALYSIS 严重重叠 |
| `B2C_WORKFLOW_RIGOROUS_ANALYSIS_REPORT_2026-04-18.md` | 19,040 | 开篇即说明是前两份的交叉验证 |
| `B2C_WORKFLOW_CODER_SUBAGENT_QA_REPORT_2026-04-17.md` | 13,318 | Coder SubAgent 已落地，判断过时 |
| `B2C_WORKFLOW_SUBAGENT_SPLIT_REVIEW_2026-04-18.md` | 13,520 | 结论已被 FINAL_ADOPTION 采纳 |
| `CODER_SUBAGENT_V3_QA_REPORT_2026-04-17.md` | 6,102 | 已被 V3.1 取代 |
| `CODER_SUBAGENT_V3_1_IMPLEMENTATION_AND_CONSTRUCTION_QA_REPORT_2026-04-17.md` | 9,415 | 4 个 finding 已全部解决 |
| `CODER_SUBAGENT_V2_1_MUST_FIX_CHECKLIST_2026-04-17.md` | 9,376 | 指出的问题在 V3/V3.1 中已全部修正 |
| `CODER_SUBAGENT_CONSTRUCTION_PLAN_V1_1_REVIEW_2026-04-17.md` | 3,986 | 残留问题已被后续版本修正 |
| `CODER_SUBAGENT_FIX_COMPARISON_REPORT_2026-04-18.md` | 4,721 | 已完成的变更日志 |
| `LOUPE_CONSTRUCTION_PLAN_V1_1_QA_REPORT.md` | 2,096 | 指出的高危问题在 V1.2 中已解决 |
| `LOUPE_CONSTRUCTION_PLAN_V1_2_QA_REPORT.md` | 1,229 | 仅 28 行纯确认性文档 |
| `LOUPE_EVAL_SYSTEM_REVIEW_REPORT.md` | 3,599 | 评估已完成落地 |
| `LOUPE_TEST_RUNNER_FINAL_REVIEW.md` | 2,975 | Test Runner 已落地 |
| `LOUPE_MACRO_WORKFLOW_EVAL_PROPOSAL.md` | 3,091 | 已被 Test Runner 方案取代 |
| `Loupe_V1.2_Code_Review_Report.md` | 4,001 | V1.2 代码 review 已完成 |
| `MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_REVIEW_2026-04-21.md` | 13,660 | 审查 finding 已被 V1 版本吸收 |
| `B2C_WORKFLOW_BATCH_ABC_PR_DESCRIPTION_2026-04-18.md` | 6,496 | PR 已合入 |

**历史施工清单/建设计划（7 个）**：

| 文件 | 大小(字符) | 删除理由 |
|------|-----------|---------|
| `B2C_WORKFLOW_SUBAGENT_BATCH_A0_EXEC_TASKS_2026-04-18.md` | 7,861 | 已完成施工 |
| `B2C_WORKFLOW_SUBAGENT_BATCH_A0_FILE_PLAN_2026-04-18.md` | 9,238 | 已完成施工 |
| `B2C_WORKFLOW_SUBAGENT_BATCH_ABC_EXEC_TASKS_2026-04-18.md` | 12,468 | 已完成施工 |
| `B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md` | 16,017 | 已完成施工 |
| `B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md` | 3,562 | 架构决策已落地 |
| `FUNCTIONALITY_DEEP_DIVE_V3_FILE_CHECKLIST.md` | 11,713 | 逐文件实施清单已完成 |
| `DEEP_DIVE_WORKFLOW_V3_BREAKDOWN.md` | 10,605 | V3 拆解已完成 |

**历史版本（V0/V1 被 V1.1 完全取代，2 个）**：

| 文件 | 大小(字符) | 删除理由 |
|------|-----------|---------|
| `MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_2026-04-21.md` | 35,377 | V0 版，已被 V1 取代 |
| `MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1_2026-04-21.md` | 44,109 | V1 版，已被 V1.1 完整取代 |

#### P1 - 建议移入 doc/archive/ 归档（3 个）

| 文件 | 归档理由 |
|------|---------|
| `DEEP_DIVE_WORKFLOW_V3_ARCHITECTURE_PROPOSAL.md` | 架构设计理念有参考价值 |
| `coder-workflow-design.md` | Coder Agent 原始设计文档 |
| `UI_DEEP_DIVE_REMOVAL_IMPLEMENTATION_PLAN_2026-04-18.md` | "删能力"范式方法论有参考价值 |

#### 保留（3 个顶层 + 22 个 ADR）

- `LOUPE_WORKFLOW_SLIMMING_ASSESSMENT_2026-04-22.md` — 当前权威瘦身评估
- `MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md` — 当前主控优化方案（建议精简：82K 字符过大）
- `LOUPE_B2C_WORKFLOW_ARCH_OPTIMIZATION_2026-04-21.md` — eval-framework 架构优化参考
- **22 个 ADR 全部保留** — 结构化决策记录，价值密度最高

---

### 2.2 mobile-qa-workflow/archive/ + construction-plans/（53 个文件）

#### P0 - 整体删除

| 目录 | 文件数 | 删除理由 |
|------|--------|---------|
| `archive/v4.1-history/` | 15 | 纯历史审计/施工计划的多版本迭代，零运行时引用 |
| `construction-plans/v2.2/` | 19 | PR1-PR8 施工计划 + REVIEW，已全部落地 |
| `construction-plans/v4.2/` | 19 | PR1-PR7 施工计划 + REVIEW，已全部落地 |

**关键依据**：Grep 全局搜索确认，core/、phases/、agents/、reference/、scripts/ 中没有任何 `<load>`、`import`、`source` 指向这两个目录。Git 历史已保留完整演进记录。

---

### 2.3 mobile-qa-workflow/ 顶层审计文档（2 个，1437 行）

#### P0 - 移出运行时目录

| 文件 | 行数 | 操作 |
|------|------|------|
| `QUALITY-AUDIT-REPORT-v1.2.1.md` | 625 | 移入 `doc/` 目录 |
| `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` | 812 | 移入 `doc/` 目录 |

**理由**：这两个文件是工程管理文档，不是工作流运行时文件，不应被 Skill 安装分发，更不应被 LLM 加载到上下文中。移入 `doc/` 后同时精简内容：
- 三轮修订摘要堆叠 → 仅保留最新版
- 版本变更日志 → 独立或删除
- 预计各缩减约 100 行

---

### 2.4 eval-cases/seed-10/（占位文件清理）

#### P0 - 删除占位 README 文件（20 个）

所有 10 个 case 的以下文件为纯占位符，实际代码和日志已内嵌在 `issue-description.md` 中：
- `input/code-snapshot/README.md` × 10
- `input/logs/README.md` × 10

同时可删除对应的空目录 `code-snapshot/` 和 `logs/`（如果只包含 README）。

**10 个 eval case 本身质量高**（覆盖 Simple/Medium/Complex/Extreme 四档难度，7 种问题类型），应全部保留核心文件（metadata.yaml、issue-description.md、ground-truth/*）。

---

### 2.5 eval-framework/（代码治理）

#### P1 - 清理编译缓存

| 操作 | 说明 |
|------|------|
| 删除 `__pycache__/` 目录（2 处） | `eval-framework/__pycache__/` 和 `eval-framework/tests/__pycache__/` |
| 添加到 `.gitignore` | 确保不再提交编译缓存 |

#### P2 - 配置冗余收敛

`configs/eval-config.yaml` 中已定义 `execution_profiles`（pr_quick/nightly/weekly/monthly），而 `configs/nightly-full.yaml`、`configs/monthly-compare.yaml`、`configs/pr-quick.yaml` 是三个更详细的独立配置。存在信息分散问题。

**建议**：统一为一个配置入口。方案 A：将 configs/ 下三文件的额外配置合并回 eval-config.yaml 的 profiles 中，删除独立文件。方案 B：eval-config.yaml 的 profiles 改为引用 configs/ 下的文件。

#### P2 - 代码质量修复

| 问题 | 影响范围 | 修复方案 |
|------|---------|---------|
| import 路径不一致（`from session_manager` vs `from .session_manager`） | coordinator.py, iteration_loop.py 等 | 统一为包内相对导入 |
| 权重默认值三处硬编码 | scoring-rubric-base.yaml, judge.py, scoring_engine.py | 统一由 YAML 文件提供 |
| `_estimate_agent_count` 和 `_collect_runtime_metrics` 重复实现 | judge.py, coordinator.py | 提取到公共模块 |

---

### 2.6 mobile-qa-workflow/scripts/（迁移脚本清理）

#### P1 - 删除一次性迁移脚本

| 文件 | 行数 | 删除理由 |
|------|------|---------|
| `migrate-workflow-status-v3-to-v4.py` | 272 | v3→v4 一次性迁移脚本，若所有工作区已迁移则无用。也可移除 ruamel.yaml 依赖 |

**前提**：确认无存量 v3 schema 工作区。

**活跃脚本全部保留**：3 个 Python 构建/聚合工具 + 11 个 Shell CI 检查脚本 + 4 个测试文件，均为 CI 守门必需。

---

### 2.7 mobile-qa-workflow/core/（提示词精简）

#### P1 - core-rules-dsl-reference.xml 退役内容清理（约 25 行）

| 清理项 | 行数 | 说明 |
|--------|------|------|
| 5 个已退役 deep-dive agent 声明 | ~10 | 仅保留活跃 agent |
| 已退役 inline step-pause 参数说明 | ~15 | registry 形态已取代 inline 形态 |

core-rules.xml（自动生成产物）会随之自动缩减。

#### P1 - workflow-status-template.yaml 注释精简（约 30 行）

| 清理项 | 行数 | 说明 |
|--------|------|------|
| 废弃字段删除注释（fanout_mode 等） | ~13 | 缩减为 1 行指向 ADR-007 |
| 各字段历史修订注释 | ~17 | 移入变更日志，仅保留语义说明 |

#### P2 - core-rules-subagent.xml 注释压缩（约 20 行）

顶部 30 行注释可压缩为 10 行。

#### P2 - config-schema.yaml 清理（约 5 行）

删除底部空的 `known_legacy_aliases` dict 和历史映射注释。

---

### 2.8 mobile-qa-workflow/phases/（提示词精简）

#### P2 - p2-spec-definition.md 历史注释缩减（约 20 行）

- Non-Bug 早退说明（14 行纯注释）→ 压缩为 3 行 + ADR 引用
- curation_confidence 三分支说明 → 压缩

#### 注意：P3/P4 的 invoke-subagent 重复是 DSL 结构性限制

P3 root-cause.md（255 行）和 P4 fix-design.md（150 行）中三档 fan-out 的 invoke-subagent 调用存在大量 `<load>` 指令重复（约 80 行/文件），但**当前 DSL 不支持 load 指令模板化**，无法在不改 DSL 的前提下削减。标记为长期优化项。

---

### 2.9 mobile-qa-workflow/agents/（消除双写）

#### P2 - coder-workflow.md Error Dump 模板内联消除（约 38 行）

`coder-workflow.md` 第 138-176 行内嵌的 Error Dump 模板与 `templates/error-dump.md` **逐字相同**。改为 `<load target="templates/error-dump.md">` 引用，消除双写。

---

### 2.10 mobile-qa-workflow/system-prompt.md（自动生成产物优化）

#### P1 - 通过优化生成脚本缩减 system-prompt（约 140 行）

当前 532 行，是最长的单文件。优化方向：

| 优化项 | 预估缩减 | 说明 |
|--------|---------|------|
| L2 各阶段概览压缩 | ~60 行 | 仅列阶段名称，不列全部 step 目标 |
| L4 平台检查清单评估 | ~80 行 | Android/iOS 50 项 checkbox 是否需要全文嵌入到 system-prompt 值得商榷 |

**修改点在 `scripts/build-system-prompt.py`**，system-prompt.md 本身是生成产物不应手改。

---

### 2.11 mobile-qa-workflow/PLATFORM-GUIDE.md + SKILL.md（去重）

#### P2 - 消除三文件重叠

SKILL.md / system-prompt.md / PLATFORM-GUIDE.md 三文件在角色口径、状态枚举、持久化字段、运行时恢复协议等内容上存在重叠。

**建议**：以 `workflow-status-template.yaml` 为唯一权威源，PLATFORM-GUIDE.md 中与 SKILL.md 重叠的内容（约 15 行）改为引用而非复制。

---

### 2.12 mobile-qa-workflow/functionality-deep-dive/（子工作流精简）

#### P2 - archive/v3-legacy/ 条件删除（5 个文件，~200 行）

按 `agents/README.md` 记录的三项前提条件执行：
1. 所有持久化会话 `schema_version >= 4`
2. 90 天内零 v3-legacy 流量
3. 无残留 `<load target="archive/v3-legacy/...">` 引用

**建议**：在 v4.3 立项时统一清理。当前存储成本极低（~200 行），不值得冒兼容性风险。

#### P2 - 顶层文件名修正

`FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md` → 重命名为 `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V4.md`（内容已是 V4 复合角色架构）。

#### 评估结论：模块整体不冗余

27 个文件（活跃 22 + 归档 5），总计约 1500 行。角色-阶段-参考-模板四层分离设计合理，4 个 reference 按阶段选择性加载节省上下文窗口，6 个模板有明确的强制/按需/条件分层。与父级工作流松耦合（P3 触发、summary 回注）。**不建议进一步拆解或合并**。

---

### 2.13 mobile-qa-workflow/reference/（评估结论：不裁剪）

- `reasoning-chain-core.md`（源文件）+ 4 个 `reasoning-guide-*.md`（源文件）→ 聚合生成 `reasoning-chain.md`（产物）：**设计性分层，不冗余**
- 4 个 guide 各约 35 行，按分类选择性加载可节省 75% 的 guide 内容
- `analysis-strategies.md`、`fix-strategies.md`、`contract-checklist-spec.md`、`platform-checklist.md`：各有独立职责，无裁剪空间

---

### 2.14 mobile-qa-workflow/templates/（评估结论：不裁剪）

13 个模板全部被 P1-P6 + 闭环知识沉淀引用，无冗余。`intake-form.md`（Agent 侧）和 `intake-form-blank.md`（用户侧）面向不同受众，均需保留。

---

### 2.15 install_trae.sh shim 清理

#### P2 - 确认迁移完成后删除

`install_trae.sh`（6 行）已是纯 shim，仅转发到 `install.sh --target=trae`。按 v4.2 遗留 #5 计划，用户迁移完成后可删除。

---

### 2.16 .github/workflows/（保持现状）

`eval.yml` 和 `qa-workflow-schema-check.yml` 是活跃 CI 配置，不裁剪。

---

## 三、优先级执行矩阵

| 优先级 | 操作 | 影响文件数 | 估算缩减 | 风险 |
|--------|------|-----------|---------|------|
| **P0** | 删除 doc/ 27 个历史文档 | 27 | ~383K 字符 | 无（Git 已保留） |
| **P0** | 删除 archive/ + construction-plans/ | 53 | ~112 万字符 | 无（零运行时引用） |
| **P0** | 删除 eval-cases 20 个占位 README | 20 | ~2K 字符 | 无 |
| **P0** | 移出 2 个审计文档到 doc/ | 2 | 运行时 -1437 行 | 无 |
| **P1** | 清理 __pycache__ + .gitignore | 2 目录 | 编译缓存 | 无 |
| **P1** | 删除迁移脚本 | 1 | 272 行 | 需确认无 v3 工作区 |
| **P1** | core-rules 退役内容清理 | 2 | ~25 行 prompt | 无 |
| **P1** | workflow-status-template 注释精简 | 1 | ~30 行 | 无 |
| **P1** | system-prompt 生成逻辑优化 | 1 (脚本) | ~140 行 prompt | 需验证 Limited 平台兼容性 |
| **P2** | coder-workflow.md 双写消除 | 1 | ~38 行 | 无 |
| **P2** | p2-spec-definition 注释压缩 | 1 | ~20 行 | 无 |
| **P2** | PLATFORM-GUIDE / SKILL.md 去重 | 2 | ~15 行 | 无 |
| **P2** | eval-framework 配置收敛 | 3-4 | 信息分散修复 | 低 |
| **P2** | eval-framework import 修复 | 5+ | 代码质量 | 低 |
| **P2** | install_trae.sh 删除 | 1 | 6 行 | 需确认迁移完成 |
| **P2** | deep-dive v3-legacy 清理 | 5 | ~200 行 | 需满足三项前提 |
| **长期** | DSL 模板化减少 invoke-subagent 重复 | P3/P4 | ~160 行 prompt | 需 DSL 层改造 |

---

## 四、不建议裁剪的模块（重要说明）

以下模块经深度分析确认结构合理、无冗余，不应裁剪：

| 模块 | 理由 |
|------|------|
| **22 个 ADR (doc/adr/)** | 结构化决策记录，价值密度最高的文档资产 |
| **10 个 eval case** | 真实测试用例，覆盖 4 档难度 7 种问题类型 |
| **12 个 eval-framework Python 模块** | 全部有实质实现，非 stub |
| **13 个 templates/** | 全部被 P1-P6 引用，无冗余 |
| **10 个 reference/ 文件** | 分层聚合设计合理，按需加载节省 token |
| **11 个 CI check 脚本** | 全部是活跃守门脚本 |
| **6 个 phases/ 文件** | 核心工作流阶段定义 |
| **10 个 agents/ 文件** | shared-base + wrapper 分层设计合理 |
| **functionality-deep-dive/ 活跃文件（22 个）** | 松耦合子工作流，四层分离设计合理 |
| **core-rules 四文件分层架构** | essential + dsl-reference → 聚合产物，subagent 独立裁剪 |
| **reasoning-chain 分层架构** | core + 4 guides → 聚合产物，选择性加载设计优良 |

---

## 五、执行建议

### 第一阶段（P0，立即执行，预计缩减 80%+ 体积）

1. 批量删除 doc/ 下 27 个历史文档
2. 整体删除 `mobile-qa-workflow/archive/` 和 `mobile-qa-workflow/construction-plans/` 两个目录
3. 删除 eval-cases 下 20 个占位 README
4. 将 `QUALITY-AUDIT-REPORT-v1.2.1.md` 和 `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 移入 `doc/`
5. 将 doc/ 下 3 个有参考价值的历史文档移入 `doc/archive/`

### 第二阶段（P1，短期执行，核心提示词精简）

6. 清理 `__pycache__`，更新 `.gitignore`
7. 删除迁移脚本（确认无 v3 工作区后）
8. 清理 core-rules-dsl-reference.xml 中退役 agent 和 inline 参数（~25 行）
9. 精简 workflow-status-template.yaml 注释（~30 行）
10. 优化 build-system-prompt.py 生成逻辑，缩减 system-prompt.md（~140 行）

### 第三阶段（P2，优化完善）

11. coder-workflow.md Error Dump 改为引用
12. p2-spec-definition.md 历史注释压缩
13. PLATFORM-GUIDE.md / SKILL.md 去重
14. eval-framework 配置收敛和代码修复
15. install_trae.sh 清理
16. deep-dive v3-legacy 条件清理

### 长期规划

17. DSL 层支持 load 指令模板化，减少 P3/P4 的 invoke-subagent 结构性重复
18. `MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1` 精简（82K 字符过大）
