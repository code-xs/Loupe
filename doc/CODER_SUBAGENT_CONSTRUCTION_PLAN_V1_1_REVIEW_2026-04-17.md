# Coder SubAgent 施工方案 V1.1 复审报告

- 评审对象: 更新版施工方案 `https://bytedance.larkoffice.com/docx/D1esdOTZIo6zBVxn2fLc8VrGnqb`
- 评审时间: 2026-04-17
- 评审范围: 仅审查施工方案本身及其与当前仓库/当前环境的适配性, 不修改代码

## 1. 结论

更新版 V1.1 已经**有效修复了上一轮指出的 4 个问题的大部分主体缺陷**:

- F1: 已补 `Schema 兼容策略`
- F2: 已补 `Step 6 失败分支终止意图`
- F3: 已补 `元信息字段标准化解析函数`
- F4: 已将镜像同步从单点后置改为三次检查点

但复审后确认, **仍存在 3 个值得在开工前继续修正的严重问题**。它们不是方向性错误, 而是会在实际施工/验收中造成:

1. 控制流仍可能被误实现
2. 条件产物规则可能被插错层级导致不生效
3. 同步校验命令在当前 macOS 环境下会直接失败

因此本次结论为:

> **V1.1 已明显优于上一版, 但仍不建议直接按原文开工。建议先修正本文列出的 3 个严重问题, 再进入实施。**

## 2. Findings

### 1. 高风险: Step 6 的“ABORT + 阶段终止”仍不是当前 DSL 的正式控制语义, F2 未完全闭环

施工方案 V1.1 通过在 Step 6 中加入:

- `current_phase_result = ABORT`
- `【阶段终止】不进入 Step 7`

