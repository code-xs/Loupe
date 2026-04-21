# Mobile QA Workflow v4.2 — 施工总清单（OVERVIEW）

> **方案文档**：[`doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md)（含二次修订 / 4 条质检门槛接纳）
> **本目录性质**：v4.2 收敛方案的"主控施工单"。每个 PR 启动实施时，再在本目录追加 `pr-{N}-{slug}.md` 详细施工文档（参考 v2.2 体例）。
> **方案规模**：8 PR / 总工作量 ~10.6d（不含 PR-8 长期演进）/ 跨平台兼容性硬约束 / CI 4 件套兜底。

---

## 0. 立项前置条件（必须 100% 满足）

立项前必须验证以下 4 条质检接纳门槛（来源 V1.1 §4.1.0 + §3.2.10 末尾 + §3.2.21 末尾）：

| # | 门槛 | 验证方式 | Owner |
|---|------|---------|-------|
| G1 | V1.1 方案已 sign-off（含二次修订） | doc 文件已合入 main | 方案 owner |
| G2 | 执行引擎确认支持 LLM 自解释新 DSL 标签（无外部 parser 阻塞） | 已在 V1.1 §3.2.21 完成核查 | 平台 owner |
| G3 | ADR 目录基础设施就绪（`doc/adr/`）+ ADR-010 / ADR-021 文档草稿可在 PR-1 内随 O4+ 一并提交 | 目录创建 + 模板文件 | PR-1 owner |
| G4 | 跨平台回归基础设施（Cursor / Trae / Dify 三平台 eval-cases 跑通） | 现有 `eval-framework/` 已具备，无需额外搭建 | QA owner |

---

## 1. 8 PR 总览

| # | PR 名 | 包含 V1.1 项 | 工作量 | 风险 | 依赖前置 PR |
|---|------|-------------|--------|------|------------|
| PR-1 | **基础整改 + ADR 化 + CI 4 件套首批** | O1 + O2 + O3 + O4+ + O5(部分) + O6 + O22(部分) | 0.9d | 极低 | — |
| PR-2 | **同步债清理 + system-prompt 生成器交付（不替换文件）+ state 字段瘦身** | O5(配套校验) + O7 + O8 + O9 + O17+(生成器实现) | 2.2d | 低 | PR-1 |
| PR-3 | **phase 出口宏标签** | O21 + O22(`check-phase-abort-structure.sh`) | 1.0d | 中 | PR-1（ADR-021）+ PR-2（不依赖运行时但需 CI 基础设施） |
| PR-4 | **D14 收口 #1：Spec-Uncertain 契约统一** | O13a | 0.5d | 中（用户可见行为变化） | PR-2 |
| PR-5 | **D14 收口 #2：step-pause registry 数据化** | O10+ + O22(`check-step-pause-registry.sh`) | 0.6d | 中 | PR-4 |
| PR-6 | **D14 收口 #3：phase 内联删除 + Fix-Confirming + system-prompt 首次构建** | O13 + O14 + O12 + 触发 PR-2 留下的 system-prompt.md 自动构建替换（解 H1） | 1.4d | 中 | PR-3 + PR-5 |
| PR-7 | **结构收敛 + Token 优化 + 模块化** | O15 + O16 + O11+ + O19+ + O23 + O24 + O25 | 2.5d | 中 | PR-6（O15 改写依赖 O21 宏可用） |
| PR-8 | **长期演进（v4.3 主体规划）** | O20 | 5d+ | 高 | PR-7（不在 v4.2 范围） |

**v4.2 范围**：PR-1 ~ PR-7（≈10.6d），PR-8 单独立项 v4.3。

---

## 2. 跨 PR 依赖关系图

```
PR-1 (基础整改 + ADR + CI 首批)
   │
   ├──> PR-2 (同步债 + 生成器交付 + state 瘦身)
   │      │
   │      ├──> PR-3 (phase 出口宏标签)  [B2.5 隔离]
   │      │      │
   │      │      └──> PR-6 (D14 收口 #3)
   │      │             ▲
   │      └──> PR-4 (D14 #1: Spec-Uncertain 契约)
   │             │
   │             └──> PR-5 (D14 #2: registry 数据化)
   │                    │
   │                    └──> PR-6 (D14 #3: 内联删除 + Fix-Confirming + system-prompt 首次构建)
   │                           │
   │                           └──> PR-7 (结构收敛 + Token + 模块化)
   │                                  │
   │                                  └──> PR-8 (v4.3 长期演进)
```

**关键路径**（最长串行链）：PR-1 → PR-2 → PR-4 → PR-5 → PR-6 → PR-7 = **7.1d**（PR-3 可与 PR-4/5 并行，不在关键路径上）。

---

## 3. 跨 PR 硬依赖与降级路径（来源 V1.1 §4.1.0）

### Hard Dependency 1（H1）：system-prompt 首次构建延迟到 PR-6

- **PR-2** 只交付 O17+ 生成器实现（脚本 + 单元测试），**不**首次构建并替换 `system-prompt.md`
- **PR-6** 内 O13a 已合入（PR-4 完成）后，才执行首次构建并替换
- **CI 守门**：`check-build-system-prompt-precondition.sh` 在 PR-2 合入时启用，验证 system-prompt.md 中 Spec-Uncertain 段落 `allowed_values` 必须为 `1|2|S` 而非 `Confirm`，否则 CI 红

### Hard Dependency 2（H2）：PR-3 失败时 PR-4/5/6 的降级路径

- **触发条件**：PR-3 合入后，前 5 个使用宏标签的子 PR 抽查 LLM 执行记录发现：
  - 展开不一致率 > 10%，或
  - `check-phase-abort-structure.sh` 持续误报阻塞合入，或
  - Limited 平台小 LLM 漏展开率 > 5%
- **降级动作**：
  - PR-6 中 O13/O14 改写**回退到原"5 步咒语"写法**（不阻塞 D14 收口）
  - O21 推迟到 v4.3 评估
  - V1.1 §5 量化对比表中"Phase 早退 ABORT 点平均行数"与"B1\* 类 bug 再现概率"两行收益降级为 0
  - **不允许**反向阻塞：PR-3 验收失败不得阻止 PR-4/5/6 进入实施

### Hard Dependency 3（H3）：PR-4 / PR-5 / PR-6 严格串行

- **禁止**在同一 PR 中并行 O13a / O10+ / O13 / O14
- 每个 PR 合入后必须**单独跑 eval-cases 全量回归 + 跨平台 4 类验收**
- 原因（V1.1 §4.1）：
  - O13a 改契约语义（Cursor 用户立刻看到选项变化）
  - O10+ 把 case switch 转为 registry，依赖 O13a 已统一
  - O13 删 phase 内联，依赖 O13a 统一 + O10+ 注册表就绪
  - O14 引入 `Fix-Confirming` + 删 allowlist，依赖前序全部就绪

### Hard Dependency 4（H4）：ADR 必须先于代码 PR

- **ADR-021**（`<phase-abort>` 宏标签）+ **ADR-010**（step-pause-registry）作为 PR-1 的 O4+ 范围交付物，**先于** PR-3 / PR-5 任何代码改动
- ADR-021 首段必须显式区分 `<phase-abort>` 宏标签与 v2.2 PR-4 文档名 `phase-abort-fanout-isolation` 的差异（见 V1.1 §3.2.21 末尾"命名冲突规避"）

---

## 4. CI 守门启用时间表（O22 4 + 2 件套）

| 脚本 | 启用 PR | 默认严重度 | 说明 |
|------|---------|------------|------|
| `check-state-enum.sh` | PR-1 | error | V1 O5 配套，state 枚举漂移守门 |
| `check-system-prompt-sync.sh` | PR-1 | warning（PR-1）→ error（PR-2 合入后） | system-prompt.md 与 core/ 同步守门；PR-2 生成器交付前先 warning |
| `check-io-contract.sh` | PR-1 | error | I/O 契约守门 |
| `check-subagent-params.sh` | PR-1 | error | SubAgent 参数守门 |
| `check-build-system-prompt-precondition.sh` | PR-2 | error | H1 守门：Spec-Uncertain 契约必须为 `1|2|S` |
| `check-phase-abort-structure.sh` | PR-3 | warning（PR-3）→ error（PR-6 合入后） | phase 出口规范性守门；PR-3 合入初期允许 warning 用于人工抽查 |
| `check-step-pause-registry.sh` | PR-5 | error | Registry 三类校验（含**硬编码 case 禁出**） |

**总计 7 个 CI 脚本**，全部纳入 `.github/workflows/qa-workflow-schema-check.yml`，PR 合入门禁。

---

## 5. 跨平台回归矩阵（每 PR 必跑）

| PR | Cursor / Claude Code（Full）| Trae（Full）| Dify / Coze（Limited）| 单 prompt LLM（Minimal）|
|----|------|------|------|------|
| PR-1 | eval-cases 全量 | eval-cases 全量 | 抽 1 用例 | 抽 1 用例 |
| PR-2 | eval-cases 全量 + 生成器单测 | eval-cases 全量 | **eval-cases 全量**（O7/O8 state 瘦身需双侧验证）| 抽 1 用例 |
| PR-3 | eval-cases 全量 + 人工抽查 LLM 记录 ≥ 10 例 | eval-cases 全量 + 人工抽查 ≥ 5 例 | **人工抽查 ≥ 5 例**（小 LLM 宏展开重点验证）| 抽 1 用例 + 人工 |
| PR-4 | **eval-cases 全量 + 人工 Spec-Uncertain 弹窗 ≥ 3 例**（用户可见行为变化）| eval-cases 全量 | **eval-cases 全量 + 人工抽查**（双侧弹窗选项必须一致）| 抽 1 用例 |
| PR-5 | eval-cases 全量 + 新增 stop_state demo case | eval-cases 全量 | eval-cases 全量 | 抽 1 用例 |
| PR-6 | eval-cases 全量 + 5+ Spec-Uncertain/Fix-Confirming 用例 | eval-cases 全量 | **eval-cases 全量 + 5+ 用例**（删 phase 内联后 Limited 平台是高风险点）| 抽 1 用例 |
| PR-7 | eval-cases 全量 + token 实测 | eval-cases 全量 + token 实测 | eval-cases 全量 + token 实测 | **token 实测重点**（小 LLM 受益最大） |

**通用门禁**（来源 V1.1 §4.2）：
1. `eval-framework/artifact_checker.py` 全量通过
2. `eval-cases/seed-10` 上 chains A/B 的 `mean_score` 不降（容许 ± 5% 抖动），零分 case 不增
3. 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

---

## 6. PR 详细信息

### PR-1 · 基础整改 + ADR 化 + CI 4 件套首批

- **包含**：O1（doc 整理）+ O2（命名规范）+ O3（legacy deep-dive 归档）+ O4+（ADR 化 + ~165 行散布注释外迁）+ O5(部分: 2 个 sync 脚本)+ O6 + O22(部分: 4 个 CI 脚本)
- **新增文件**：`doc/adr/` 目录 + ADR-001 ~ ADR-019（散布注释外迁）+ ADR-010 草稿 + ADR-021 草稿 + 4 个 CI 脚本
- **删除文件**：无（O3 是归档不是删除）
- **关键约束**：
  - O3 必须按"归档 + deprecated 标记 + 老会话回放兼容"，**禁止物理删除**（V1.1 §3.1 / F2 finding）
  - ADR-021 首段必须显式区分宏标签与 v2.2 PR-4 子命题名
- **DoD**：grep 验证文档归档 + ADR 目录建立 + 4 个 CI 脚本绿 + 老会话 v3-legacy 回放 1 例
- **回滚**：单 PR 回滚（无运行时变更，零阻塞影响）

### PR-2 · 同步债清理 + system-prompt 生成器交付 + state 字段瘦身

- **包含**：O5(配套校验脚本)+ O7（current_state 收敛）+ O8（field 瘦身）+ O9（注释级整理）+ O17+(生成器实现 + 单测，**不**替换 system-prompt.md)
- **关键约束**：
  - O17+ 生成器**只交付脚本 + 单测**，PR-2 合入后 system-prompt.md 文件**不变**
  - `check-build-system-prompt-precondition.sh` 在本 PR 启用为 error，强制 system-prompt.md 中 Spec-Uncertain `allowed_values` 必须为 `1|2|S`（即不允许此 PR 内即兴构建）
  - `check-system-prompt-sync.sh` 升级为 error
- **DoD**：sync 脚本通过 + Limited 平台抽 1 case 验证 + 生成器单测 100% + system-prompt.md **未被本 PR 修改**
- **回滚**：单 PR 回滚（state 瘦身可逐字段回退）

### PR-3 · phase 出口宏标签（B2.5 隔离）

- **包含**：O21（`<phase-abort>` / `<phase-complete>` 宏定义 + 全 phase 改写）+ O22(`check-phase-abort-structure.sh`)
- **关键约束**（V1.1 §3.2.21 H1/H2/H3）：
  - **H1**：`core/core-rules.xml` `<supported-tags>` 内显式定义两个新 `<tag>` 块（含 `<rule>` 4 步展开规则 + `<params>` 必填校验）
  - **H2**：`system-prompt.md`（PR-6 首次构建后才生效，本 PR 先在源 doc 中放置）置顶位置写入完整展开规则——不只是引用
  - **H3**：本 PR 合入后，**前 5 个使用宏标签的 PR 强制人工抽查 LLM 执行记录 ≥ 10 例**
  - `check-phase-abort-structure.sh` 默认 warning，PR-6 合入后升级 error
- **DoD**：所有 phase 文件出口已用宏标签 + CI 结构校验绿 + 人工抽查首批 ≥ 10 例正确展开
- **回滚 / 降级**：见 §3 H2

### PR-4 · D14 收口 #1：Spec-Uncertain 契约统一（O13a）

- **包含**：O13a（`Spec-Uncertain` 回复契约统一为 `1|2|S` 三选）
- **关键约束**：
  - 本 PR 是 **Cursor 平台用户可见行为变化**——Spec-Uncertain 弹窗选项变化
  - **必须**先于 PR-5 合入；**禁止**与 PR-5 / PR-6 合并
  - 本 PR 合入后才能解除 PR-2 留下的 `check-build-system-prompt-precondition.sh` 守门（实际在 PR-6 内完成 system-prompt.md 替换）
- **DoD**：Cursor + Dify 双侧 Spec-Uncertain 弹窗选项完全一致 + 人工抽查 ≥ 3 例
- **回滚**：单 PR 回滚到契约旧值

### PR-5 · D14 收口 #2：step-pause registry 数据化（O10+）

- **包含**：O10+（step-pause-registry.yaml + 编排器 step 4 拆 4a/4b/4c）+ O22(`check-step-pause-registry.sh`)
- **关键约束**（V1.1 §3.2.10 末尾 / H3 接纳）：
  - O10+ 落地后编排器 `core/workflow.xml` step 4 内**严格禁止**任何硬编码 case 分支
  - `check-step-pause-registry.sh` 三类校验：
    1. registry 状态名必须在 enum 内
    2. 编排器实际触发 step-pause 的所有路径上的 `current_state` 必须在 registry 中有对应条目
    3. **硬编码 case 禁出**（grep 任何 `<switch case="<交互态>">` 必须返回零匹配）
- **DoD**：3 类 CI 校验全绿 + 新增 stop_state demo case（验证只改 registry 即可生效）
- **回滚**：registry 与编排器 step 4 同时回退

### PR-6 · D14 收口 #3：phase 内联删除 + Fix-Confirming + system-prompt 首次构建

- **包含**：O13（删 phase 内联 step-pause）+ O14（引入 `Fix-Confirming` enum + 删 `legacy-phase-step-pause-allowlist.txt`）+ O12（白名单文件删除）+ **触发 PR-2 留下的 system-prompt.md 首次自动构建并替换**（解 H1）
- **关键约束**：
  - O13 / O14 改写时**强烈推荐使用 PR-3 的 `<phase-abort>` 宏**（如 PR-3 已降级，则回退到 5 步咒语写法）
  - 本 PR 合入后 `check-phase-abort-structure.sh` 由 warning 升级为 error
  - system-prompt.md 首次构建后必须人工 diff 通过
- **DoD**：step-pause 不重复弹窗 + Cursor + Dify 双侧一致 + `legacy-phase-step-pause-allowlist.txt` 已删除 + system-prompt.md 自动构建产物人工 diff 通过 + 5+ Spec-Uncertain/Fix-Confirming 用例 OK
- **回滚**：rollback 链 = O14 → O13 → 重建 system-prompt.md → 恢复 allowlist

### PR-7 · 结构收敛 + Token 优化 + 模块化

- **包含**：O15（子工作流收敛）+ O16（结构收敛）+ O11+（invoke-subagent boilerplate + coder-agent 拆三件 + shared-input-guard 提取）+ O19+（wrapper 整合 + shared-input-guard）+ O23（core-rules.xml 拆 essential + dsl-reference）+ O24（reasoning-chain 按 4 类拆分）+ O25（SubAgent 专用 core-rules-subagent.xml）
- **关键约束**：
  - O15 改写依赖 O21 宏可用（如 PR-3 已降级则回退）
  - O11+ 拆 coder-agent 时必须保留 `coder-agent.md` 入口文件（Limited 平台单 prompt 注入需要）
  - Token 实测必须覆盖 3 类 LLM（Claude / Qwen / Doubao），P3 complex 路径下降 ≥ 25%
- **DoD**：3 平台手动验证（Cursor + Trae + 选 1 Limited）+ P5/P6 调用路径正确 + Token 实测达标
- **回滚**：模块化改动可逐子项回退

### PR-8 · 长期演进（O20，单独立项 v4.3）

- 本 PR 不在 v4.2 范围；v4.2 收尾后单独立项

---

## 7. 时间轴建议（关键路径 ~7.1d，含并行）

```
Day 0      Day 1      Day 2      Day 3      Day 4      Day 5      Day 6      Day 7
 │          │          │          │          │          │          │          │
 ├─PR-1(0.9d)
 │          ├─PR-2(2.2d)──────────┤
 │                                ├─PR-3(1.0d)──┤  (并行)
 │                                ├─PR-4(0.5d)─┤
 │                                              ├─PR-5(0.6d)──┤
 │                                                            ├─PR-6(1.4d)──────┤
 │                                                                              ├─PR-7(2.5d)──────────┤
```

- **关键路径**：PR-1 → PR-2 → PR-4 → PR-5 → PR-6 → PR-7 = **7.2d**
- **并行机会**：PR-3 与 PR-4 可并行（PR-3 不依赖 PR-4 的契约改动；PR-3 仅依赖 PR-1 的 ADR-021）
- **总人天**：10.6d（含并行后压缩到 ~8d 实际工期）
- **建议节奏**：1 PR / 周（含 review / 回归 / 跨平台验证缓冲），v4.2 全量收口约 **7-8 周**

---

## 8. PR 详细施工文档生成约定

每个 PR 启动实施时，在本目录追加 `pr-{N}-{slug}.md`，参考 v2.2 体例：

- PR-1 → `pr-1-foundation-cleanup-and-ci-bootstrap.md`（**v1.0 / 已 superseded** — 含 review 阻断标注）+ `pr-1-foundation-cleanup-and-ci-bootstrap-v1.1.md`（**当前生效** — 修订 review 4 项 Patch 块）+ `pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md`（v1.0 评审报告 / 2 阻断 + 3 高优）
- PR-2 → `pr-2-sync-debt-and-system-prompt-generator.md`
- PR-3 → `pr-3-phase-exit-macro-tags.md`
- PR-4 → `pr-4-d14-spec-uncertain-contract-unification.md`
- PR-5 → `pr-5-d14-step-pause-registry.md`
- PR-6 → `pr-6-d14-inline-removal-and-system-prompt-rebuild.md`
- PR-7 → `pr-7-structural-convergence-token-and-modularization.md`

**子文档骨架**（同 v2.2/README §"子文档骨架"）：

```
# PR-{N} · {名称}

> 主控文档：./README.md
> 方案依赖：V1.1 §3.2.{xx} + §4.1 批次 B{x}

## 1. PR 元信息（分支 / Base / Reviewer / 关联 V1.1 项 / 工作量 / 涉及文件）
## 2. 文件级 diff 列表（每文件：修改类型 / V1.1 锚点 / 原文 / 新文 / 修订理由 / 兼容性影响）
## 3. PR-level DoD（链接到 V1.1 §4.2 + 本主控 §5 跨平台矩阵）
## 4. PR-level 回滚动作
## 5. 静态契约校验自检（本 PR 视角，链接 §4 CI 守门表）
```

**约定**（同 v2.2 README）：
- 跨 PR 横切契约（V1.1 §3 各 O 项 / §4.2 DoD / §5 量化目标 / §7 回滚）只在 V1.1 与本主控维护，子文档**链接而非复述**
- 行号锚点使用 `startLine:endLine:filepath` 三段式
- 子文档展开前**重新对齐 main 行号**

---

## 9. v4.2 收口 / 验收

v4.2 收口判定（PR-1 ~ PR-7 全部合入后）：

1. **结构指标**：V1.1 §5 量化对比表所有"目标行数 / token / 文件数"指标达成
2. **行为指标**：eval-cases seed-10 chains A/B mean_score 不降，零分 case 不增
3. **跨平台指标**：Cursor + Trae + Dify 三平台 eval-cases 全量通过；Spec-Uncertain / Fix-Confirming 弹窗选项 100% 一致
4. **CI 指标**：7 个 CI 脚本全部 error 级运行，main 分支零失败
5. **文档指标**：ADR 目录 ≥ 21 个 ADR 文件；V1.1 / 本主控 / 各 PR 子文档锚点全部有效

收口后冻结 v4.2 baseline，PR-8（O20）启动 v4.3 立项。

---

## 10. 修订日志

- **2026-04-21**：初版（基于 V1.1 §4.1 / §4.1.0 / §3.2.10 / §3.2.21 推导）。8 PR 方案 = V1.1 原 12 批次的"温和合并"档（A 档），关键路径 7.2d / 总工期 ~8 周。
