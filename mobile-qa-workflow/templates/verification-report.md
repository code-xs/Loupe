# Verification Report 模板

```markdown
## Verification Report — {Issue-ID}

### 元信息
- **关联 Issue**: [Issue Card ID]
- **关联 Implementation Report**: [Implementation Report ID]
- **验证时间**: [时间戳]
- **验证结论**: [通过 / 未通过（需回退到 Phase 4）/ 部分通过（L3-Dynamic 待 CI 补充）]

---

### 契约溯源交叉验证结果

- **验证状态**: [PASS / WARNING / FAIL / SKIPPED]
- **修复路由**: [code-fix / non-code-fix]
- **溯源记录总数**: [N 条]
- **fix-design 跨模块引用数**: [M 处]
- **溯源覆盖率**: [N/M × 100%]

#### 逐条校验结果

| # | 溯源项 | 源文件 | 期望值 | 实际值 | 匹配状态 | 验证结果 |
|---|-------|--------|-------|-------|---------|---------|
| 1 | [API/资源描述] | [file:line] | [期望值] | [实际值] | [✅/❌/⚠️] | [PASS/MISMATCH/SUSPICIOUS] |
| 2 | ... | ... | ... | ... | ... | ... |

#### 异常等级说明
- **PASS**：所有溯源项匹配状态均为 ✅
- **WARNING**（SUSPICIOUS）：存在标记为「待确认」的项，但无明确不匹配
- **FAIL**（INSUFFICIENT）：溯源记录条数 < fix-design 跨模块引用数
- **FAIL**（MISMATCH）：存在期望值与实际值不匹配的项
- **FAIL**（MISSING）：溯源记录为空或关键字段缺失
- **SKIPPED**：Repair-Route = non-code-fix，无需溯源验证

#### 对 L1 结论的影响
- 契约溯源验证状态为 **FAIL** 时，L1 判定自动为 **未通过**
- 契约溯源验证状态为 **WARNING** 时，L1 可标记为 **部分通过（需人工确认溯源项）**
- 契约溯源验证状态为 **PASS** 或 **SKIPPED** 时，不影响 L1 判定

---

### L1: Spec 静态符合性验证

通过 AI 代码走查，对照 Spec Document 逐条验证修改后的代码逻辑：

| Spec 条目 | 验证方式 | 验证结果 | 证据（代码引用/逻辑推导） |
|-----------|---------|---------|----------------------|
| Expected Behavior 1: [描述] | [AI 代码走查] | [通过/未通过] | [file:line 代码引用 + 逻辑说明] |
| Expected Behavior 2: [描述] | ... | ... | ... |
| Invariant 1: [描述] | [静态不变量检查] | [维护/违反] | ... |
| Invariant 2: [描述] | ... | ... | ... |

---

### L2: 静态影响面 & 回归安全性验证

基于调用图分析修改函数的上下游影响，对照 Fix Design 回归测试设计：

| 验证项 | 验证方式 | 验证结果 | 备注 |
|-------|---------|---------|------|
| 直接影响模块: [模块名] | [Call Graph 分析 + 代码走查] | [通过/未通过] | |
| 间接影响模块: [模块名] | [静态调用链分析] | [通过/未通过] | |
| 关键不变量: [不变量描述] | [静态逻辑验证] | [维护/违反] | |
| 跨平台一致性(L1 视觉) | [双端代码对比] | [一致/有差异] | |
| 跨平台一致性(L2 行为) | [双端逻辑对比] | [一致/有差异] | |
| 跨平台一致性(L3 容错) | [双端异常处理对比] | [一致/有差异] | |

---

### L3: 发布质量验证

#### L3-Static（AI 静态完成）
| 质量维度 | 基线值 | 修复后值 | 判定 |
|---------|-------|---------|------|
| Lint Error 数 | [N 个] | [M 个] | [无新增/有新增] |
| Lint Warning 数 | [N 个] | [M 个] | [无新增/有新增，列出新增项] |
| API 版本合规 | [合规] | [合规/存在风险点] | [通过/需关注] |
| 静态安全扫描 | [N 个问题] | [M 个问题] | [无新增/有新增] |

#### L3-Dynamic（[Pending-CI] 需运行时环境补充，不阻塞当前验证流程）
| 质量维度 | 基线值 | 说明 |
|---------|-------|------|
| 相关功能 Crash Free Rate | [X%] | 需真机/CI 运行时数据，待发布后监控 |
| 关键链路性能(P95) | [Xms] | 需 Profiler/APM 工具，AI 无法静态获取 |
| 内存占用 | [XMB] | 需运行时 Heap Dump，AI 无法静态获取 |

> **说明**：L3-Dynamic 各项在当前 AI 静态分析阶段无法完成，标记为 `[Pending-CI]`。
> 这些指标应由 CI 流水线在部署后自动收集，或由开发人员在真机验证阶段补充填写。
> L3-Dynamic 的 `[Pending-CI]` 状态不阻塞问题进入闭环，但应在 Knowledge Card 中记录需 CI 回填。

---

### 中间态报告（v4.1 范围 — 始终物理存在；成功填 N/A，失败必填）

> **协议层现状声明（v4.1 / C9 方案 A）**：
> 当前 `<template-output>` 在 `core/core-rules.xml` 仅有 `file` / `template` 两个参数（无模式 / 变量绑定 / 条件块 / 分支渲染能力），P6 成功与失败路径调用同一模板，模板本身为静态 markdown。
> 因此 v4.1 范围**不能**实现"成功路径不渲染本段"的条件渲染；本段在所有验证场景下均会物理出现于生成的 verification-report.md。
> v4.1 取**方案 A**：三必填字段始终物理存在，**成功路径填标准 `N/A` 占位**、**失败路径必填实际内容**。"协议层条件渲染机制"（方案 B）作为 v4.2 遗留 #4 的 follow-up 候选（不在本 PR 范围）。
>
> **三必填字段**（缺一项视为 C9 校验失败 — 无论成功/失败场景；成功场景的 `N/A` 占位也算"已填"）：

- **failure_classification**: 失败分类
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须从以下集合中选择并填写：
    - `L1-Spec-Mismatch`：L1 Spec 静态符合性验证未通过
    - `L1-Contract-Trace-Fail`：契约溯源交叉验证 FAIL
    - `L2-Regression-Risk`：L2 静态影响面或回归测试设计未通过
    - `L3-Static-Lint-Regress`：L3-Static Lint / 安全扫描出现新增问题
    - `L3-Static-Api-Compat`：L3-Static API 版本合规出现风险
    - `Root-Cause-Not-Closed`：验证发现修复未真正闭合根因（建议回退到 Phase 3 重做 RCA）
    - `Other`：上述均不适用时使用，并在 evidence 字段补充说明
- **evidence**: 失败证据
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须包含：
    - 触发失败的具体验证项（引用 L1/L2/L3-Static 表格中的行）
    - 期望值与实际值的并列对照（若适用）
    - 关联代码位置（`file:line`）或日志锚点
- **repro_path**: 复现路径
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须包含：
    - 复现步骤（最小化序列）
    - 复现环境（平台 / 版本 / 配置 / 必要前置数据）
    - 期望复现结果（与 evidence 中"实际值"一致）

#### 中间态报告 Markdown 块（成功场景）

> 以下示例使用 `~~~markdown` 围栏以避免与外层 ```` ``` ```` 围栏冲突；实际生成时按内部内容原样填入即可。