来表达失败分支终止, 见更新版方案 [D1esdOTZ...:L30-L36](file:///var/folders/0p/qnd_s8v92bz2ym98_38qzk5r0000gn/T/mcp-lark-docs/lark_doc_D1esdOTZIo6zBVxn2fLc8VrGnqb_1776440156363.md#L30-L36), [D1esdOTZ...:L1162-L1234](file:///var/folders/0p/qnd_s8v92bz2ym98_38qzk5r0000gn/T/mcp-lark-docs/lark_doc_D1esdOTZIo6zBVxn2fLc8VrGnqb_1776440156363.md#L1162-L1234), [D1esdOTZ...:L4573-L4616](file:///var/folders/0p/qnd_s8v92bz2ym98_38qzk5r0000gn/T/mcp-lark-docs/lark_doc_D1esdOTZIo6zBVxn2fLc8VrGnqb_1776440156363.md#L4573-L4616)。

但当前仓库的 DSL 规则层里:

- 只明确存在 `goto` 标签, 见 [core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L116-L123)
- 未定义任何 `abort` / `terminate` / `return` 标签
- 仓库既有工作流的终止表达仍是自然语言 `阶段结束，返回编排器`, 见 [p5-fix-impl.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p5-fix-impl.md#L119-L123), [p6-verification.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L67-L70)

这意味着:

- `current_phase_result = ABORT` 只是**新增约定文本**
- 方案没有同时定义“谁来读取它、何时阻断后续 Step”
- 施工人员如果按字面把它写成普通 `<action>`，仍可能出现“文本上说终止，流程上却继续往下写”的落差

结论:

- F2 的方向修对了, 但**终止机制还没有被定义成当前体系中的可执行/可审计语义**。

建议修订:

- 选一个并写死:
  - 方案 A: 全部失败分支统一使用现有口径 `阶段结束，返回编排器`，不要引入新变量
  - 方案 B: 在 `core-rules.xml` / 工作流约定中正式定义 `current_phase_result = ABORT` 的消费语义
- 在 Step 6 伪代码中补一句:
  - “主 Agent 在读取到 `current_phase_result = ABORT` 后必须立即结束当前 Phase，不再执行后续步骤”

### 2. 高风险: C-7 的 YAML 插入层级描述仍不准确, 条件产物规则有被加错位置的风险

V1.1 已修正字段名, 这一点是对的, 见 [D1esdOTZ...:L1646-L1679](file:///var/folders/0p/qnd_s8v92bz2ym98_38qzk5r0000gn/T/mcp-lark-docs/lark_doc_D1esdOTZIo6zBVxn2fLc8VrGnqb_1776440156363.md#L1646-L1679)。

但这里仍有一个剩余问题:

- 文档写的是“在 `standard_artifacts` 列表末尾新增 2 条规则”
- 实际仓库结构里, 列表是 `standard_artifacts.required`, 见 [artifact-checklist.yaml](file:///Users/bytedance/Code/loupe/eval-framework/artifact-checklist.yaml#L4-L55)
- 方案里的 snippet 也没有带出完整缩进上下文, 显示为顶层 `- path: ...`

这会带来一个非常现实的执行风险:

- 有经验的开发者大概率能自行放对
- 但若有人按文档字面把规则贴在 `standard_artifacts` 下错误层级, 或贴成顶层 list, `artifact_checker.py` 就不会按预期读取
- 最终表现会是“规则写进 YAML 了, 但门禁不生效”

结论:

- F1 的字段兼容问题已大幅缓解, 但**YAML 结构插入位置仍然描述不够精确**，这是新的残余高风险点。

建议修订:

- 将 C-7 明确改成:
  - “在 `standard_artifacts.required` 列表末尾新增 2 条规则”
- snippet 改成带完整缩进的可粘贴版本

### 3. 高风险: Sync-3 校验命令与当前 macOS 环境不兼容, 文档里的最终验收脚本会直接失败

V1.1 的 Sync-3 命令使用:

- `md5sum`
- `find ... -exec md5sum {} \;`
- 进程替换比较哈希

见 [D1esdOTZ...:L2006-L2019](file:///var/folders/0p/qnd_s8v92bz2ym98_38qzk5r0000gn/T/mcp-lark-docs/lark_doc_D1esdOTZIo6zBVxn2fLc8VrGnqb_1776440156363.md#L2006-L2019)。

但在当前环境中已实测:

- `md5sum not found`
- 仅有 `/sbin/md5`

这意味着:

- 文档中写死的最终哈希校验命令在当前 macOS 环境下不能直接执行
- 而 Sync-3 又是方案里的 P0 验收动作, 所以这不是小瑕疵, 是**末端验收脚本不可执行**

结论:

- 这是一个明确的环境兼容性阻断项。

建议修订:

- 将 Sync-3 改成以下任一可移植方案:
  - macOS 版本: 使用 `md5 -r`
  - 跨平台版本: 使用 Python 统一计算 hash
- 推荐直接改成 Python 脚本版, 避免 `md5sum` / `md5` 分叉

## 3. 其他观察

以下问题我认为目前**不构成新的严重阻断**, 但建议在文档里顺手补强:

- `Token Budget` 仅提出“需要评估”, 但未给出明确阈值和验证命令, 建议补一个最小验收方法
- `parse_impl_report_metadata()` 的责任边界已经清晰, 但“如 scoring_engine.py 统一调用此函数”略显过度, 因为 `scoring_engine.py` 当前并不直接消费 `impl-report.md`
- `on_missing: fail` 已写入规则, 但 C-0/C-8b 伪代码没有单独说明如何处理该字段, 建议补一句“当前按必需产物缺失处理, 由现有失败策略承接”

## 4. 复审结论

### 已确认修正到位

- F1: **基本到位**
- F3: **基本到位**
- F4: **明显到位**

### 尚未完全闭环

- F2: **只修到了“意图明确”, 还没修到“语义闭环”**

### 是否还有其他严重问题

有, 仍有以下 3 个严重问题需要处理:

1. Step 6 的终止语义仍未正式化
2. C-7 的 YAML 插入层级仍不够精确
3. Sync-3 的哈希命令不兼容当前 macOS 环境

### 最终建议

> 建议在 V1.1 基础上再补一个小版本修订, 把这 3 个问题收口后再开工。这样施工文档就可以从“明显进步但仍有执行歧义”提升到“可直接实施且验收链路稳固”。
