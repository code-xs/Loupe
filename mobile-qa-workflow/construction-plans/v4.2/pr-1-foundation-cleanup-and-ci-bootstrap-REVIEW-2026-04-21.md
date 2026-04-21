# PR-1 施工方案质检报告

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-1-foundation-cleanup-and-ci-bootstrap.md`
> 评审日期：2026-04-21
> 评审结论：**暂不建议按当前版本直接开工**
> 评审方式：基于当前仓库现状做静态一致性核查，重点验证施工单的目标文件、DoD、CI 脚本设计、兼容性声明是否与真实工程一致。

---

## 1. 总体结论

本施工单的整体拆分思路是对的：先做地基清理、再补 ADR、最后上第一批 CI 守门，顺序上基本符合 v4.2 总控的依赖关系。

但当前版本存在 **2 个阻断级问题** 和 **3 个高优先级问题**，主要集中在：

- O3 的落点文件与真实工程结构不一致，且对现有 XML 结构的假设错误
- `check-io-contract.sh` 的校验模型与当前 DSL/phase 写法不一致，按文施工会得到“假绿”守门
- phase 文件清单和 DoD 计数与仓库现状不一致，导致部分验收项不可执行
- `check-system-prompt-sync.sh` 的比对算法过于粗糙，落地后大概率长期告警
- O3 其实会触达 legacy 恢复链路，不应被表述为“零运行时变更”

建议先修订施工单，再进入实施。

---

## 2. 质检评级

| 维度 | 评级 | 说明 |
|---|---|---|
| 目标清晰度 | B | 范围边界基本清楚，但部分落点写错文件 |
| 与仓库现状一致性 | D | 多处关键假设与当前工程不一致 |
| 可实施性 | C- | 可以修订后实施，当前版本不可直接照单执行 |
| CI 方案可靠性 | D | 至少 2 个脚本方案会出现假绿或噪音告警 |
| 回滚与兼容性意识 | B- | 有考虑回滚，但对 O3 的 runtime 性质定性不足 |

**综合结论**：`不通过（需修订后复审）`

---

## 3. Blocking Findings

### 3.1 阻断问题 1：O3 修改目标文件写错，且拟议 diff 不符合当前 XML 结构

**结论**：施工单把 O3 的核心修改目标写成了不存在的 `mobile-qa-workflow/functionality-deep-dive/core/core-rules.xml`，同时假设 `<agent>` 声明带 `file=` 属性；这与当前工程真实结构不一致，按文施工会直接卡住。

**事实依据**：

- 施工单要求修改 `mobile-qa-workflow/functionality-deep-dive/core/core-rules.xml`，并把 `<agent ... file="..."/>` 改到 archive 路径。
- 当前仓库中并不存在该文件；专项子流程真正加载的是主流程的 `mobile-qa-workflow/core/core-rules.xml`。
- 当前 `core/core-rules.xml` 中 legacy deep-dive agent 的定义形态是：
  - `<agent name="context-reconstructor" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>`
  - 即只有 `name`/`scenario` 和文本内容，没有 `file=` 属性。

**风险**：

- 实施者会在错误路径上改文件，或者被迫临时扩展 XML 结构，导致 PR-1 从“地基整理”变成“DSL 结构变更”。
- legacy 恢复链路相关声明会出现“文档写了、运行时没跟上”的假完成状态。

**修订建议**：

- 把 O3 的目标文件统一改为 `mobile-qa-workflow/core/core-rules.xml`。
- 不要在 PR-1 引入新的 `<agent file="...">` 结构，除非先补充 DSL 兼容性说明和消费方逻辑。
- 将“归档 legacy agent 文件”与“如何让旧会话继续恢复”拆成两个明确子任务，并给出真实可执行的引用链说明。

---

### 3.2 阻断问题 2：`check-io-contract.sh` 的校验对象和当前仓库模型不匹配，会产生假绿

**结论**：施工单设计的 `check-io-contract.sh` 无法正确校验当前仓库，按现状实现大概率直接得到空结果并通过，达不到守门目的。

**事实依据**：

- 施工单脚本方案假设 `core/workflow.xml` 的 `<io-contract>` 内存在 `file="..."` 属性，并用正则 `r'<io-contract>(.*?)</io-contract>'` 提取。
- 真实工程中 `core/workflow.xml` 的写法是 `<io-contract desc="各阶段产物 I/O 契约">`，内部是 `output="issue-card.md"`、`output="spec.md, context-curation-report.md, context-bundle.md"` 这种产物名列表，不存在 `file="..."`。
- phase 文件的 `<template-output>` 则主要是 `file="{output_file}"`、`file="{workspace_folder}/..."` 这类变量化路径，和 `io-contract` 的 basename 语义不在同一层。

**风险**：

- `DECLARED` 会被提取为空，脚本直接“通过”，形成假绿。
- 即便补齐了正则，仍然无法把 `output="spec.md"` 与 `file="{output_spec}"` 或 `file="{workspace_folder}/context-curation-report.md"` 做可靠映射。

**修订建议**：

- 改成“产物名层”的守门，而不是“file 属性直接相等”。
- 方案 A：统一从 phase 顶部静态变量或 `config_source` 输出键解析产物名，再与 `io-contract output` 比对。
- 方案 B：先在 phase 文件里补充一层显式 artifact 声明，再做 CI 守门。
- 在脚本设计定稿前，不建议把该项作为 PR-1 的 error 级门禁。

---

## 4. Major Findings

### 4.1 高优先级问题 1：phase 文件清单和 DoD 计数与当前工程不一致

**结论**：施工单把 PR-1 的 O6 定义为“7 个 phase 文件统一加注释”，但当前主流程实际只有 6 个 phase 文件，且文件名与方案文案不一致。

**事实依据**：

- 施工单列出了 `p4-implementation.md`、`p5-fix-implementation.md` 等候选文件。
- 当前仓库真实清单为：
  - `p1-intake.md`
  - `p2-spec-definition.md`
  - `p3-root-cause.md`
  - `p4-fix-design.md`
  - `p5-fix-impl.md`
  - `p6-verification.md`
- 因此 “grep 命中 7 处幂等性约束注释” 的 DoD 在当前仓库是不可达的。

**风险**：

- 实施时会出现改错文件、漏改真实文件、或为了满足 DoD 临时制造伪文件名的情况。
- reviewer 无法根据 DoD 判断是否真正确认全部 phase。

**修订建议**：

- 在施工单中把 phase 清单直接改成当前真实文件名。
- O6 与 DoD 统一改成“6 个主流程 phase 文件”。
- 如果想覆盖专项 deep-dive phases，应单独列为另一个子项，不要与主流程 phase 混写。

---

### 4.2 高优先级问题 2：`check-system-prompt-sync.sh` 的 enum 比对方法不可靠，容易长期告警

**结论**：脚本方案拿 `workflow-status-template.yaml` 中的“完整枚举集”去对比 `system-prompt.md` 中所有 `current_state = xxx` 的赋值结果，这两者不是同一语义层，落地后会变成脆弱告警。

**事实依据**：

- 施工单脚本设计中：
  - `ENUM_CORE` 从状态模板注释中抽完整 enum 集
  - `ENUM_SP` 则通过 `grep 'current_state[:=]...' system-prompt.md` 抓取赋值 RHS
- 但 `system-prompt.md` 本身已经有一段完整合法枚举声明；赋值集合只是“被写入过的状态子集”，天然不等于“完整注册表”。

**风险**：

- 只要某个合法状态没有在 `system-prompt.md` 中出现赋值语句，就会被误报为不同步。
- 长期 warning 会降低 reviewer 对真实告警的敏感度，最终形同虚设。

**修订建议**：

- 改为比较“权威枚举声明块”对“权威枚举声明块”，不要比较赋值命中集。
- 如果 PR-1 只想兜住明显漂移，可先做更窄的断言：例如校验关键 stop state、Spec-Uncertain allowed_values、顶层镜像白名单等少量高风险 token。

---

### 4.3 高优先级问题 3：PR-1 被表述为“零运行时变更”，但 O3 实际触达 legacy 恢复行为

**结论**：施工单总体定位写的是“零运行时变更”，这对 O1/O2/O4/O5/O6 基本成立，但对 O3 并不严谨。只要移动 legacy agent 文件并改恢复引用，旧会话恢复路径就属于运行时兼容链路。

**事实依据**：

- 施工单首页将 PR-1 定义为“零运行时变更”。
- 同一文档中 O3 又要求移动 5 个 legacy agent，并确保 `v3-legacy` 会话恢复继续可用。
- 当前 `functionality-deep-dive/core/workflow.xml` 明确存在 legacy 恢复逻辑：`workflow_version == v3-legacy` 时优先沿旧状态恢复。

**风险**：

- 实施者和 reviewer 会低估 O3 的回放验证重要性，把它当成单纯文档归档处理。
- 一旦 archive 路径或恢复约定稍有偏差，影响的是旧会话可恢复性，而不是静态文档质量。

**修订建议**：

- 将 PR-1 的定位改成“主路径零运行时变更，legacy 恢复链路有兼容性触达”。
- 把 O3 单独标成“兼容性敏感改动”，并保留专门的本地回放验收步骤。

---

## 5. 次要问题与优化建议

### 5.1 `check-subagent-params.sh` 需要补充实现级约束说明

- 目前施工单只给了 challenger 分支的近似写法，arbiter 侧还是“略”。
- 作为 error 级 CI，脚本必须在施工单中给出完整、可复现的判断规则，否则 reviewer 无法判断误报/漏报边界。

### 5.2 PR-1 的回归矩阵与工作量估算偏紧

- 施工单同时要求文档归档、ADR 落地、4 个脚本、workflow 集成、legacy 回放、全量 eval-cases、多平台抽样。
- 对一个标注为 `0.9d` 的 PR 来说，实施量与验收量偏乐观，建议在施工单中显式拆出“必做”和“可并到 follow-up”的校验项。

---

## 6. 建议的修订动作

建议按以下顺序修订施工单后再开工：

1. **先修结构映射**
   - 统一 O3 的真实目标文件、真实 phase 清单、真实 deep-dive 引用链。

2. **再修 CI 设计**
   - 先重写 `check-io-contract.sh` 的校验模型。
   - 收窄 `check-system-prompt-sync.sh` 到“声明块对声明块”或“关键 token 对关键 token”。

3. **最后修 DoD**
   - 把“7 个 phase 文件”改为“6 个主流程 phase 文件”。
   - 对 O3 单列 legacy 回放验收，不再混入“零运行时变更”的口径。

---

## 7. 可采纳项

以下内容可以保留，作为修订后的施工单基础：

- PR 拆分顺序基本合理，符合 v4.2 总控依赖关系
- O1 修 `RCA-InProgress`、O2 修 system-prompt 编号重复，都是明确且低风险的收口项
- 先做 ADR-010 / ADR-021 草稿，再做 PR-3 / PR-5，是合理的 H4 前置策略
- 历史文档“归档而非删除”的方向正确，能保留审计与回溯能力

---

## 8. 最终裁定

**裁定**：`Reject for now`

**原因**：当前施工单不是“方向错误”，而是“若按字面执行会在关键位置撞到真实工程结构”。其中 O3 与 `check-io-contract.sh` 已达到阻断级，必须修订后再实施。

**建议流程**：

- 先修订施工单到 v1.1
- 复审通过后再开 PR-1 实施
- 实施时优先只落 O1/O2/O4/O5/O6 中与真实工程完全对齐的部分

