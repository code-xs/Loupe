# PR-6 施工方案 v1.1 Review 报告（v1.1）

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md`
> 评审日期：2026-04-22
> 评审结论：**Needs Fixes**
> 评审口径：复核 v1.0 review 的 4 条 findings 是否完成收口，并对 v1.1 新引入的协议、守门与 DoD 变化做二次静态审查。

---

## 1. 总体结论

v1.1 相比 v1.0 已完成大部分关键修正，尤其是以下 4 点方向已明显改善：

- 用 `<phase-abort state="Fix-Confirming">` 替代 `<phase-complete>`，正确瞄准了 `stepsCompleted` 提前污染问题
- 不再把 `spec_options` / `fix_design_summary` 塞进 `fields`，正确规避了 Check 15 的顶层字段断言
- Check 11 不再强行升级为 `error`，并把 single-form 强校验拆到独立 Check 17，CI 分层更合理
- 明确承认 P2 `Spec-Uncertain` 存在“收敛到 orchestrator 路径”的轻微行为变化，不再继续使用“完全等价”表述

但当前版本仍残留 **1 个高风险协议问题** 与 **2 个中风险守门/文档一致性问题**。最大的问题是：为了解决 `fields` 冲突，v1.1 引入了“phase 上下文继承”来把 `{spec_options}` / `{fix_design_summary}` 传给 orchestrator 4c 渲染 registry title_template，但该通道在现有编排器与 ADR-010 中并没有被定义。

**综合裁定**：v1.1 明显优于 v1.0，但暂时仍不建议直接开工，建议先补齐这 3 处缺口。

---

## 2. Findings

| No. | 严重度 | 问题 | 结论 |
|---|---|---|---|
| 1 | High | `phase 上下文继承` 作为渲染通道没有现有契约支撑，`spec_options` / `fix_design_summary` 可能在 4c 渲染时丢失 | 必须修 |
| 2 | Medium | 新增 `<phase-abort update_config>` 后没有接入现有 config-schema 守门，形成新的校验盲区 | 应修 |
| 3 | Medium | v1.1 文档内部仍有多处旧口径残留，包含 P4 宏类型、single-form 守门归属、`selected_spec_index` 写回位置 | 应修 |

### Finding 1

**问题**：v1.1 用“phase 上下文继承”替代了 v1.0 的 `fields` 传值，但这个传值机制目前只存在于方案叙述中，没有在现有编排器实现或 ADR-010 中形成明确契约。按当前主干逻辑，phase 局部变量在 `<phase-abort>` 退出后是否还能被 orchestrator step 4c 使用，并无已证实依据。

**证据**：

- v1.1 明确声称 `spec_options` 由 orchestrator 4c “直接消费 phase 上下文”： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L265-L280](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L265-L280)
- v1.1 同样声称 `fix_design_summary` 由 orchestrator 4c “消费 phase 上下文”： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L317-L345](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L317-L345)
- 但当前编排器 step 2 只读取 `workflow_status` / `config_source`，没有任何“继承 phase 局部变量”的动作： [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L23-L40)
- 当前 orchestrator step 4c 只 `load registry` 并按 `current_state` 派发，也没有定义从上一 phase 输出中提取临时变量的流程： [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L158-L209)
- ADR-010 当前正文与落地纪要只定义了“按 `current_state` 查 registry 展开”，没有出现“phase 上下文继承”或“phase 局部变量跨 phase 传递”的契约： [ADR-010](file:///Users/bytedance/Code/loupe/doc/adr/010-step-pause-registry-data-driven.md#L13-L30), [ADR-010](file:///Users/bytedance/Code/loupe/doc/adr/010-step-pause-registry-data-driven.md#L61-L86)

**影响**：

- `Spec-Uncertain` 弹窗可能拿不到 `{spec_options}`
- `Fix-Confirming` 弹窗可能拿不到 `{fix_design_summary}`
- 这两个字段一旦丢失，就不是“文档不完美”而是**用户可见行为直接退化**

**建议修法**：

- 二选一收口：
- 方案 A：把这两个值放回一个**正式定义**的持久化/临时承载通道，例如新增受控 schema 字段或新增明确 DSL 参数，并同步 ADR/脚本
- 方案 B：在 ADR-010 与 `core/workflow.xml` 中正式引入“phase → orchestrator 单轮上下文传递”契约，并说明生命周期、读取时机、跨回合是否保留、对 Limited 平台如何同步

### Finding 2

**问题**：v1.1 为了让 P4 在 `<phase-abort>` 场景下仍能写 `output_fix_design`，新增了 `phase-abort.update_config`。这个方向本身可以理解，但它没有接入现有 `config_source` 守门链路，因此引入了新的校验盲区。

**证据**：

- v1.1 新增 RULES-D4，给 `<phase-abort>` 增加 `update_config` 参数： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L568-L601](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L568-L601)
- v1.1 计划在 P4 使用 `<phase-abort ... update_config='{"output_fix_design": "{output_file}"}'>`： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L317-L345](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L317-L345)
- 现有 `check-config-schema.sh` 只扫描 phase 文件中的文本动作 `更新 {config_source}：key = ...`，并不会解析宏参数中的 `update_config`： [check-config-schema.sh](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-config-schema.sh#L49-L79)
- v1.1 也明确承认 `check-phase-abort-structure.sh` 当前不校验 `update_config`： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L354-L361](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L354-L361)

**影响**：

- `phase-abort.update_config` 一旦后续被误写新 key，不会被现有 Check 7 或 Check 15 抓到
- v1.1 虽然修复了“键归属”，却同时削弱了“键注册受控”这一守门闭环

**建议修法**：

- 最小修法：同步扩展 `check-config-schema.sh`，让它也能解析 `<phase-abort ... update_config='...'>` / `<phase-complete ... update_config='...'>`
- 如果本 PR 不想动脚本，则 DoD 不能继续把 config-schema 守门描述成完整闭环，至少要补“人工 review P4 的 `update_config` key”这一临时要求

### Finding 3

**问题**：v1.1 文档内部仍有多处旧口径残留，说明本轮修订没有完全收干净，会误导 reviewer 和实施者。

**证据**：

- `SCRIPT-D3` 兼容性段仍写着 P4 会包含 `<phase-complete state="Fix-Confirming">`，与 v1.1 的 Fix-1 正文冲突： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L969-L973](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L969-L973)
- RULES-D3 仍写 “single-form 由 `check-io-contract.sh` 校验”，但 v1.1 已改成由新脚本 `check-step-pause-form.sh` + Check 17 强守门： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L547-L563](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L547-L563), [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L749-L823](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L749-L823), [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L1052-L1084](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L1052-L1084)
- ADR 追加段草稿中也仍写 “single-form 由 `check-io-contract.sh` step-pause-single-form 段强制”： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L1190-L1194](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L1190-L1194), [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L1226-L1229](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L1226-L1229)
- P2 重入专项回归里写的是 “`selected_spec_index` 在 `user_inputs` 中正确 = 1 / 因 `user_inputs.selected_spec_index` 已写入不再触发 Spec-Uncertain`”，但当前 registry 写回的是**顶层** `selected_spec_index`，不是 `user_inputs.selected_spec_index`： [pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md:L1359-L1359](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-6-d14-inline-removal-and-system-prompt-rebuild-v1.1.md#L1359-L1359), [step-pause-registry.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/step-pause-registry.yaml#L47-L59), [workflow-status-template.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L39-L45)

**影响**：

- reviewer 容易按旧口径误判是否通过
- 实施者可能错误修改脚本归属或错误断言 `selected_spec_index` 的存储位置
- DoD 与验收步骤会出现“按文档执行也过不了”或“过了但并非验证目标”的情况

**建议修法**：

- 统一全篇把 single-form 守门归口到 `SCRIPT-D6 / Check 17`
- 把所有残留 `<phase-complete state="Fix-Confirming">` 文案改为 `<phase-abort state="Fix-Confirming">`
- 把 P2 重入专项中的 `user_inputs.selected_spec_index` 改成顶层 `workflow_status.selected_spec_index`

---

## 3. 已确认改善

以下内容本轮确认已较 v1.0 实质改善：

- `Fix-Confirming` 的 `stepsCompleted` 污染问题已被正面识别并通过 `<phase-abort>` 方案尝试收口
- `fields` 误用问题不再直接以“塞临时变量进 schema”这种形式出现
- CI 守门的强弱分层明显更清楚，尤其是 Check 11 / Check 17 的拆分方向是对的
- 方案对行为变化的表述更加诚实，review 可执行性比 v1.0 高

---

## 4. 最终裁定

**裁定**：`Needs Fixes`

**建议先修的最小集合**：

1. 明确定义并落地 `spec_options` / `fix_design_summary` 的跨 phase 渲染通道，不要只在方案里口头声明“phase 上下文继承”
2. 让 `check-config-schema.sh` 覆盖宏参数里的 `update_config`，补齐新的守门盲区
3. 清理 v1.1 内部残留旧口径，尤其是 `phase-complete Fix-Confirming`、single-form 守门归属、`selected_spec_index` 存储位置

若以上 3 点收口，v1.1 方案就有机会进入通过态；在此之前，仍不建议直接按当前版本实施。
