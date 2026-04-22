# v4.2 PR-6 施工方案 v1.0

> **PR 名**：D14 收口 #3 — phase 内联删除 + `Fix-Confirming` enum + `system-prompt.md` 首次自动构建
> **包含 V1.1 项**：O13 + O14 + O12 + 触发 PR-2 留下的 `system-prompt.md` 首次自动构建并替换（解 H1）
> **关联主控**：[`v4.2/README.md` §6 PR-6 章节](./README.md#pr-6--d14-收口-3phase-内联删除--fix-confirming--system-prompt-首次构建)
> **方案来源**：[`doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.2.13 / §3.2.14 / §3.2.12 / §3.3.17 Stage-1
> **前置 PR**：PR-3'（O21 宏标签 + Check 15 守门）+ PR-5（O10+ registry 数据化 + Check 16 守门）—— 两者必须**已合入 main 且零 warning** 才能启动本 PR（H3 严格串行）。
> **施工时长估算**：1.4 d（与 README §1 工作量表一致；本 PR 是 D14 治理收口的最后一公里，不涉及大体量结构重构）。
> **风险等级**：中（删除 phase 内联 step-pause 后 Limited 平台是高风险点，必须 5+ 用例双侧一致）。

---

## 0. 唯一职责声明（防 PR 越界）

本 PR 的**唯一职责**是把 PR-3'/PR-5 已经铺好的两条治理路径（phase 出口宏 + step-pause 注册表）**合龙**，并依此触发 system-prompt.md 自动构建首次替换：

1. **D14 调度作用域整改清零**（O13 + O14）：phase 文件残留的 2 处内联 `<step-pause>` 全部迁出，迁移到 `step-pause-registry.yaml` 的注册表项 + `<phase-abort>` 宏触发，由编排器 step 4c 统一调度。
2. **新枚举 `Fix-Confirming` 落地**（O14）：`workflow-status-template.yaml` enum 集 + `step-pause-registry.yaml` registry 同时新增本枚举条目，覆盖 P4 step 6 「Continue / Revise」选择。
3. **顶层镜像白名单元协议下线**（O12 收尾 / v4.2 遗留 #3）：删除 `non_bug_user_choice` 顶层镜像字段、删除"白名单"概念在 `core-rules.xml` / `system-prompt.md` / `PLATFORM-GUIDE.md` 中的引用，编排器统一改读 `user_inputs.<key>`。
4. **触发 system-prompt.md 自动构建首次替换**（H1 解锁 / O17+ Stage-1）：在 PR-3'(已含 `1|2|S` 契约) + PR-5(已含 registry) + 本 PR 新增的 `Fix-Confirming` 全部就绪后，运行 `build-system-prompt.py --mode=full ALLOW_FIRST_BUILD=1` 替换 `system-prompt.md`，然后人工 diff 验证零业务语义差异。
5. **D19 / H1 守门下线**：删除 `legacy-phase-step-pause-allowlist.txt` 物理文件、CI workflow yml 中相关 Check 1/2/4/6/13 全部下线或调整，Check 15 (`check-phase-abort-structure.sh`) 由 warning 升级 error。

### 0.1 不在本 PR 范围（明确边界 / 防 reviewer 误读）

| 议题 | 归属 PR | 备注 |
|------|--------|------|
| O15（P3 三档 fan-out 升级早退路径合并） | PR-7 | 需要 O21 宏稳定运行 ≥ 1 个 PR 周期后再做 |
| O16（deep-dive 主子配置键名收敛 / v4.2 遗留 #1） | PR-7 | 与 O11+ 模块化拆分配套 |
| O11+（invoke-subagent boilerplate + coder-agent 拆分 + shared-input-guard 提取） | PR-7 | 与 O19+ / O23 / O24 / O25 同 PR |
| O17+ Stage-2（L0-L4 分层产物按需注入） | v4.3 评估 | 本 PR 仅落 Stage-1 单文件全量构建 |
| O20（functionality-deep-dive 子工作流状态收编） | PR-8（v4.3） | 大体量重构，独立立项 |
| `selected_spec_index` 在 P2 内的实际消费（按值差异化路由） | PR-7 O15 | 本 PR 仅写入 enum；O15 才让 P2 按值路由 |
| `workflow_version` 字段从 `legacy` 迁移到正式 schema 标识 | v4.3 | 与 ADR-019 物理删除前提配套 |

---

## 1. PR 元信息表

| 字段 | 值 |
|------|---|
| PR 类型 | 🟢 治理收口（含 1 项契约层小变更：新增 `Fix-Confirming` enum） |
| 主分支基线 | 必须基于 PR-5 已合入 main 的 commit；若仍处于 feature 分支阶段，则基于 `feature/v4.2-pr-5` HEAD |
| 改动量预估 | ~22 个变更点 / 跨 16 个文件（含 1 个文件物理删除 / 1 个文件全量重写） |
| 依赖 ADR | ADR-014（D14 收口 / 追加 PR-6 落地纪要） + ADR-019（superseded / allowlist 物理删除） + ADR-016（删 inline 形态过渡声明） + ADR-021 / ADR-010（落地纪要扩段） + ADR-015（受限双写白名单 → 简化双写） + ADR-008（编排器读路径补充） |
| 跨平台回归矩阵 | Cursor + Trae + Dify + 单 prompt LLM 全跑（README §5 PR-6 行）；其中 Dify 必须 5+ 用例双侧弹窗一致 |
| CI 守门变化 | Check 1 / Check 2 / Check 4 / Check 6 / Check 13 下线或调整；Check 15 升级 error；新增"H1 解锁后 Spec-Uncertain 字面无锚点也校验"的兜底逻辑（迁移到 Check 10 算法升级） |
| 回滚成本 | 中（涉及 enum 集 + system-prompt 全文件 + ADR 状态机切换 + CI yml 全面调整；rollback 顺序见 §4） |

---

## 2. 文件级 diff 列表（按变更点编号 / 23 项）

> 命名约定（与 PR-5 v1.1 体例对齐）：
>
> - `REG-N*` = `step-pause-registry.yaml` 内的新增 / 删除条目
> - `PHASE-D*` = `phases/p*-*.md` 文件内的 step-pause 删除 + 宏改写
> - `XML-D*` = `core/workflow.xml` 内的删除 / 调整
> - `RULES-D*` = `core/core-rules.xml` 内的删除 / 调整
> - `TPL-D*` = `core/workflow-status-template.yaml` 内的删除 / 调整
> - `SP-N1` = `system-prompt.md` 全量重写
> - `GEN-D*` = `scripts/build-system-prompt.py` 增强
> - `SCRIPT-D*` = CI 守门脚本调整
> - `CI-D*` = `.github/workflows/qa-workflow-schema-check.yml` 调整
> - `ADR-D*` = ADR 文档调整
> - `DOC-D*` = `PLATFORM-GUIDE.md` 等文档调整
> - `FILE-D1` = 文件物理删除

### 2.1 文件 A · `core/step-pause-registry.yaml`（REG-N1 新增 + REG-D1 删除）

#### 2.1.1 REG-N1（新增 `Fix-Confirming` 注册表项 / O14）

**操作**：在 `Boundary-Refined`（kind:route 路由项）**之前**新增第 8 个条目（保持 6 个交互态 + 1 个新交互态 + 1 个路由态的分组顺序）。

**新文（追加块，~18 行）**：

```yaml
  - state: Fix-Confirming
    title_template: |
      Fix Design 四重论证完成，请确认是否进入修复实施：
      {fix_design_summary}
    result_field: fix_confirming_choice
    allowed_values: [Continue, Revise]
    options:
      - title: "[C] Continue：论证通过，进入 Phase 5 修复实施"
        action: "fix_confirming_choice=Continue"
      - title: "[R] Revise：修改方案后重新论证"
        action: "fix_confirming_choice=Revise"
    on_success:
      Continue:
        set_state: Fix-Implementing
        write: { reroute_reason: null, reroute_target_phase: null }
        goto: step_2
      Revise:
        set_state: Fix-Designing
        increment: fix_retry_count
        goto: step_2
```

**修订理由**：
- 与 `phases/p4-fix-design.md:135-141` 现存的内联 step-pause 在用户体验上 1:1 等价（Continue 进入 Fix-Implementing / Revise 跳回 Fix-Designing 并增加重试计数）。
- `title_template` 含 `{fix_design_summary}` 占位，由 P4 step 6 在 `<phase-abort>` 的 `fields` 中写入（见 §2.4 PHASE-D2）。
- `Revise` 分支显式 `increment: fix_retry_count` 与 PR-5 子文档 §1.2 描述的"4c 派发 on_success 时 increment 已是注册表能力"对齐，无需编排器侧改动。
- **未启用 `mirror_to_top`**——本字段直接走 user_inputs 命名空间（与 v4.2 遗留 #3 收尾对齐，参见 §2.1.2）。

#### 2.1.2 REG-D1（删除 Non-Bug 项的 `mirror_to_top: true` 标记 / 配套 v4.2 遗留 #3）

**操作**：在 `state: Non-Bug` 注册表项中删除以下行：

```yaml
    mirror_to_top: true   # D15 双写数据化（v4.2 PR-5 起步白名单：仅本项；遗留 #3 删除后本标记一并下线）
```

**同步修订**：注册表 schema 头部注释（第 6-13 行）对应删除：

```yaml
#   / mirror_to_top(可选 bool，D15 双写标记，
#     v4.2 PR-5 起仅 Non-Bug；遗留 #3 删除后下线)。
```

替换为：

```yaml
#   （v4.2 PR-6 起 mirror_to_top 已下线，编排器 4a 全部走 user_inputs.<key> 单写）
```

**修订理由**：v4.2 遗留 #3 收尾——`non_bug_user_choice` 顶层字段下线后，编排器 4a 不再需要分支判断 `mirror_to_top == true` 做双写（详见 §2.5 XML-D1）。注册表的 `mirror_to_top` 字段对未来扩展无价值，与 v4.3 演进方向（编排器全量改读 `user_inputs.<key>`）冲突，本 PR 一并下线。

#### 2.1.3 兼容性影响

- ① 现有 6 个交互态 + 1 个路由态行为 100% 不变（仅 schema 头注释变化）；
- ② 新增 `Fix-Confirming` 后 registry 总条目 = 8（CI Check 16 第 ② 类双向严格相等校验需同步更新 EXPECTED 集，详见 §2.13）；
- ③ Non-Bug 用户选择不再写顶层 `non_bug_user_choice`，编排器侧 case Non-Bug 的渲染入参 `{non_bug_user_choice}` 引用必须改写（详见 §2.5 + §2.7）。

---

### 2.2 文件 B · `core/workflow-status-template.yaml`（TPL-D1~D4）

#### 2.2.1 TPL-D1（enum 集新增 `Fix-Confirming`）

**操作**：第 4-8 行的 v4.1 完整集合注释块**整体替换**为：

```yaml
# current_state 合法枚举集（C5 单一权威源，v4.2 完整集合）：
#   Intake / Spec-Defining / Spec-Uncertain / Context-Curating / Curation-Failed
#   / Boundary-Refined / Non-Bug / Info-Insufficient / RCA-Designing
#   / RCA-LowConfidence / Fix-Designing / Fix-Confirming / Fix-Implementing
#   / Verifying / Human-Review / Done
# 任何 phase / 编排器 / 文档新增的 current_state 取值，必须先在此处注册并同步
# SKILL.md / system-prompt.md / PLATFORM-GUIDE.md。
```

**关键变化点**：
- 标题由"v4.1 完整集合"改为"**v4.2 完整集合**"（防 `check-system-prompt-sync.sh` / `check-phase-abort-structure.sh` 的 python 提取器卡在旧锚点 — **两脚本均按 `v4\.1\s*完整集合` 正则抓取**，本 PR 同步更新两脚本的正则锚点为 `v4\.[12]\s*完整集合`，详见 §2.12 SCRIPT-D2 与 §2.13 SCRIPT-D3）。
- 新增 `Fix-Confirming`（紧邻 `Fix-Designing` 之后，符合状态机时序：Fix-Designing → Fix-Confirming → Fix-Implementing）。
- enum 总数由 15 → 16。

#### 2.2.2 TPL-D2（删除 `non_bug_user_choice` 顶层字段 / v4.2 遗留 #3 收尾 / O12 配套）

**操作**：删除现有第 101-106 行整段：

```yaml
# ⚠️ 顶层镜像字段白名单（v4.1 双写过渡，v4.2 收敛 / D8 + D15）
# 协议（强契约）：编排器双写时仅当 step-pause 的 result_field 出现在以下字段集中，
#   才会同步写入顶层；不在白名单内的 result_field 仅写 user_inputs.<key>，不污染顶层 schema。
# 起步白名单 = { non_bug_user_choice }；新增需 PR Review 显式批准并同步本块注释。
# v4.2 收敛动作：编排器改读 user_inputs.<key>，并删除以下字段（v4.2 遗留 #3）。
non_bug_user_choice: null    # 镜像 user_inputs.non_bug_user_choice（v4.1 起步白名单）
```

**替换为（保留 v4.2 收敛纪要 / 防止 reviewer 在 git blame 时丢失上下文）**：

```yaml
# ⚠️ 顶层镜像字段（v4.1 过渡 / v4.2 PR-6 收尾）
# v4.1 起步白名单 = { non_bug_user_choice } 已于 v4.2 PR-6 删除（v4.2 遗留 #3 收口 / O12 配套）；
# 编排器 4a 现在统一走 user_inputs.<result_field> 单写路径，无 mirror。
# 历史镜像字段恢复路径见 ADR-015 v4.2 修订段。
```

**修订理由**：v4.2 遗留 #3 完整收口——`user_inputs.non_bug_user_choice` 已是事实标准，顶层镜像仅为 v4.1 兼容字段，PR-6 D14 内联删除后已无 phase 文件依赖顶层引用，可安全删除。

#### 2.2.3 TPL-D3（user_inputs 注释块更新 / 配套 TPL-D2）

**操作**：第 77-81 行的 user_inputs 注释段：

```yaml
# user_inputs（v4.1 / C11 D2）：step-pause 用户回复的命名空间容器。
# 编排器 step 4 解析 step-pause 用户回复后总是写入 user_inputs.<result_field>；
# 仅当 <result_field> 在下方"顶层镜像字段白名单"内时，才同步写入顶层（D15 双写白名单受限）。
# v4.2 收敛后编排器改读 user_inputs.<key>，届时删除下方所有顶层镜像字段。
user_inputs: {}
```

**替换为**：

```yaml
# user_inputs（v4.1 / C11 D2 / v4.2 PR-6 收口）：step-pause 用户回复的命名空间容器。
# 编排器 step 4a 解析 step-pause 用户回复后**总是**写入 user_inputs.<result_field>（单写）；
# 顶层镜像白名单已于 v4.2 PR-6 全量下线（详见 ADR-015 v4.2 修订段）。
# 编排器 / phase / system-prompt 引用用户选择时，统一使用 {user_inputs.<key>} 形式。
user_inputs: {}
```

#### 2.2.4 TPL-D4（注释段中 `selected_spec_index` 字段说明微调 / 配套 system-prompt.md 同步重建）

**操作**：第 39-45 行的注释段（PR-3' 引入）保留主体不变，但把"v4.2 阶段：本字段仅写入，P2 暂不消费"改为"v4.2 阶段：本字段由编排器写入；P2 在 PR-7 O15 内按值差异化路由（本 PR 不引入 P2 行为变化）"，明确把行为变化推给 PR-7。

**修订理由**：避免 reviewer 在阅读 PR-6 改动时误以为本 PR 引入 P2 路由变化（仅删除内联，路由恢复由编排器 4c 接管，行为对齐 PR-3' 已合入的契约）。

---

### 2.3 文件 C · `phases/p2-spec-definition.md`（PHASE-D1）

#### 2.3.1 PHASE-D1（删除 Spec-Uncertain 内联 step-pause / O13）

**操作**：删除现有第 48-63 行整段：

```xml
            <check if="Spec 存在模糊性或来源冲突">
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior</action>
                <!-- ⚠️ v4.2 遗留 #6：本内联 <step-pause> 与编排器 step 4 case Spec-Uncertain
                     重复弹窗（已知 bug）；按 D14 收窄声明，v4.1 暂不动以避免 scope creep，
                     v4.2 整体迁出 phase 文件，由编排器统一调度。 -->
                <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
{spec_options}
">
                    <option title="[1] {option_1}
"/>
                    <option title="[2] {option_2}
"/>
                    <option title="[S] Skip：先并行分析所有可能，后续确认
" action="确认前对每种可能 Spec 分别分析"/>
                </step-pause>
            </check>
```

**替换为（O21 宏改写，3 行）**：

```xml
            <check if="Spec 存在模糊性或来源冲突">
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior，
                        将候选选项数组命名为 `{spec_options}`（供下方 phase-abort 宏 fields 字面引用，
                        编排器 4c 渲染 step-pause-registry.yaml `state: Spec-Uncertain` 项的
                        title_template 中 `{spec_options}` 占位时直接消费）</action>
                <phase-abort state="Spec-Uncertain"
                             fields='{"spec_options": "{spec_options}"}'
                             reason="ADR-014"/>
            </check>
```

**修订理由（V1.1 §3.2.13）**：
- O13a 已经统一了 Spec-Uncertain 契约为 `1|2|S` 三选（PR-3' 落地），phase 内联与编排器 case 已是完全等价的两份实现，删除内联即可消除 D14 重复弹窗 bug；
- 用 O21 宏 `<phase-abort>` 1 行表达，比原"显式 set_state + ABORT + 退出"5 步咒语更简洁，与 PR-3' 已落地的 P2 Non-Bug 早退（第 91-93 行）写法对齐；
- `fields` 参数显式写入 `spec_options`，让编排器 4c 的 step-pause `title_template` 渲染有数据源（与 P2 Non-Bug 早退把 `non_bug_context` 写入 fields 的范式 1:1 等价）。

#### 2.3.2 兼容性影响

- ① 用户体验完全等价（Cursor / Dify 双侧弹窗仍是 `1|2|S` 三选，title 渲染含 `{spec_options}`）；
- ② Limited 平台（Dify / Coze）原本按 phase 内联描述执行（system-prompt.md L293-298），本 PR 同步重建 system-prompt.md 后，Limited 平台改按编排器 step 4c 描述执行——双侧合龙到 registry 单一权威源；
- ③ CI Check 1 / Check 2 / Check 6（依赖 allowlist）下线后，本 phase 文件不再被任何 D14 守门特殊豁免（Check 15 升级 error 后会强校验本 phase 文件含 ≥ 1 个宏出口，本变更点提供 1 个 `<phase-abort>` 满足要求）。

---

### 2.4 文件 D · `phases/p4-fix-design.md`（PHASE-D2）

#### 2.4.1 PHASE-D2（删除 Fix Design Confirm 内联 step-pause + 改 phase-abort Fix-Confirming / O14）

**操作**：删除现有第 131-142 行整段：

```xml
        <step n="6" goal="回归测试设计与输出">
            <action>基于 Spec 和修改范围设计 TC1（直接验证）/ TC2（边界验证）/ TC3（回归验证）/ TC4（跨平台验证）/ TC5（专项附录验证，按需）。</action>
            <template-output file="{output_file}" template="mobile-qa-workflow/templates/fix-design.md"/>
            <action>更新 {config_source}：output_fix_design = {output_file}</action>
            <step-pause title="Fix Design 四重论证完成，请确认是否进入修复实施：
">
                <option title="[C] Continue：论证通过，进入 Phase 5 修复实施
" action="更新 {workflow_status}：current_state = Fix-Implementing, reroute_reason = null, reroute_target_phase = null"/>
                <option title="[R] Revise：修改方案后重新论证
" action="goto step 2"/>
            </step-pause>
        </step>
```

**替换为（O21 宏改写）**：

```xml
        <step n="6" goal="回归测试设计与输出">
            <action>基于 Spec 和修改范围设计 TC1（直接验证）/ TC2（边界验证）/ TC3（回归验证）/ TC4（跨平台验证）/ TC5（专项附录验证，按需）。</action>
            <template-output file="{output_file}" template="mobile-qa-workflow/templates/fix-design.md"/>
            <action>生成 Fix Design 简要摘要文本（≤ 200 字，覆盖：根因覆盖度 / 副作用风险 / 变更最小性 / 可回滚性
                    四个维度的 1 句话总结），**将该段文本命名为 `{fix_design_summary}`**（供下方 phase-abort 宏
                    fields 字面引用 + 编排器 4c 渲染 step-pause-registry.yaml `state: Fix-Confirming` 项
                    title_template 中 `{fix_design_summary}` 占位时直接消费）</action>
            <phase-complete state="Fix-Confirming"
                            fields='{"fix_design_summary": "{fix_design_summary}", "output_fix_design": "{output_file}"}'
                            reason="ADR-014"/>
        </step>
```

**修订理由（V1.1 §3.2.14）**：
- P4 step 6 是 Fix Design 阶段**正常完成**态（不是 ABORT），故用 `<phase-complete>` 而非 `<phase-abort>`（与 PR-3' Seg-1 在 P3 step 10 用 `<phase-complete state="Fix-Designing">` 的范式对齐）；
- `state="Fix-Confirming"` 触发编排器 step 4c 命中 registry 新增的 `Fix-Confirming` 项（详见 §2.1.1），由 4c 发起 step-pause 等待用户回复 Continue / Revise；
- `fields` 中 `output_fix_design` 字段同步写入（替代被删除的"更新 {config_source}：output_fix_design = {output_file}" 单独 action），与 phase-complete 宏的 `update_config` 参数解耦——本写入是 status 字段而非 config 字段，留 update_config 给后续真正的 config_source 更新使用；
- `fix_design_summary` 是新增的本轮局部变量（非 workflow_status 字段），仅用于 step-pause title 渲染，编排器 4c 完成本次 step-pause 派发后即丢弃（与 P2 Non-Bug 的 `non_bug_context` 字段不同——后者是顶层 schema 字段，前者只是宏 fields 内的临时占位）。

#### 2.4.2 关于 `fix_design_summary` 字段是否需要进 schema 的判断

**结论：不进 schema，仅作为本轮局部变量**。理由：
- 本字段与 `non_bug_context`（ADR-017 入 schema）的差异：`non_bug_context` 在 Non-Bug 跨轮回流（reflow）后仍需保留供下一轮判定参考；`fix_design_summary` 仅在 Fix-Confirming step-pause 单次渲染中使用，Continue → Fix-Implementing 后即不再需要，Revise → Fix-Designing 后会重新生成新摘要；
- 不进 schema 可避免 `workflow-status-template.yaml` 字段表持续膨胀（PR-2 O8 已经做过 schema 瘦身，本 PR 不再回潮）；
- 与编排器 4c 的展开规则一致——4c 渲染 title_template 时直接读 phase-abort/complete 的 fields 写回值，不依赖 schema 字段持久化。

#### 2.4.3 兼容性影响

- ① 用户体验完全等价（Continue / Revise 选项不变，Revise 仍跳回 Fix-Designing 并 +1 fix_retry_count）；
- ② P4 phase 文件首次包含宏出口，CI Check 15 的 `check_phase_has_macro` 函数对 P4 的 notice 提示（`scripts/check-phase-abort-structure.sh:144-145`）需要删除（详见 §2.13 SCRIPT-D3）；
- ③ Cursor / Trae 用户在 PR-3'+PR-5+PR-6 全部合入后，看到的 Fix Design 弹窗形态由"phase 内联 step-pause"变为"编排器 step 4c registry 渲染"——title 字符串多了 `{fix_design_summary}` 摘要段（更友好，但若 reviewer 不希望此变化，可通过 registry title_template 调整恢复成"无摘要"形态）。

---

### 2.5 文件 E · `core/workflow.xml`（XML-D1~D3）

#### 2.5.1 XML-D1（删除 step 4a 中 mirror_to_top 双写块 / 配套 v4.2 遗留 #3）

**操作**：删除现有第 120-123 行整段（在 step 4a 解析成功的 check 块内）：

```xml
                        <check if="该 registry 项 mirror_to_top == true">
                            <action>同步镜像写入 workflow_status.{key} = {value}
                                    （v4.2 PR-5 起仅 Non-Bug 一项；v4.2 遗留 #3 删除后本块一并下线）</action>
                        </check>
```

并同步删除第 191-192 行（在 step 4c on_success 派发后的清空块内）的 mirror_to_top 清空动作：

```xml
                            <action>派发完成后清空 user_inputs.{result_field}（消费一次性输入）；
                                    若 mirror_to_top == true，同步清空 workflow_status.{result_field}</action>
```

**替换为**：

```xml
                            <action>派发完成后清空 user_inputs.{result_field}（消费一次性输入 / v4.2 PR-6 起 mirror 双写已下线）</action>
```

#### 2.5.2 XML-D2（删除 ANCHOR-N2 注释段 + 删除 4c 内联过渡桥接说明）

**操作**：删除现有第 159-167 行（ANCHOR-N2 + 过渡桥接说明）：

```xml
                <!-- ANCHOR: spec-uncertain-allowed-values -->
                <!-- v4.2 PR-5 过渡锚点：PR-2 引入 ANCHOR-N2 用于 system-prompt sync 守门
                     （check-system-prompt-sync.sh / check-build-system-prompt-precondition.sh
                     依赖本锚点 + 锚点后窗口 25 行抓 allowed_values=）。XML-D1 step 4 重写后
                     Spec-Uncertain 字面已迁移到 step-pause-registry.yaml，本注释保留锚点 +
                     字面 allowed_values="1|2|S" 作为过渡桥接，与 registry 项 Spec-Uncertain
                     的 allowed_values: ["1", "2", "S"] 字面同源。PR-6 build-system-prompt.py
                     首次构建并把 registry 注入 sp 之后由 PR-6 同步删除本注释 + 把两脚本
                     抽取目标改为 registry.yaml（v4.2 PR-5 v1.1 落地，与 ADR-010 §6.6 衔接事项 #2 联动）。 -->
```

**替换为（一行说明，便于 git blame）**：

```xml
                <!-- v4.2 PR-6 落地：Spec-Uncertain 字面已 100% 迁移到 step-pause-registry.yaml
                     的 `state: Spec-Uncertain` 项；ANCHOR-N2 锚点已下线（详见 SCRIPT-D2 / SCRIPT-D4）。 -->
```

**修订理由**：ANCHOR-N2 是 PR-2/PR-5 时为 H1 守门（防止 PR-2 即兴运行 build-system-prompt.py 替换 system-prompt.md）服务的过渡锚点；PR-6 完成 system-prompt.md 首次自动构建后，sync 守门改为"声明块对声明块严格相等 + registry 字面对 registry 字面严格相等"形态，不再需要锚点窗口式扫描。

#### 2.5.3 XML-D3（io-contract 段 enum 集补全 / 与 TPL-D1 联动）

**操作**：本 PR 不修改 `<io-contract>` 块（其内容仅描述 phase 输入输出契约，与 enum 集解耦）；但在 step 2 的"读取 {workflow_status} 文件，获取 stepsCompleted, current_state ..." 这一行 action 后追加一行 enum 子集说明（便于 reviewer 一目了然新增字段）：

```xml
                <!-- v4.2 PR-6 enum 集变更：current_state 新增 Fix-Confirming
                     （位于 Fix-Designing 与 Fix-Implementing 之间，触发 P4 step 6 用户确认）；
                     权威源 core/workflow-status-template.yaml 头部 v4.2 完整集合注释。 -->
```

#### 2.5.4 兼容性影响

- ① 编排器 4a 单写路径（仅 user_inputs.<key>）与编排器 4c 不再依赖 mirror_to_top 标记 — 与 REG-D1 同步；
- ② step 4c 命中 `Fix-Confirming` 后按 registry on_success 自动派发 Continue → Fix-Implementing 或 Revise → Fix-Designing + fix_retry_count + 1，无需任何编排器侧硬编码 case（与 H3"零硬编码 case"一致）；
- ③ Check 16 第 ② 类 `EXPECTED_REGISTRY` 必须同步加入 `Fix-Confirming`，否则 PR-6 一合入瞬间 CI 红（详见 §2.13 SCRIPT-D3）。

---

### 2.6 文件 F · `core/core-rules.xml`（RULES-D1~D3）

#### 2.6.1 RULES-D1（input-protocol rule n=5 简化双写描述 / O12 配套）

**操作**：第 192-199 行 input-protocol rule n=5：

```xml
                    <rule n="5">
                        编排器恢复后采用"白名单受限双写"（D15）：
                          workflow_status.user_inputs.&lt;key&gt; = &lt;value&gt;       （总写）
                          workflow_status.&lt;key&gt; = &lt;value&gt;                  （仅当 &lt;key&gt; 在
                                                                                core/workflow-status-template.yaml
                                                                                顶层镜像白名单内才写）
                        v4.1 起步顶层镜像白名单 = { non_bug_user_choice }。
                    </rule>
```

**替换为（v4.2 PR-6 收口形态）**：

```xml
                    <rule n="5">
                        编排器 4a 解析成功后**单写**用户回复（v4.2 PR-6 起，详见 ADR-015 v4.2 修订段）：
                          workflow_status.user_inputs.&lt;key&gt; = &lt;value&gt;
                        编排器 / phase / system-prompt 引用用户回复值时，统一使用 {user_inputs.&lt;key&gt;} 形式。
                        历史顶层镜像字段（v4.1 起步白名单 = { non_bug_user_choice }）已于 v4.2 PR-6 全量下线。
                    </rule>
```

#### 2.6.2 RULES-D2（step-pause 标签 rule `step-pause-scope` 简化 / 删除 D19 例外条款）

**操作**：第 113-124 行 `<rule critical="true" id="step-pause-scope">` 整段重写：

**当前**：

```xml
                    <rule critical="true" id="step-pause-scope">
                        调度作用域约束（v4.1 / D14）：
                        &lt;step-pause&gt; 仅允许出现在 core/workflow.xml 编排器 step 4 内
                        （按 current_state 路由触发）；phase 文件
                        （phases/**、functionality-deep-dive/phases/**）禁止内联
                        &lt;step-pause&gt;。phase 早退应通过
                          &lt;action&gt;更新 {workflow_status}：current_state = &lt;stop_state&gt;&lt;/action&gt;
                          &lt;action&gt;设置 current_phase_result = ABORT&lt;/action&gt;
                        让编排器接管，由编排器 step 4 对应 case 统一触发 step-pause。
                        例外清单见 mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt
                        （v4.2 遗留 #6 治理目标，PR-5 维护、PR-8 CI 消费）。
                    </rule>
```

**替换为**：

```xml
                    <rule critical="true" id="step-pause-scope">
                        调度作用域约束（v4.1 / D14 / v4.2 PR-6 收口完成）：
                        &lt;step-pause&gt; 仅允许出现在 core/workflow.xml 编排器 step 4c 内
                        （按 current_state 命中 step-pause-registry.yaml 触发）；phase 文件
                        （phases/**、functionality-deep-dive/phases/**）**严禁**内联 &lt;step-pause&gt;。
                        phase 早退用 &lt;phase-abort state="..." fields="..." reason="..."/&gt; 宏，
                        phase 正常完成用 &lt;phase-complete state="..." .../&gt; 宏（详见 ADR-021）；
                        编排器 step 4c 命中 registry 项后按 ADR-010 §0 展开规则发起 step-pause。
                        v4.2 PR-6 起 D19 allowlist 例外清单已下线（physical removal），
                        CI 守门改为"零容忍"模式（详见 ADR-019 superseded 状态）。
                    </rule>
```

#### 2.6.3 RULES-D3（step-pause forms 块删除 inline 过渡形态 / 配套 ADR-016 v4.2 收口段）

**操作**：第 128-147 行 `<forms>` 块整段重写：

**当前**：

```xml
                <forms>
                    <!-- Inline 形态（v4.1 老写法 / PR-6 删除 phase 内联前过渡保留 / 仅 phase 文件残留例外） -->
                    <form name="inline">
                        <required>title, result_field, allowed_values</required>
                        <optional cardinality="0..*">option</optional>
                        <forbidden>registry-key</forbidden>
                        <expand>LLM 按 input-protocol rule n=1 输出强结构 [result_field=...][allowed_values=...]
                                并附 "请用 &lt;key&gt;=&lt;value&gt; 回复" 末尾行；编排器 4a 按 result_field 解析。</expand>
                    </form>
                    <!-- Registry 形态（v4.2 PR-5 起 / 编排器 4c 唯一形态） -->
                    <form name="registry">
                        <required>registry-key</required>
                        <forbidden>title, result_field, allowed_values, option</forbidden>
                        <expand>LLM 按 ADR-010 §0 展开规则查 core/step-pause-registry.yaml，
                                把 registry-key 命中项的 title_template / result_field / allowed_values / options
                                渲染为等价 inline 形态再按 input-protocol rule n=1 输出。</expand>
                    </form>
                    <mutex critical="true">两 form 必须命中且仅命中其中之一；同时含 registry-key 与 title
                                          / 同时缺两组关键字段，均判定为协议违规（check-io-contract.sh 互斥校验段 error）。</mutex>
                </forms>
```

**替换为（v4.2 PR-6 起 registry 形态成为唯一合法形态）**：

```xml
                <forms>
                    <!-- v4.2 PR-6 起 inline 形态已退役（phase 内联 step-pause 已 100% 迁出）；
                         registry 形态是唯一合法形态。inline 形态的字段定义保留在 ADR-016 主体作为
                         "registry 项渲染时遵守的等价输出契约"——LLM 把 registry-key 展开为等价 inline
                         形态后，按 input-protocol rule n=1 输出强结构。 -->
                    <form name="registry">
                        <required>registry-key</required>
                        <forbidden>title, result_field, allowed_values, option</forbidden>
                        <expand>LLM 按 ADR-010 §0 展开规则查 core/step-pause-registry.yaml，
                                把 registry-key 命中项的 title_template / result_field / allowed_values / options
                                渲染为等价输出契约（即 ADR-016 主体定义的强结构 + input-protocol rule n=1 末尾行）。</expand>
                    </form>
                    <single-form critical="true">v4.2 PR-6 起所有 &lt;step-pause&gt; 必须含 registry-key 且不含
                                                  title / result_field / allowed_values / option；违规由
                                                  check-io-contract.sh single-form 校验段 error（详见 SCRIPT-D5）。</single-form>
                </forms>
```

同步把 `<param name="title">` / `<param name="result_field">` / `<param name="allowed_values">` 三个 param 的 `required="form:inline"` 改为 `required="false"`（不删除参数定义，保留作为"registry 项渲染时的等价输出契约"参考），并追加注释"v4.2 PR-6 起 inline 形态已退役"。

#### 2.6.4 兼容性影响

- ① 任何遗留 inline 形态的 step-pause（含 phases / system-prompt / functionality-deep-dive/phases）必须 100% 删除，否则 SCRIPT-D5 校验红（本 PR 已通过 PHASE-D1/D2 + SP-N1 删除全部 inline 形态）；
- ② functionality-deep-dive/phases/** 当前不含任何 `<step-pause>`（PR-5 v1.1 子文档 §1.4 已确认），本 PR 不做特殊处理；
- ③ 若未来需要再次引入 inline 形态（如新平台特殊需求），必须先评估对 D14 治理的回潮风险，并通过新 ADR + 配套 CI 守门支持。

---

### 2.7 文件 G · `system-prompt.md`（SP-N1）

#### 2.7.1 SP-N1（首次自动构建并替换 / O17+ Stage-1 / 解 H1）

**操作**：分两步执行：

**Step 1 — 首次构建**：

```bash
cd $REPO_ROOT/mobile-qa-workflow
ALLOW_FIRST_BUILD=1 python3 scripts/build-system-prompt.py --mode=full --output=system-prompt.md
```

**Step 2 — 人工 diff 验证**：

```bash
git diff -- system-prompt.md > /tmp/sp-pr6-diff.patch
# 由 reviewer 人工通读 diff，确认零业务语义差异
```

#### 2.7.2 必须人工 diff 验证的关键变化点（reviewer checklist）

| 验证点 | 期望结果 | 备注 |
|------|---------|------|
| ENUM-DECLARATION-BLOCK | 16 项 enum，含 `Fix-Confirming` | 由 build_l0_identity 中 STATE_TRANSITIONS_HUMAN 渲染 |
| Phase 2 step 3 内联 step-pause 描述 | **已删除** | 由 build_l2_phase_logic 抽取 phase 文件得到（无 step-pause 节点） |
| Phase 4 step 6 内联 step-pause 描述 | **已删除** | 同上 |
| Spec-Uncertain ANCHOR 注释（ANCHOR-N1） | **已删除** | 生成器不输出过渡锚点 |
| 顶层镜像白名单段落（D15 双写白名单受限说明） | **已删除** | 由 build_l1_execution_rules 抽取 core-rules.xml 得到（已含 RULES-D1 修订） |
| 双写白名单 / `non_bug_user_choice` 顶层引用 | **已删除** | 全部改为 `{user_inputs.<key>}` 引用 |
| `<phase-abort>` / `<phase-complete>` 4/5 步展开规则（O21 / ADR-021） | **完整保留** | 来自 PR-3' Seg-1 已写入 system-prompt 0.2 节，生成器需在 build_l1_execution_rules 中追加该段抽取（见 §2.16 GEN-D1） |
| Phase 列表 step-pause-registry 路由表 | **新增** | 从 `core/step-pause-registry.yaml` 渲染（见 §2.16 GEN-D2） |
| `Fix-Confirming` 在状态机图中的位置 | 位于 `Fix-Designing → Fix-Confirming → Fix-Implementing` 链路 | 状态机图由生成器从 STATE_TRANSITIONS_HUMAN 模板加 enum 集渲染 |
| L3 推理工具箱 OVHSC | **完整保留**（V1 §6 第 1 条不可触动） | 来自 reasoning-chain.md |
| L4 平台知识 Android + iOS 段 | **完整保留** | 来自 platform-checklist.md |

#### 2.7.3 文件头注释更新（生成器输出后人工微调一行）

构建完成后，文件第 12 行 `@ sync-check=2026-04-21（PR-1 落地基线）` 改为：

```
@ sync-check=2026-04-XX（PR-6 首次自动构建基线）
@ build-cmd=ALLOW_FIRST_BUILD=1 python3 scripts/build-system-prompt.py --mode=full --output=system-prompt.md
```

并把"⚠️ 本文件当前为'手维护'状态"段落改为"✅ 本文件由 `scripts/build-system-prompt.py` 自动构建；任何手改将被 CI Check 14 (build-system-prompt 单测) + Check 10 (system-prompt-sync) 拦截。"

#### 2.7.4 兼容性影响

- ① **Limited 平台（Dify / Coze）行为变化**：原本基于 system-prompt.md 内 P2/P4 内联 step-pause 描述执行，本 PR 后改为依据"编排器 step 4c registry 单一权威源"描述执行——必须 5+ 用例双侧（Cursor + Dify）人工抽查弹窗一致性（README §5 PR-6 行强制要求）；
- ② Limited 平台首次接收新 system-prompt 时建议人工读 ≥ 5 个会话的 LLM 思考过程，确认"按 registry 渲染 step-pause"的行为正确（H3 接纳要求 / V1.1 §3.2.21）；
- ③ system-prompt.md 行数变化（预估 569 行 → ~480 行，减少约 15%）——主要来自删除 inline step-pause 描述 + 删除白名单段落 + 删除 ANCHOR 注释。

---

### 2.8 文件 H · `PLATFORM-GUIDE.md`（DOC-D1）

#### 2.8.1 DOC-D1（删除"顶层镜像白名单"段落 / O12 配套）

**操作**：删除现有第 28 行后半段 + 第 60 行整段：

第 28 行后半段（"顶层镜像字段（v4.1 起步白名单 = `{ non_bug_user_choice }`）由编排器对 step-pause 用户回复执行**白名单受限双写**..."以及"v4.2 收敛后才会改读 `user_inputs.<key>` 并删除顶层镜像字段。**接入方不得删除编排器侧的镜像读写逻辑**。"）整段删除。

第 60 行（"⚠️ **顶层镜像字段白名单（v4.1 D8 + D15）**：v4.1 起步白名单 = `{ non_bug_user_choice }`...v4.2 整体收敛后将删除所有顶层镜像字段，编排器统一改读 `user_inputs.<key>`"）整段删除。

**替换为（精简版 v4.2 收口形态，~3 行）**：

```markdown
- step-pause 用户回复统一写入 `workflow_status.user_inputs.<result_field>` 命名空间（v4.2 PR-6 起，详见 ADR-015 v4.2 修订段）；编排器 / phase / system-prompt 引用用户回复值时统一使用 `{user_inputs.<key>}` 形式。
```

并相应在第 53-58 行"至少持久化字段"列表中的"Non-Bug 三字段（职责正交）"段删除 `non_bug_user_choice`，仅保留 `non_bug_reflow_count` + `non_bug_context`，并补一行说明"用户选择走 `user_inputs.non_bug_user_choice` 不进顶层 schema"。

#### 2.8.2 兼容性影响

- ① 接入方文档简化（不再需要维护"白名单"复杂度），与 V1.1 §3.2.12 收益对齐；
- ② 现存接入方（参见 v4.1 PR-7 PLATFORM-GUIDE 改动）若仍依赖顶层 `non_bug_user_choice` 字段，需在 v4.2 升级文档中明确告知改读 `user_inputs.non_bug_user_choice`（建议在 PR-6 changelog 中显式列出）。

---

### 2.9 文件 I · `scripts/legacy-phase-step-pause-allowlist.txt`（FILE-D1）

#### 2.9.1 FILE-D1（物理删除文件 / D14 整改清零）

**操作**：

```bash
git rm mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt
```

**修订理由**：D14 治理目标是 v4.2 整改清零（ADR-019 §2 第 4 条 / "v4.2 遗留 #6 整改完成时，本文件应被清空并删除"）。本 PR 删除 P2 + P4 两条内联 step-pause 后，文件中 2 条 allowlist 条目已无对应源码命中（CI Check 2 反向校验会触发 D19-DRIFT），物理删除是清零的必然动作。

#### 2.9.2 兼容性影响

- ① CI Check 1 / Check 2 / Check 6 全部依赖本文件存在，必须同步下线或调整（详见 §2.14 CI-D1）；
- ② `check-io-contract.sh` step-pause-mutex 段当前依赖本文件做豁免（脚本第 75-90 行），必须同步删除豁免逻辑（详见 §2.11 SCRIPT-D1）；
- ③ ADR-019 状态由 active → superseded（详见 §2.15 ADR-D3）。

---

### 2.10 文件 J · `scripts/check-io-contract.sh`（SCRIPT-D1）

#### 2.10.1 SCRIPT-D1（删除 allowlist 豁免 + 由 mutex 校验改为 single-form 校验）

**操作**：

**变更 1**：删除 `mutex_check_file()` 函数中第 84-100 行的 allowlist 加载与"is_legacy 豁免"逻辑：

```bash
# 加载 allowlist：(repo_relative_path, expected_line) 元组列表
legacy_entries = []
if os.path.isfile(allowlist_path):
    for raw in open(allowlist_path, encoding='utf-8'):
        ...
```

**变更 2**：删除函数内"allowlist 豁免（v4.2 遗留 #6 / 与 D14/D16 同口径 / ±5 行漂移）"分支（第 149-158 行）：

```python
is_legacy = False
for ep, el in legacy_entries:
    if ep == repo_path and abs(start_line - el) <= 5:
        is_legacy = True
        break
if is_legacy:
    n_skipped_legacy += 1
    i = j + 1
    continue
```

**变更 3**：把"3) 形态判定"分支（第 161-173 行）改为单形态校验：

```python
# v4.2 PR-6 收口：registry 形态成为唯一合法形态
has_reg   = bool(re.search(r'\bregistry-key\s*=', attrs))
has_inline_field = bool(re.search(r'\b(title|result_field|allowed_values|option)\s*=', attrs))
n_checked += 1

if not has_reg:
    print(f"::error::step-pause-single-form-no-registry / {target}:{start_line} / 缺 registry-key（v4.2 PR-6 起 inline 形态已退役）")
    fail = 1
elif has_inline_field:
    print(f"::error::step-pause-single-form-mixed / {target}:{start_line} / 含 registry-key 时禁止同时含 title/result_field/allowed_values/option")
    fail = 1
```

**变更 4**：脚本头注释段（第 64-72 行）的"`<step-pause>` 互斥校验段"段名改为"single-form 校验段"，并把豁免说明改为"PR-6 落地后 phase 内联已 100% 清零，无任何豁免"。

#### 2.10.2 兼容性影响

- ① PR-6 合入瞬间，所有 `<step-pause>` 必须只剩 registry 形态（编排器 4c 内的 1 处 + functionality-deep-dive 内 0 处 = 1 处全仓 step-pause），否则 CI 红；
- ② 本变更前提是 PHASE-D1 + PHASE-D2 + SP-N1 全部已完成（前置依赖明确）。

---

### 2.11 文件 K · `scripts/check-system-prompt-sync.sh`（SCRIPT-D2）

#### 2.11.1 SCRIPT-D2（升级抽取算法 / 加入 registry 字面对 registry 字面校验）

**操作**：

**变更 1**：把 `ENUM_CORE` 的 python 提取正则由 `v4\.1\s*完整集合` 改为 `v4\.[12]\s*完整集合`（兼容 TPL-D1 改动）。

**变更 2**：把 `ENUM_SP` 的 python 提取保持不变（system-prompt.md 中 ENUM-DECLARATION-BLOCK 是声明块，不依赖锚点）。

**变更 3**：完全删除"2a) Spec-Uncertain ANCHOR 提取式比对"段（第 70-99 行），改为新增"2a) step-pause-registry 字面同步校验"：

```bash
# ──────────────────────────────────────────────────────────
# 校验 2a：step-pause-registry 字面同步校验（v4.2 PR-6 起）
# v4.2 PR-6 替换 ANCHOR-N1/N2 锚点扫描机制：直接对比 system-prompt.md 中
# Phase 4 step 4 描述段的 step-pause 路由表（生成器输出）与 core/step-pause-registry.yaml
# 中 7 项交互态 + 1 项路由态的 state / result_field / allowed_values 字面是否完整出现。
# ──────────────────────────────────────────────────────────
REG_STATES=$(python3 -c "import re; print('\n'.join(re.findall(r'^\s*-\s*state:\s*([A-Za-z][A-Za-z0-9-]*)', open('core/step-pause-registry.yaml').read(), flags=re.M)))")

for st in $REG_STATES; do
  if ! grep -q "$st" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺 registry state 引用: $st"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done
```

**变更 4**：保留"2b) 关键 stop_state 必须出现 ≥ 1 次"段，但把 stop_state 列表加入 `Fix-Confirming`：

```bash
for state in "Non-Bug" "RCA-LowConfidence" "Curation-Failed" "Human-Review" "Fix-Confirming"; do
  if ! grep -q "$state" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺关键 stop_state 引用: $state"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done
```

#### 2.11.2 兼容性影响

- ① ANCHOR-N1/N2 抽取算法下线后，本脚本与 `check-build-system-prompt-precondition.sh`（详见 §2.13）解耦；
- ② SP-N1 首次构建后必须保证 8 项 registry state（含 Fix-Confirming）在 system-prompt.md 中至少出现 1 次（生成器输出会自然满足，详见 §2.16 GEN-D2）；
- ③ 升级 ENUM 比对算法兼容 v4.1 / v4.2 双版本（兼容 PR-6 合入到 main 之前的过渡期）。

---

### 2.12 文件 L · `scripts/check-phase-abort-structure.sh`（SCRIPT-D3）

#### 2.12.1 SCRIPT-D3（默认严重度升级 error + ENUM 抽取兼容 v4.2 + 删除 P4 notice）

**操作**：

**变更 1**：第 26 行严重度切换：

```bash
SEVERITY="${PHASE_ABORT_SEVERITY:-error}"   # v4.2 PR-6 起默认 error；warning 模式仅供本地调试
```

**变更 2**：第 40-71 行 ENUM_SET 提取的 python 块中，把 `'v4.1 完整集合' in ln` 改为：

```python
if not collect and ('v4.1 完整集合' in ln or 'v4.2 完整集合' in ln):
```

**变更 3**：删除 `check_phase_has_macro()` 函数中第 144-145 行 P4 notice：

```bash
if [[ "$file" == *p4-fix-design* ]]; then
  echo "::notice::$file: P4 未用宏（PR-6 删除内联 step-pause 后改写 / 详见主文档 §2.3.2）"
else
  ...
fi
```

替换为统一的 emit error 分支（无 P4 特例）：

```bash
if grep -qE '<phase-(abort|complete)\b' "$file"; then
  return 0
fi
emit "$SEVERITY" "$file: 未发现任何 phase-complete/abort 宏（phase 文件至少需含 1 处宏出口）"
```

**变更 4**：脚本头部注释段（第 13-15 行）"Severity 切换"块改为：

```bash
# Severity 切换：
#   PHASE_ABORT_SEVERITY=warning（PR-3' 起步，PR-6 前 main 默认值）
#   PHASE_ABORT_SEVERITY=error  （v4.2 PR-6 起默认 / D14 收口完成）
```

#### 2.12.2 兼容性影响

- ① P4 在 PHASE-D2 落地后含 1 处 `<phase-complete state="Fix-Confirming">`，新校验逻辑会通过；
- ② 升级 error 后，未来任何 phase 文件新增时若无宏出口会直接 CI 红——预期效果，与 D14 治理目标对齐；
- ③ ENUM 抽取兼容双版本，与 SCRIPT-D2 算法升级原因一致。

---

### 2.13 文件 M · `scripts/check-step-pause-registry.sh`（SCRIPT-D4）

#### 2.13.1 SCRIPT-D4（EXPECTED 集补全 + ENUM 抽取兼容 v4.2）

**操作**：

**变更 1**：第 19-23 行 ENUM_SET 提取（与 SCRIPT-D3 同款修复）：

```bash
ENUM_SET=$(python3 - "$TPL" <<'PY'
...
    if not collect and ('v4.1 完整集合' in ln or 'v4.2 完整集合' in ln): collect = True; continue
...
PY
)
```

**变更 2**：第 39 行 EXPECTED 集加入 `Fix-Confirming`：

```bash
# v4.2 PR-6：6 个交互态 + Fix-Confirming + 1 个路由态 Boundary-Refined
EXPECTED="Info-Insufficient Spec-Uncertain Non-Bug RCA-LowConfidence Curation-Failed Human-Review Fix-Confirming Boundary-Refined"
```

**变更 3**：第 ③ 类硬编码 case 黑名单（python 提取段，第 458-463 行）已包含 `Fix-Confirming`（PR-5 子文档 §2.4 已前向兼容预留），本 PR 无需修改。

#### 2.13.2 兼容性影响

- ① EXPECTED 加入 `Fix-Confirming` 后，registry 必须含本条目（REG-N1 已提供），否则双向严格相等校验红；
- ② 编排器 step 4 区间内若硬编码 `<case if="Fix-Confirming">` 会被 ③ 类校验拦截——预期效果。

---

### 2.14 文件 N · `scripts/check-build-system-prompt-precondition.sh`（SCRIPT-D5）

#### 2.14.1 SCRIPT-D5（脚本物理下线 / 完成历史使命）

**操作**：

```bash
git rm mobile-qa-workflow/scripts/check-build-system-prompt-precondition.sh
```

**修订理由**：本脚本是 PR-2 引入的 H1 守门——禁止 PR-2 阶段即兴运行 build-system-prompt.py 替换 system-prompt.md。PR-6 是 H1 设计的解锁触发点（README §3 H1 / 主控 §3 H1）：本 PR 一旦完成 SP-N1 首次构建并替换，H1 守门的"防御目标"已不复存在，脚本失去价值。

#### 2.14.2 替代守门

H1 守门下线后，sync 安全网由以下脚本接管：
- `check-system-prompt-sync.sh`（SCRIPT-D2 升级版）：保证 system-prompt.md 与 core/ 关键 token 同步；
- `check-state-enum.sh`（PR-1 落地）：保证 enum 集 state 写入合法；
- `check-phase-abort-structure.sh`（SCRIPT-D3 升级版）：保证 phase 出口宏结构正确；
- `check-step-pause-registry.sh`（SCRIPT-D4 升级版）：保证 registry 双向严格相等 + 硬编码 case 禁出。

四件套联防的 sync 安全网比单点 H1 锚点更强，无需保留 H1 残留。

---

### 2.15 文件 O · `.github/workflows/qa-workflow-schema-check.yml`（CI-D1）

#### 2.15.1 CI-D1（5 项 Check 调整 / 1 项升级 / 1 项删除）

**操作**：

| Check 编号 | 当前状态 | PR-6 操作 | 理由 |
|----------|---------|---------|------|
| Check 1 — D16 step-pause 完整参数 | 依赖 ALLOWLIST 跳过 legacy | **整段删除**（含 ALLOWLIST 加载块） | inline 形态退役，参数完整性由 SCRIPT-D1 single-form 校验 + registry schema 自校验承担 |
| Check 2 — D14 调度作用域 + D19 allowlist 双向匹配 | 依赖 ALLOWLIST | **整段删除** | D14 整改清零，无 phase 内联 step-pause 残留可校验 |
| Check 3 — D15 顶层白名单守门 | 抽 WHITELIST 非空检查 | **整段删除** | TPL-D2 删除顶层 `non_bug_user_choice` 后白名单段已下线，本 Check 无校验对象 |
| Check 4 — 顶层镜像字段过渡注释（v4.2 收敛 / 遗留 #3） | 检查 `non_bug_user_choice` 顶层注释带 "v4.2 收敛/遗留 #3" | **整段删除** | 顶层字段已删除，无校验对象 |
| Check 5 — 迁移脚本存在性 (D13 路径锁定) | 仅校验脚本物理存在 | **保持不变** | 与 PR-6 无关 |
| Check 6 — D19 allowlist 存在/非空/格式 (固化计数 == 2) | 强校验 allowlist == 2 行 | **整段删除** | allowlist 文件已删除（FILE-D1） |
| Check 7 — M16 config-schema 键漂移 | 调用独立脚本 | **保持不变** | 与 PR-6 无关 |
| Check 8 — D18 parse-error 4 类生命周期 | 4 类正则全在 workflow.xml 内 | **保持不变** | XML-D1/D2 删除的是 mirror_to_top 块，不影响 parse_error_count 4 类动作 |
| Check 9 — state enum 守门 | 调用 check-state-enum.sh | **保持不变** | check-state-enum.sh 提取正则由 SCRIPT 同步升级（独立改动，详见 §2.15.2） |
| Check 10 — system-prompt sync 守门 | 调用 check-system-prompt-sync.sh | **保持不变**（脚本由 SCRIPT-D2 升级） | 同上 |
| Check 11 — io-contract 守门 | env IO_CONTRACT_SEVERITY=warning | **升级为 error**（同时由 SCRIPT-D1 升级单形态校验后，本 Check 内置 single-form 校验段也升级） | 与 PR-2 README §4 表中"PR-2 评估升级 error"承诺对齐 |
| Check 12 — subagent-params 守门 | error 起步 | **保持不变** | 与 PR-6 无关 |
| Check 13 — build-system-prompt precondition 守门 | error，依赖 ANCHOR-N1/N2 | **整段删除** | 配套 SCRIPT-D5 物理删除 |
| Check 14 — build-system-prompt + p3-reentry replay tests | 跑 unittest discover | **保持不变**（生成器单测随 GEN-D1/D2 同步增加） | 单测增量在 §2.16.3 |
| Check 15 — phase-abort/complete 宏结构守门 | env PHASE_ABORT_SEVERITY=warning | **删除 env 行**（脚本默认值已升级 error，详见 SCRIPT-D3） | 与 README §4 表中"PR-6 升级 error"承诺对齐 |
| Check 16 — step-pause-registry 守门 | error 起步 | **保持不变**（EXPECTED 集由 SCRIPT-D4 同步加入 Fix-Confirming） | 同上 |

#### 2.15.2 配套：`scripts/check-state-enum.sh` 提取正则升级

虽然 README 列表中本脚本是 PR-1 落地，但其提取算法依赖 `v4.1 完整集合` 锚点，与 TPL-D1 相同问题。本 PR 同步把脚本内 `awk '/v4.1 完整集合/,/^[^#]/'` 的正则改为 `awk '/v4\\.[12] 完整集合/,/^[^#]/'`（最小入侵改动，与 SCRIPT-D2/D3/D4 ENUM 升级同款）。

#### 2.15.3 兼容性影响

- ① 删除的 5 个 Check（1/2/3/4/6/13）= **6 项 CI 守门**，均因校验对象已下线（allowlist 文件 / 顶层白名单字段 / 顶层镜像注释 / ANCHOR）；
- ② Check yml 总数由 16 → 10（净减 6 项），CI 时长预估缩短 ~30s；
- ③ 升级 error 的 2 项（Check 11 / Check 15）+ 升级到 error 的 1 项（Check 16 EXPECTED 加 Fix-Confirming）= 形成强约束环路，PR-6 后再无 sync 漂移空隙。

---

### 2.16 文件 P · `scripts/build-system-prompt.py`（GEN-D1~D3）

#### 2.16.1 GEN-D1（build_l1_execution_rules 增加 phase-abort/complete 宏展开规则抽取）

**操作**：在 `build_l1_execution_rules()` 函数（脚本第 130 行）中，从 `core/core-rules.xml` 抽取 `<tag name="phase-abort">` + `<tag name="phase-complete">` 块，并按规则展开为 markdown 友好的 4/5 步说明（与 PR-3' 已在 system-prompt.md 0.2 节写入的内容字面同源）。

**新增代码片段（追加在 input_protocol 提取之后）**：

```python
    phase_abort_rule = _extract_section(
        core_rules, r'^\s*<tag name="phase-abort">', r"^\s*</tag>"
    )
    phase_complete_rule = _extract_section(
        core_rules, r'^\s*<tag name="phase-complete">', r"^\s*</tag>"
    )

    if phase_abort_rule:
        parts.append("## phase-abort 宏展开规则（O21 / ADR-021）\n\n```xml\n" + phase_abort_rule.strip() + "\n```\n")
    if phase_complete_rule:
        parts.append("## phase-complete 宏展开规则（O21 / ADR-021）\n\n```xml\n" + phase_complete_rule.strip() + "\n```\n")
```

#### 2.16.2 GEN-D2（新增 build_l1_step_pause_routing_table 函数注入 registry 路由表）

**操作**：在 `build_l1_execution_rules()` 末尾追加 step-pause-registry 路由表渲染：

```python
def _build_routing_table(workflow_root: Path) -> str:
    """从 step-pause-registry.yaml 渲染 8 项 state 的简表。"""
    path = workflow_root / "core" / "step-pause-registry.yaml"
    if not path.is_file():
        return ""
    text = _read(path)
    items = re.findall(
        r'^\s*-\s*state:\s*([A-Za-z][A-Za-z0-9-]*)\s*\n((?:.|\n)*?)(?=^\s*-\s*state:|\Z)',
        text,
        re.M,
    )
    rows = ["| state | result_field | allowed_values |", "|---|---|---|"]
    for state, body in items:
        rf_m = re.search(r'result_field:\s*([^\n]+)', body)
        av_m = re.search(r'allowed_values:\s*\[([^\]]+)\]', body)
        kind_m = re.search(r'kind:\s*route', body)
        rf = rf_m.group(1).strip() if rf_m else "(route)"
        av = av_m.group(1).strip() if av_m else "(route)"
        rows.append(f"| `{state}` | `{rf}` | `{av}` |")
    return "## step-pause-registry 路由表（v4.2 PR-6 起 / O10+ + O14）\n\n" + "\n".join(rows) + "\n"
```

并在 `build_l1_execution_rules()` 末尾 `parts.append(_build_routing_table(workflow_root))`。

#### 2.16.3 GEN-D3（单元测试增量）

**操作**：在 `scripts/tests/test_build_system_prompt.py`（PR-2 已建）追加：

| 测试用例 | 验证目标 |
|---------|---------|
| `test_l1_includes_phase_abort_rule` | build_l1 输出含 `## phase-abort 宏展开规则` 段 |
| `test_l1_includes_phase_complete_rule` | build_l1 输出含 `## phase-complete 宏展开规则` 段 |
| `test_l1_includes_step_pause_routing_table` | build_l1 输出含 8 项 state（含 Fix-Confirming）的 markdown 表格 |
| `test_full_mode_emits_fix_confirming_in_enum` | full mode 输出 ENUM-DECLARATION-BLOCK 含 `Fix-Confirming` |
| `test_full_mode_no_inline_step_pause` | full mode 输出**不含** `<step-pause title=` 行（registry 形态除外） |
| `test_verify_mode_passes_v42` | verify mode 在含 `Fix-Confirming` enum 时通过（不报 illegal） |

**verify_core_consistency 算法升级**：脚本第 282-285 行的 `ENUM_BLOCK_REGEX` 由 `r"v4\.1\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)"` 改为 `r"v4\.[12]\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)"`（兼容 v4.1 / v4.2）。

#### 2.16.4 兼容性影响

- ① 生成器输出的 system-prompt.md 自然包含 ADR-021 宏展开规则 + registry 路由表，与 SCRIPT-D2 升级后的"registry 字面同步校验"形成正向闭环；
- ② 单测覆盖率提升，PR-2 留下的 6 个 unittest 增加 6 个 = 12 个，全部 must pass。

---

### 2.17 文件 Q · ADR 文档调整（ADR-D1~D6）

#### 2.17.1 ADR-D1（`doc/adr/014-step-pause-scope-restriction.md` / 追加 PR-6 收口段）

**操作**：在文末追加新段：

```markdown
## 7. v4.2 PR-6 收口纪要 — D14 整改清零（O13 + O14 / 2026-04-XX）

**收口动作**：
1. 删除 `phases/p2-spec-definition.md:53` Spec-Uncertain 内联 step-pause（O13）；
2. 删除 `phases/p4-fix-design.md:135` Fix Design Confirm 内联 step-pause（O14）；
3. `step-pause-registry.yaml` 新增 `Fix-Confirming` 注册表项；
4. `workflow-status-template.yaml` enum 集新增 `Fix-Confirming`；
5. `legacy-phase-step-pause-allowlist.txt` 物理删除（ADR-019 同步 superseded）；
6. CI Check 1 / Check 2 / Check 6 / Check 13 全部下线（依赖对象已不存在）；
7. CI Check 15（`check-phase-abort-structure.sh`）严重度由 warning 升级 error。

**收口后契约**：
- phase 文件（`phases/**`、`functionality-deep-dive/phases/**`）**严禁**任何 `<step-pause>` 内联（无例外清单）；
- phase 早退用 `<phase-abort>` 宏（ADR-021）；phase 正常完成可选用 `<phase-complete>` 宏；
- 编排器 step 4c 命中 `step-pause-registry.yaml` 后渲染 step-pause（registry 形态唯一）；
- CI single-form 校验由 `check-io-contract.sh` step-pause-single-form 段强制（详见 ADR-016 v4.2 修订段第二次更新）。

**关联**：
- ADR-019（superseded / allowlist 物理删除）
- ADR-016 v4.2 修订段（PR-6 第二次更新：删除 inline 形态过渡声明）
- ADR-021（宏标签全 phase 应用）
- ADR-010 §6 PR-5 落地纪要 + §7 PR-6 收口纪要（registry 含 Fix-Confirming）
```

#### 2.17.2 ADR-D2（`doc/adr/016-step-pause-required-params.md` / 追加 PR-6 第二次修订段）

**操作**：在 v4.2 修订段（PR-5 落地）之后追加：

```markdown
## v4.2 修订段 #2（PR-6 收口 / 2026-04-XX / 关联 ADR-014 收口纪要）

**变化背景**：PR-6 完成 D14 整改清零（O13 + O14）后，phase 内联 `<step-pause>` 已 100% 删除，
inline 形态失去存在场景。`core/core-rules.xml` `<tag name="step-pause"><forms>` 块已删除
inline `<form>` 定义，仅保留 registry 形态。

**两形态契约（v4.2 PR-6 收口形态）**：

| 形态 | 必填参数 | 禁出参数 | 适用范围 |
|---|---|---|---|
| ~~`inline`~~ | ~~`title` + `result_field` + `allowed_values`~~ | ~~`registry-key`~~ | **v4.2 PR-6 起退役** |
| `registry` | `registry-key` | `title` + `result_field` + `allowed_values` + `option` | 编排器 4c（唯一合法形态） |

**inline 形态字段定义保留作用**：原 ADR-016 主体的 `<step-pause>` 必填参数表保留作为
"registry 项渲染时遵守的等价输出契约"——LLM 把 `registry-key` 展开为等价 inline 形态后，
按 `input-protocol` rule n=1 输出强结构 `[result_field=...][allowed_values=...]` + 末尾行
"请用 <key>=<value> 回复"。

**强约束**：
1. 所有 `<step-pause>` 必须含 `registry-key` 且不含 `title` / `result_field` / `allowed_values` / `option`；
2. single-form 违规由 `scripts/check-io-contract.sh` step-pause-single-form 段（CI-D1 升级版）error；
3. inline 形态相关参数定义在 `core-rules.xml` 中保留，但 `required` 属性已从 `form:inline` 改为 `false`。
```

#### 2.17.3 ADR-D3（`doc/adr/019-legacy-step-pause-allowlist.md` / 状态切换 superseded）

**操作**：

**变更 1**：把文件头"状态：active"改为：

```markdown
> **状态**：superseded-by-v4.2-PR-6（v4.2 D14 整改清零 / 详见 ADR-014 §7）
```

**变更 2**：在文末追加 `## 6. 退役纪要（v4.2 PR-6 / 2026-04-XX）`：

```markdown
## 6. 退役纪要（v4.2 PR-6 / 2026-04-XX）

**退役条件**：
- D14 整改清零（O13 + O14 / phase 内联 step-pause 0 处）→ allowlist 文件中 2 条条目均无对应源码命中；
- ADR-014 §7 PR-6 收口纪要承接本 ADR 的"D14 例外清单"管理职责（v4.2 PR-6 起无任何例外）。

**物理动作**：
1. `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 物理删除；
2. CI Check 1 / Check 2 / Check 6 全部下线；
3. `scripts/check-io-contract.sh` step-pause-mutex 段升级为 single-form 校验段（详见 ADR-016 v4.2 修订段 #2）。

**v4.3 演进**：本 ADR 完整退役（无后续动作）；ADR-014 §7 与 ADR-016 v4.2 修订段 #2 共同承接 D14 治理职责。
```

#### 2.17.4 ADR-D4（`doc/adr/015-userinputs-mirror-allowlist.md` / 追加 v4.2 修订段）

**操作**：在文末追加：

```markdown
## 6. v4.2 PR-6 修订段 — 顶层镜像白名单全量下线（O12 收尾 / 2026-04-XX）

**变化背景**：v4.1 起步白名单 = `{ non_bug_user_choice }`（仅 1 项）的"白名单元协议"维护成本
（PR Review + CI 4 个 Check + 跨文档说明）显著高于其收益。v4.2 PR-6 完成 O12 收尾：
保留双写实现已不必要（编排器 4a 改为单写 user_inputs.<key>），同步删除顶层镜像字段定义。

**收口动作**：
1. `core/workflow-status-template.yaml` 删除顶层 `non_bug_user_choice` 字段（TPL-D2）；
2. `core/workflow-status-template.yaml` 删除"⚠️ 顶层镜像字段白名单"注释段（TPL-D2）；
3. `core/workflow.xml` step 4a 删除 mirror_to_top 双写分支（XML-D1）；
4. `core/step-pause-registry.yaml` 删除 Non-Bug 项 mirror_to_top 标记（REG-D1）；
5. `core/core-rules.xml` `<input-protocol>` rule n=5 简化为单写描述（RULES-D1）；
6. `system-prompt.md` 全量重写后不含"白名单受限双写"段（SP-N1）；
7. `PLATFORM-GUIDE.md` 删除顶层镜像白名单说明（DOC-D1）；
8. CI Check 3 / Check 4 全部下线（依赖白名单段已不存在）。

**收口后契约**：
- 编排器 4a 解析 step-pause 用户回复后**仅写入** `user_inputs.<result_field>`（单写）；
- phase / system-prompt / PLATFORM-GUIDE 引用用户回复值时，统一使用 `{user_inputs.<key>}` 形式；
- 历史镜像字段恢复路径：若未来需要恢复某字段顶层镜像（罕见），需通过新 ADR 评估，绑定 schema 复活 + 编排器双写改造 + CI 守门重建。

**关联**：
- ADR-008（v4.2 PR-6 修订段：顶层镜像协议正式退役）
- ADR-014 §7 PR-6 收口纪要
- ADR-019 superseded
```

#### 2.17.5 ADR-D5（`doc/adr/008-step-pause-userinputs-namespace.md` / 追加 v4.2 修订段，与 ADR-D4 联动）

**操作**：在文末追加：

```markdown
## v4.2 PR-6 修订段（2026-04-XX）

**变化**：v4.1 起步的"双写过渡总框架"已于 v4.2 PR-6 完成单写收口（详见 ADR-015 §6）。
编排器 4a 现在统一走 `user_inputs.<key>` 单写路径，顶层镜像字段全量下线。

**当前契约**：
- `<step-pause>` 触发的写回 = `user_inputs.<result_field>` 单写；
- 引用方统一用 `{user_inputs.<key>}` 形式；
- v4.3 不再有镜像扩展计划（如未来需重新引入镜像，需通过新 ADR 评估）。
```

#### 2.17.6 ADR-D6（`doc/adr/000-index.md` / 索引同步）

**操作**：

| ADR 编号 | 当前列 | PR-6 修改 |
|---------|------|---------|
| ADR-008 | active / D8 / v4.1 PR-2（已合入） | active / D8 / v4.1 PR-2（已合入）+ **v4.2 PR-6 修订** |
| ADR-014 | active / D14 / v4.1 PR-1+PR-2（已合入） + v4.2 PR-3' 修订 | active / D14 / v4.1 PR-1+PR-2（已合入）+ v4.2 PR-3' 修订 + **PR-6 收口纪要** |
| ADR-015 | active / D15 / v4.1 PR-1+PR-2（已合入） | active / D15 / v4.1 PR-1+PR-2（已合入）+ **v4.2 PR-6 修订（白名单下线）** |
| ADR-016 | active / D16 / v4.1 PR-1（已合入） | active / D16 / v4.1 PR-1（已合入）+ v4.2 PR-5 修订 + **PR-6 修订 #2（inline 形态退役）** |
| ADR-019 | active / D19 / v4.1 PR-5+PR-8（已合入） | **superseded-by-v4.2-PR-6** / D19 / v4.1 PR-5+PR-8（已合入） + **v4.2 PR-6 退役** |
| ADR-010 | active / D10+V1.1 O10+ / **v4.2 PR-5（已交付）** | 可选追加"+ PR-6 含 Fix-Confirming 注册"（标识 registry 完整集合到 8 项） |

#### 2.17.7 兼容性影响

- ① ADR 状态机修订均为文档级，无运行时影响；
- ② ADR-019 状态切换为 superseded 但**保留文件**（ADR-020 已有 superseded-by 范式），便于 git blame 追溯；
- ③ ADR 索引修订是 v4.2 H4 强约束的延续，PR-6 是 H4 终点。

---

## 3. PR-level DoD（Definition of Done）

### 3.1 静态契约校验（CI 完全绿）

| # | 校验项 | 期望结果 |
|---|------|---------|
| 1 | `bash scripts/check-state-enum.sh` | exit 0 / 16 项 enum 含 Fix-Confirming |
| 2 | `bash scripts/check-system-prompt-sync.sh` | exit 0 / SP 与 core 双侧 ENUM-DECLARATION-BLOCK 严格相等 / 8 项 registry state 在 SP 中均有引用 |
| 3 | `bash scripts/check-io-contract.sh` | exit 0 / single-form 校验通过 / 全仓 step-pause 仅 1 处（编排器 4c）+ 含 registry-key |
| 4 | `bash scripts/check-subagent-params.sh` | exit 0 |
| 5 | `bash scripts/check-phase-abort-structure.sh` | exit 0 / 6 phase 文件均含 ≥ 1 个 phase-abort/complete 宏 |
| 6 | `bash scripts/check-step-pause-registry.sh` | exit 0 / EXPECTED 8 项 ≡ REGISTRY 8 项 / 编排器 step 4 区间零硬编码 case |
| 7 | `bash scripts/check-config-schema.sh` | exit 0 |
| 8 | `python -m unittest discover -s scripts/tests/ -v` | 12 项单测全绿（含 GEN-D3 增量 6 项） |
| 9 | `git ls-files mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` | 输出为空（文件已删除） |
| 10 | `git ls-files mobile-qa-workflow/scripts/check-build-system-prompt-precondition.sh` | 输出为空（文件已删除） |
| 11 | `grep -rE '^\s*<step-pause' mobile-qa-workflow/phases/ mobile-qa-workflow/functionality-deep-dive/phases/` | 输出为空 |
| 12 | `grep -rE 'mirror_to_top' mobile-qa-workflow/core/ mobile-qa-workflow/scripts/` | 仅 schema 注释中保留的"mirror_to_top 已下线"说明（详见 REG-D1） |
| 13 | `grep -rE '顶层镜像白名单|白名单受限双写' mobile-qa-workflow/` | 仅出现在 ADR-D4 ADR-015 v4.2 修订段 + ADR-D6 ADR-008 修订段（历史叙述） |

### 3.2 跨平台回归（README §5 PR-6 行强制要求）

| 平台 | 验收用例 | 关键验证点 |
|------|---------|---------|
| Cursor / Claude Code | eval-cases 全量 + 5+ Spec-Uncertain/Fix-Confirming 用例 | Spec-Uncertain 弹窗仍是 1\|2\|S 三选 / Fix-Confirming 弹窗 Continue\|Revise 二选 / step-pause 不重复弹窗 |
| Trae | eval-cases 全量 | 同上 |
| Dify / Coze | eval-cases 全量 + 5+ 用例 | Limited 平台按新 system-prompt.md 描述执行（registry 单一权威源）/ 弹窗与 Cursor 完全一致 |
| 单 prompt LLM（Minimal） | 抽 1 用例（Spec-Uncertain 路径优先） | 小 LLM 按 ADR-010 §0 + ADR-021 展开规则正确渲染 step-pause / 不漏 Fix-Confirming 路由 |

**通用门禁（README §5 末尾）**：
1. `eval-framework/artifact_checker.py` 全量通过
2. `eval-cases/seed-10` chains A/B `mean_score` 不降（容许 ±5% 抖动）
3. 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

### 3.3 灰度合入清单（README §3 H3 严格串行 + V1.1 §3.2.21 H3 接纳）

- ① PR-6 commit 提交后，必须**单独**跑 eval-cases 全量回归（不与 PR-7 并入）；
- ② 跨平台 4 类回归（Cursor / Trae / Dify / Minimal）必须全部通过；
- ③ system-prompt.md 首次构建后人工 diff 验证 ≥ 1 名 reviewer 签字（"零业务语义差异"声明）；
- ④ Limited 平台 5+ 用例人工抽查无展开偏差（H3 接纳）；
- ⑤ ADR-014 / ADR-015 / ADR-016 / ADR-019 / ADR-008 / ADR-010 文档修订全部合入；
- ⑥ 主控 README §1 PR-6 行的"DoD"列 5 条 + §6 PR-6 详细 DoD 全部满足。

---

## 4. PR-level 回滚动作（README §6 PR-6 末尾"回滚: rollback 链 = O14 → O13 → 重建 system-prompt → 恢复 allowlist"细化）

> **回滚原则**：必须**严格按反向顺序**单步回退，每一步都有独立 commit + CI 验证；禁止"一次性整 PR revert"（会引入 ENUM 集 / registry / phase / system-prompt 多侧不一致）。

### 4.1 回滚顺序与单步动作

| 步骤 | 回退动作 | 验证 |
|------|--------|------|
| Step 1 | 回退 SP-N1（system-prompt.md 全量重写）→ 恢复手维护版本（含 Spec-Uncertain ANCHOR + 顶层镜像白名单段） | `git diff HEAD~1 -- system-prompt.md` 应显示完整重建 → 反向 |
| Step 2 | 回退 GEN-D1/D2/D3（生成器增强 + 单测）→ 保留 PR-2 原版 build-system-prompt.py | `python -m unittest discover -s scripts/tests/` 通过 |
| Step 3 | 回退 PHASE-D1（恢复 P2 内联 Spec-Uncertain step-pause）+ PHASE-D2（恢复 P4 内联 Fix-Confirming step-pause） | `grep -rE '^\s*<step-pause' phases/` 应回到 PR-5 状态（2 处命中） |
| Step 4 | 回退 REG-N1（删除 Fix-Confirming 注册表项）+ REG-D1 取消（恢复 mirror_to_top 标记） | `bash scripts/check-step-pause-registry.sh` 回到 PR-5 EXPECTED 7 项 |
| Step 5 | 回退 TPL-D1（删除 Fix-Confirming enum）+ TPL-D2/D3（恢复顶层 non_bug_user_choice + 注释段） | `bash scripts/check-state-enum.sh` 回到 v4.1 完整集合 15 项 |
| Step 6 | 回退 XML-D1/D2/D3 + RULES-D1/D2/D3 | `bash scripts/check-system-prompt-sync.sh` 校验通过 |
| Step 7 | 回退 SCRIPT-D1/D2/D3/D4 + 恢复 SCRIPT-D5（check-build-system-prompt-precondition.sh） | 所有 CI 脚本回到 PR-5 形态 |
| Step 8 | 回退 CI-D1（CI yml 16 项 Check 全部恢复） | yml diff 应回到 PR-5 状态 |
| Step 9 | 回退 FILE-D1（恢复 legacy-phase-step-pause-allowlist.txt） | `cat scripts/legacy-phase-step-pause-allowlist.txt` 含 2 条条目 |
| Step 10 | 回退 ADR-D1~D6（ADR 文档全部回到 PR-5 形态） + DOC-D1（PLATFORM-GUIDE.md 恢复） | `git diff HEAD~9 -- doc/adr/` 显示反向重建 |

### 4.2 部分回滚（仅删除 Fix-Confirming 但保留 Spec-Uncertain 内联删除）

如果 PR-6 合入后发现 Fix-Confirming 路径有 LLM 展开 bug 但 Spec-Uncertain 已稳定，可执行**部分回滚**：

1. 仅回退 Step 3 中 PHASE-D2（恢复 P4 内联 step-pause）+ Step 4 中 REG-N1（删除 Fix-Confirming 注册表项）+ Step 5 中 TPL-D1 的 Fix-Confirming 添加；
2. 保留其他改动（O13 + O12 + system-prompt 重建）；
3. 同时恢复 `legacy-phase-step-pause-allowlist.txt` 但仅含 1 条 P4 条目（不含 P2，因 P2 已稳定无内联）；
4. CI 守门 Check 1 / Check 2 / Check 6 / Check 13 仍下线（无需恢复，仅 D14 部分整改）。

部分回滚后 D14 治理停留在"P2 已清零、P4 暂留"的中间态，需在主控 README 中标注 v4.2 部分完成 + v4.3 跟进。

---

## 5. 反向自检清单（PR commit 前必跑）

```bash
# 1. 静态校验全套
cd $REPO_ROOT/mobile-qa-workflow
for s in scripts/check-*.sh; do
  echo "=== $s ==="
  bash "$s" || exit 1
done

# 2. 单元测试
python -m unittest discover -s scripts/tests/ -v

# 3. 实跑 build-system-prompt.py 与已 commit 的 system-prompt.md 比对
ALLOW_FIRST_BUILD=1 python3 scripts/build-system-prompt.py --mode=full --output=/tmp/sp-rebuild.md
diff -u system-prompt.md /tmp/sp-rebuild.md || (echo "ERROR: SP 与生成器输出不一致" && exit 1)

# 4. 全仓 step-pause 形态自检（应只命中 core/workflow.xml 1 处）
grep -rE '^\s*<step-pause' phases/ functionality-deep-dive/phases/ system-prompt.md
# ↑ 期望输出：（空）
grep -rE '^\s*<step-pause' core/workflow.xml
# ↑ 期望输出：1 行（registry 形态 / 编排器 4c 内）

# 5. ADR 索引一致性
grep -E 'ADR-019|ADR-014|ADR-015|ADR-016|ADR-008' doc/adr/000-index.md
# ↑ 期望含 v4.2 PR-6 修订标注

# 6. 历史白名单 / 镜像残留扫描
grep -rE 'mirror_to_top|顶层镜像白名单|白名单受限双写' core/ phases/ scripts/ system-prompt.md PLATFORM-GUIDE.md
# ↑ 期望仅命中 step-pause-registry.yaml schema 注释中的"已下线"说明

# 7. allowlist 文件物理删除验证
test ! -e scripts/legacy-phase-step-pause-allowlist.txt && echo "OK: allowlist deleted" || (echo "ERROR: allowlist 仍存在" && exit 1)
test ! -e scripts/check-build-system-prompt-precondition.sh && echo "OK: precondition script deleted" || (echo "ERROR: 未删除" && exit 1)
```

---

## 6. Reviewer 关注点 / 跨平台抽查重点

### 6.1 必须人工 review 的关键文件

| 文件 | 关注点 | 标准 |
|------|------|-----|
| `system-prompt.md`（SP-N1 重建） | 每个段落与 PR-5 版本逐节比对 / 0.2 节宏展开规则完整保留 / 无 ANCHOR 残留 | 零业务语义差异 |
| `phases/p4-fix-design.md`（PHASE-D2） | `{fix_design_summary}` 写入是否正确触发 `<phase-complete>` | 与 P3 step 10 phase-complete 模式一致 |
| `step-pause-registry.yaml`（REG-N1） | Fix-Confirming on_success 的 increment 字段 | `fix_retry_count` 自增逻辑与 P6 失败回流路径不冲突 |
| `core/core-rules.xml`（RULES-D2/D3） | step-pause-scope 规则 + forms 块 | 不丢失任何 D14 守护语义 |
| ADR-014 / ADR-015 / ADR-016 / ADR-019 文档段 | 收口纪要内容 | 与代码改动 1:1 对齐 |

### 6.2 Limited 平台（Dify / Coze）专项抽查（≥ 5 例）

| 用例 | 触发路径 | 验证点 |
|------|--------|-------|
| 1 | issue → P2 Spec-Uncertain（高歧义） | 弹窗 1\|2\|S 三选 / 用户回 1 → P2 继续 |
| 2 | issue → P2 Non-Bug 判定 | 弹窗 Accept/Reflow / 用户回 Reflow → P2 重新执行 + non_bug_reflow_count + 1 |
| 3 | issue → P3 RCA-LowConfidence | 弹窗 Retry/Human / 用户回 Retry → P2 回流 |
| 4 | issue → P4 Fix-Confirming | 弹窗 Continue/Revise / 用户回 Revise → P4 step 2 + fix_retry_count + 1 |
| 5 | issue → P4 Fix-Confirming | 弹窗 Continue → P5 进入 Fix-Implementing |

### 6.3 与历史 bug 的回潮风险检查

| 历史 bug | 回潮风险点 | 本 PR 守门 |
|---------|---------|---------|
| B1*（漏写 ABORT）| PHASE-D1/D2 改写 phase-abort/complete 宏时漏写 state 或 fields | Check 15 升级 error 后强制校验宏 state ∈ enum 集 |
| 重复弹窗（v4.2 遗留 #6）| phase 内联 step-pause 与编排器 case 同时触发 | SCRIPT-D1 single-form 校验 + Check 16 双向严格相等 |
| ENUM 漂移 | TPL-D1 改完忘记同步 SCRIPT-D2/D3/D4 / SP-N1 | Check 9 / Check 10 / Check 15 / Check 16 四件套联防 |
| 镜像字段失踪导致 Limited 平台引用断裂 | DOC-D1 + SP-N1 删除顶层镜像后接入方未察觉 | PR-6 changelog 必须显式列出"接入方需把 `{non_bug_user_choice}` 改读 `{user_inputs.non_bug_user_choice}`" |

---

## 7. 变更点工作量与时间线

### 7.1 工作量分解（总 ~1.4 d）

| 子模块 | 文件数 | 工作量 | 责任段 |
|------|------|------|-------|
| O13/O14 phase 改写 + 注册表 + enum | 4（PHASE-D1/D2 + REG-N1 + TPL-D1） | 0.2d | Seg-1 |
| O12 顶层镜像下线（registry + workflow + core-rules + template + PLATFORM + ADR-015/008） | 7（REG-D1 + XML-D1/D2/D3 + RULES-D1 + TPL-D2/D3 + DOC-D1 + ADR-D4/D5/D6） | 0.2d | Seg-1 |
| 生成器增强 GEN-D1/D2/D3 + 单测 | 1（build-system-prompt.py + tests） | 0.2d | Seg-2 |
| system-prompt.md 首次构建 + 人工 diff（SP-N1） | 1 | 0.3d | Seg-2 |
| CI yml 调整 + 守门脚本升级 | 6（CI-D1 + SCRIPT-D1/D2/D3/D4/D5） | 0.3d | Seg-3 |
| ADR 收口段编写 / 索引同步 / allowlist 物理删除 | 5（ADR-D1/D2/D3 + ADR-D6 + FILE-D1） | 0.1d | Seg-3 |
| 跨平台回归 + Limited 平台 5+ 用例抽查 | — | 0.1d | Seg-3 验收 |

### 7.2 建议提交段（与 PR-3'/PR-5 体例对齐）

> 与 PR-3'/PR-5 一致，PR-6 提交时也建议拆为多段 commit，便于 reviewer 分段审阅，但**最终作为单一 PR 合入** main（不像 PR-3'/PR-5 那样允许独立 segment 并入）。

| Seg | commit 标题 | 包含变更点 |
|-----|-----------|---------|
| Seg-1 | `Seg-1: feat(qa-workflow): v4.2 PR-6 D14 收口 #3 — phase 内联删除 + Fix-Confirming + 顶层镜像下线（O13 + O14 + O12）` | PHASE-D1/D2 + REG-N1/D1 + TPL-D1/D2/D3/D4 + XML-D1/D2/D3 + RULES-D1/D2/D3 + DOC-D1 + ADR-D4/D5/D6 + FILE-D1 |
| Seg-2 | `Seg-2: feat(qa-workflow): v4.2 PR-6 system-prompt.md 首次自动构建（O17+ Stage-1 / 解 H1）` | GEN-D1/D2/D3 + SP-N1 |
| Seg-3 | `Seg-3: feat(qa-workflow): v4.2 PR-6 CI 守门收口（删除 6 项 Check / 升级 3 项 / 删 H1 守门脚本）` | CI-D1 + SCRIPT-D1/D2/D3/D4/D5 + ADR-D1/D2/D3 |

### 7.3 关键时间路径

```
T0     : PR-5 已合入 main + 跨平台回归全绿（前置）
T0+0.5d: Seg-1 完成（O13 + O14 + O12 + ADR-D4/D5/D6）
T0+0.7d: Seg-2 完成（生成器增强 + system-prompt.md 重建 + 人工 diff）
T0+1.0d: Seg-3 完成（CI 守门收口 + ADR-D1/D2/D3）
T0+1.4d: 跨平台 4 类回归 + Limited 平台 5+ 用例抽查通过 → PR 提交合入 main
```

---

## 8. 附录 A：与 PR-5 子文档关联点对照

| PR-5 子文档（v1.1）声明的 PR-6 待办 | 本 PR-6 落地变更点 |
|---------------------------------|------------------|
| §1（不在范围 #1）"O13 / O14 / O15 — phase 早退一致性、Spec-Uncertain inline 段删除、Fix-Confirming 引入" | PHASE-D1（O13）+ PHASE-D2（O14）+ REG-N1（Fix-Confirming） |
| §1（不在范围 #2）"O17+ system-prompt.md 首次构建" | SP-N1 + GEN-D1/D2/D3 |
| §1（不在范围 #3）"O11+ + O15 模块化 / 包装层重构" | **不在本 PR 范围**（推到 PR-7） |
| §1（不在范围 #4）"v4.2 收尾遗留 #3 完整下线" | TPL-D2/D3 + XML-D1 + REG-D1 + RULES-D1 + DOC-D1 + ADR-D4/D5（O12） |
| §2.4 末尾"PR-6 引入 `Fix-Confirming` 时由 PR-6 同步把它加入 EXPECTED 与黑名单" | SCRIPT-D4 EXPECTED 集 |
| ADR-010 §6.6 衔接事项 #2"PR-6 build-system-prompt.py 首次构建并把 registry 注入 sp 之后由 PR-6 同步删除 ANCHOR 注释" | XML-D2 + SCRIPT-D2 + GEN-D2 |

---

## 9. 附录 B：关键 grep / 反查命令一览（debug 备查）

| 用途 | 命令 |
|-----|------|
| 全仓 step-pause 残留扫描 | `grep -rnE '^\s*<step-pause' mobile-qa-workflow/` |
| ENUM 集多版本兼容验证 | `python3 scripts/build-system-prompt.py --mode=verify` |
| Registry 双向严格相等 | `bash scripts/check-step-pause-registry.sh` |
| Phase 出口宏覆盖 | `bash scripts/check-phase-abort-structure.sh` |
| Single-form 校验 | `bash scripts/check-io-contract.sh` |
| Sync 校验 | `bash scripts/check-system-prompt-sync.sh` |
| 顶层镜像残留扫描 | `grep -rE 'mirror_to_top\|顶层镜像白名单' mobile-qa-workflow/` |
| ADR 状态切换验证 | `grep -E '^\| .ADR-' doc/adr/000-index.md` |

---

> **方案版本**：v1.0（首次提交，2026-04-22）
> **维护者**：v4.2 PR-6 owner（接收 PR-3' / PR-5 已落地基线后启动）
> **下次评审**：本 PR 进入 Code Review 前必跑 §5 反向自检清单 + §3.1 + §3.2 全套；任一不过 → reviewer hold
