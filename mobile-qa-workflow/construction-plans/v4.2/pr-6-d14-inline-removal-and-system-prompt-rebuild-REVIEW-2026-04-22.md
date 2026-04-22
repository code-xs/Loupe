# PR-6 施工方案 Review 报告（v1.0）

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md`
> 评审日期：2026-04-22
> 评审结论：**Needs Fixes**
> 评审口径：基于当前主干 DSL 契约、编排器状态机、现有守门脚本与 v4.2 主控约束做静态一致性审查，仅记录已证实问题。

---

## 1. 评审范围与方法

本轮 review 聚焦 4 个维度：

- **协议自洽性**：方案新写法是否与当前 `core/core-rules.xml`、`workflow-status-template.yaml`、ADR-021 宏契约一致
- **状态机正确性**：phase 退出方式、`stepsCompleted`、`current_state` 与重入路径是否保持正确
- **CI 可验证性**：DoD、脚本修改方案、workflow 检查项是否真正形成闭环
- **行为等价性**：方案声称“等价/无语义变化”的部分是否有足够证据成立

交叉核验基线：

- 施工单：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md)
- 主控方案：[README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L193-L201)
- 当前宏契约：[core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L206-L240)
- 当前编排器：[workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L145-L209)
- 当前状态模板：[workflow-status-template.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L4-L114)
- 当前 P2/P4 实现：[p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L46-L95) / [p4-fix-design.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L131-L142)
- 当前守门脚本：[check-phase-abort-structure.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-phase-abort-structure.sh#L35-L194) / [check-io-contract.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-io-contract.sh#L63-L196) / [check-system-prompt-sync.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-system-prompt-sync.sh#L13-L109)

---

## 2. 总体结论

该方案的主方向是合理的：继续推进 D14 收口、彻底迁出 phase 内联 `step-pause`、补 `Fix-Confirming`、同时解锁 `system-prompt.md` 首次自动构建，这些目标与主控 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L193-L201) 是一致的。

但当前版本仍有 **2 个高风险协议/状态机问题** 和 **2 个中风险守门/等价性问题**。若按文档原样实施，存在以下明确风险：

- `phase-abort` / `phase-complete` 的 `fields` 被当作“临时渲染上下文”使用，但现有宏契约会把它们写入 `workflow_status`，与当前 schema/Check 15 冲突
- `Fix-Confirming` 被设计成 phase 已完成后的外部确认，`Revise` 路径会提前把 `qa-fix-design` 计入 `stepsCompleted`
- P2 `Spec-Uncertain` 从“phase 内继续”变成“ABORT 后整 phase 重跑”，与文档声称的“完全等价”不一致
- 两处 CI 守门升级方案存在“文案比实现更强”的问题，可能给 reviewer 造成假闭环印象

**综合裁定**：当前版本不建议直接开工，建议先修正文档后再进入实施。

---

## 3. Findings

| No. | 严重度 | 问题 | 结论 |
|---|---|---|---|
| 1 | High | 宏 `fields` 被误用为临时渲染上下文，和现有宏展开语义、schema 守门冲突 | 必须修 |
| 2 | High | `Fix-Confirming` 用 `phase-complete` 提前结束 P4，会导致 `Revise` 路径错误追加 `stepsCompleted` | 必须修 |
| 3 | Medium | P2 `Spec-Uncertain` 改成 ABORT + 重进 phase，不是文档声称的“用户体验完全等价” | 应修 |
| 4 | Medium | 两处 CI 守门方案的“承诺强度”高于实际脚本能力，存在假绿/假闭环风险 | 应修 |

### Finding 1

**问题**：施工单把 `phase-abort` / `phase-complete` 的 `fields` 当作“一次性渲染上下文通道”来传递 `spec_options`、`fix_design_summary`、`output_fix_design`，但当前宏契约并不是“临时上下文”，而是**写回 `workflow_status` 顶层字段**。这与方案正文自己的“`fix_design_summary` 不进 schema”判断，以及现有 Check 15 的字段校验规则直接冲突。

**证据**：

- P2 方案把 `spec_options` 放进 `<phase-abort ... fields=...>`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L239-L246](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L239-L246)
- P4 方案把 `fix_design_summary` 和 `output_fix_design` 放进 `<phase-complete ... fields=...>`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L287-L296](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L287-L296)
- 同一文档又明确写明 `fix_design_summary` “不进 schema，仅作为本轮局部变量”：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L306-L311](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L306-L311)
- 现行宏契约规定：`phase-abort` / `phase-complete` 的 `fields` 会更新到 `{workflow_status}`：[core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L209-L233)
- 现行 Check 15 会校验 `fields key ∈ workflow-status-template.yaml 顶层字段表`：[check-phase-abort-structure.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-phase-abort-structure.sh#L35-L127)
- 当前状态模板并没有 `spec_options`、`fix_design_summary`、`output_fix_design` 这些顶层字段：[workflow-status-template.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L13-L114)
- `output_fix_design` 当前属于 `config_source` 侧注册键，而不是 `workflow_status` 顶层字段：[p4-fix-design.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L131-L142)

**影响**：

- 按现有脚本实现，P2/P4 宏改写会直接触发 Check 15 失败
- 即便放松脚本，`workflow_status` 也会被注入临时渲染字段，污染 schema 边界
- `output_fix_design` 从 config 通道挪到 status 通道，会打破现有键归属约定

**建议修法**：

- 不要复用 `fields` 传递“仅供 step-pause title 渲染的临时变量”
- 若确实需要临时渲染上下文，应新增独立契约，例如 `render_fields` / `transient_fields`，并同步扩展宏与守门脚本
- `output_fix_design` 应继续通过 `update_config` 或单独 `更新 {config_source}` 动作写入，不应改写为 `workflow_status` 字段

### Finding 2

**问题**：施工单把 `Fix-Confirming` 设计为 P4 step 6 的 `<phase-complete state="Fix-Confirming" .../>`，这意味着 P4 在用户还没做 `Continue / Revise` 选择前就已经按“正常完成”退出；随后 `Revise` 再把状态改回 `Fix-Designing`。这与当前 inline `step-pause` 的语义不同，会导致 **`qa-fix-design` 提前写入 `stepsCompleted`**。

**证据**：

- 方案明确将 P4 step 6 改为 `<phase-complete state="Fix-Confirming" .../>`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L287-L296](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L287-L296)
- 方案还声明 `Revise` 会回到 `Fix-Designing` 并 `increment: fix_retry_count`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L88-L97](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L88-L97)
- 当前宏契约对 `phase-complete` 的定义是“默认 OK，退出本 phase，编排器追加 `stepsCompleted`”：[core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L224-L240)
- 当前编排器在 `{current_phase_result} != ABORT` 时会把当前 phase 加入 `stepsCompleted`：[workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L145-L156)
- 编排器选下一阶段依赖 `stepsCompleted`：[workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L23-L40) 和 [workflow-model.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-model.yaml#L1-L10)
- 当前 P4 真实实现仍是 phase 内 inline `step-pause`，`Revise` 发生在 phase 内部，尚未完成 phase：[p4-fix-design.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L131-L142)

**影响**：

- `Revise` 路径会把一个“尚未被确认接受”的 P4 轮次标记为已完成
- 这会污染 `stepsCompleted` 的语义，给下一轮阶段判定和回滚分析带来歧义
- 文档中“用户体验完全等价”的结论不成立

**建议修法**：

- 不要用 `phase-complete` 表达“待用户确认的中间门”
- 可选方案 A：保留 P4 内部确认门，直到用户 `Continue` 后才正式 `phase-complete`
- 可选方案 B：若必须外置到 registry，则需要一个“不追加 `stepsCompleted` 的 pause-exit 宏/协议”，不能复用当前 `phase-complete`

### Finding 3

**问题**：P2 `Spec-Uncertain` 的改写并非方案所说的“用户体验完全等价”。当前实现是在 phase 内停顿后继续执行后续 step；新方案则改成 `phase-abort state="Spec-Uncertain"`，由编排器接管，再在用户回复后从 orchestrator `step 2` 重新判定并进入 phase。这是**整 phase 重入**，不是“在原 phase 内继续”。

**证据**：

- 新方案使用 `<phase-abort state="Spec-Uncertain" .../>`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L239-L246](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L239-L246)
- `Spec-Uncertain` registry on_success 会 `set_state: Spec-Defining` 并 `goto: step_2`：[step-pause-registry.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/step-pause-registry.yaml#L34-L59)
- 当前 P2 实现是在 step 4 内直接 inline `step-pause`，并未退出 phase：[p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L46-L63)
- 但方案宣称“用户体验完全等价”：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L250-L259](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L250-L259)

**影响**：

- P2 会从 step 1 重新执行，而不是从原 step 4 后继续
- 这会带来额外 token/时延开销，也可能改变上下文搜集与复杂度判定的时序
- 若要宣称“完全等价”，当前证据不足

**建议修法**：

- 如果接受“重入 phase”这一行为变化，应在方案中明确标成**行为变化**而非“完全等价”，并补充专项回归
- 如果目标真的是“等价迁移”，就需要设计能在 P2 内恢复执行的机制，而不是简单 `ABORT + step_2`

### Finding 4

**问题**：两处 CI 守门设计都存在“文案承诺强于实际脚本能力”的问题。

**证据 A：Check 11 升级为 error 的前提不足**

- 方案要求把 Check 11 `io-contract` 从 warning 升级为 error：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L846-L846](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L846-L846)
- 当前 CI workflow 明确写明其 basename/变量化兜底算法仍过宽，所以暂不升级 error：[qa-workflow-schema-check.yml](file:///Users/bytedance/Code/loupe/.github/workflows/qa-workflow-schema-check.yml#L325-L332)
- 施工单对 `check-io-contract.sh` 的改动只覆盖 `step-pause` single-form 段，没有修正前半段 io-contract basename 匹配算法：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L617-L661](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L617-L661) 与 [check-io-contract.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-io-contract.sh#L13-L61)

**证据 B：`check-system-prompt-sync.sh` 的“registry 字面对 registry 字面校验”描述与代码骨架不符**

- 方案文字说要校验 `state / result_field / allowed_values` 是否完整出现：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L684-L687](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L684-L687)
- 但给出的脚本骨架实际只抽 `REG_STATES` 并检查 state 名是否出现在 `system-prompt.md`：[pr-6-d14-inline-removal-and-system-prompt-rebuild.md:L689-L697](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild.md#L689-L697)

**影响**：

- Check 11 升级后仍无法保证 io-contract 守门质量，只是把现有弱守门变成强阻塞
- Check 10 升级后的 2a 段仍可能在 `result_field` 或 `allowed_values` 漂移时假绿
- reviewer 会误以为“CI 已形成强闭环”，实际并没有

**建议修法**：

- Check 11 保持 warning，直到 io-contract 主算法本身被修正后再升级
- 或者把 single-form 校验从 `check-io-contract.sh` 中拆成独立 error check，不与弱基座绑在一起
- `check-system-prompt-sync.sh` 应至少比较三元组 `state + result_field + allowed_values`，最好直接比较生成器输出的 registry 路由表与源 registry 的结构化抽取结果

---

## 4. 已确认优点

以下方向本轮确认是正确的，可保留：

- **PR 边界清晰**：没有把 PR-7 的结构收敛议题混入本 PR，和主控 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L22-L33) 一致
- **D14 收口目标明确**：P2/P4 内联清零、allowlist 物理删除、Check 15 升级 error 这一主线清楚
- **对 `system-prompt.md` 首次自动构建的门槛意识是对的**：保留人工 diff、强调 Limited 平台回归，都符合 H1/H3 风险模型
- **文档/ADR/CI 联动意识较强**：比单纯改 phase 文件更完整，审查维度覆盖得比较全

---

## 5. 最终裁定

**裁定**：`Needs Fixes`

**建议先修的最小集合**：

1. 重新定义“registry 渲染所需的临时上下文”传递机制，不要继续复用 `phase-abort/complete.fields`
2. 重做 `Fix-Confirming` 的退出模型，确保 `Revise` 不会提前完成 P4
3. 明确 P2 `Spec-Uncertain` 是“行为变化”还是“等价迁移”，并据此修正文案或重设计实现
4. 下调或重构两处 CI 守门升级方案，避免“文案闭环强于真实闭环”

若以上 4 点收口，本方案即可进入下一轮定向复审；在此之前，不建议按当前版本直接实施。