~~~markdown
### 中间态报告

- **failure_classification**: N/A (verification passed)
- **evidence**: N/A (verification passed)
- **repro_path**: N/A (verification passed)
~~~

#### 中间态报告 Markdown 块（失败场景）

~~~markdown
### 中间态报告

- **failure_classification**: [L1-Spec-Mismatch / L1-Contract-Trace-Fail / L2-Regression-Risk / L3-Static-Lint-Regress / L3-Static-Api-Compat / Root-Cause-Not-Closed / Other]
- **evidence**:
  - [触发失败的验证项 + 期望/实际对照]
  - [关联代码位置 file:line 或日志锚点]
- **repro_path**:
  - [复现步骤]
  - [复现环境]
  - [期望复现结果]
~~~

> **与 PR-4 的协作**（主文档 §3 PR-4 v2.3 微调）：PR-4 在 `phases/p6-verification.md` 失败
> 分支已确保先调用 `<template-output file="…/verification-report.md" template="…/verification-report.md"/>`
> 再回流；成功分支同样调用同一模板。本 PR 不向 `<template-output>` 引入任何自定义模式属性
> （v1.0 子文档曾设计的 intermediate 模式取值已在 v2.3 微调撤销，避免与 `core/core-rules.xml`
> `<template-output>` DSL 漂移）。
> v4.1 不承诺"成功路径省略本段"的条件渲染语义；该能力归 v4.2 遗留 #4 候选（方案 B）。

---

### 验证总结
- **L1 通过**: [是/否]
- **契约溯源交叉验证**: [PASS/WARNING/FAIL/SKIPPED]
- **L2 通过**: [是/否]
- **L3-Static 通过**: [是/否]
- **L3-Dynamic 状态**: [Pending-CI]
- **总体判定**: [L1+L2+L3-Static 全部通过 → 进入闭环 / 未通过 → 回退到 Phase 4]
- **回退原因**（若未通过）: [具体说明哪层哪项未通过，以及建议的修复方向]

---

### Code Review Summary（无 Git 环境时输出，供人工创建 PR 时使用）
- **变更摘要**: [...]
- **Root Cause**: [...]
- **Fix Design**: [...]
- **验证结论**: [...]
```
