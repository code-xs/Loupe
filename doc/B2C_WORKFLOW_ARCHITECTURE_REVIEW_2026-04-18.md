# B2C 工作流与 Prompt Engineering 深度审查及优化方案

**审查日期**: 2026-04-18
**审查目标**: 深入分析 Mobile B2C QA Workflow 的核心架构、Phase 1-6 阶段逻辑、Agent Prompt 及模块间状态机流转，识别逻辑冲突与语义描述问题，并提供优化方案。

---

## 1. 核心逻辑冲突 (Logical Conflicts)

### 1.1 状态机变量覆盖问题 (State Variable Overwrite)
- **现象**: 在 `p4-fix-design.md` (Step 2) 中，设置修复策略模式后，执行了 `<action>更新 {workflow_status}：... fanout_mode = {fix_strategy_mode}</action>`。
- **冲突**: `fanout_mode` 已经在 `p3-root-cause.md` 中被用于记录 RCA 阶段的并发策略（如 `complex-arbitrated`）。P4 阶段直接将其覆写为 Fix 阶段的策略（如 `contested-arbitrated`），这会导致验证阶段 (P6) 回流 RCA 时丢失原始的 RCA fanout 状态。
- **优化**: 区分命名空间。RCA 阶段使用 `rca_fanout_mode`，Fix 阶段使用 `fix_strategy_mode`，互不干扰。

### 1.2 Phase 5 的 Human-Review 导致死循环 (Infinite Loop on Re-entry)
- **现象**: 在 `p5-fix-impl.md` (Step 6) 中，如果判定 `error-dump.md` 存在，则设置 `Execution-Status = Human-Review` 并 `ABORT`。在 `workflow.xml` 中，人工介入并选择 `[C] Continue` 后，会重新路由进入 `qa-fix-impl`。
- **冲突**: 重新进入 P5 后，由于上一轮生成的 `error-dump.md` 依然存在于文件系统中（且工作流未包含任何清理动作），Step 6 会立刻再次触发 `ABORT`，导致工作流陷入无法恢复的死循环。
- **优化**: 在 `p5-fix-impl.md` 的 Step 3 (工作区初始化) 或 `workflow.xml` 重入前，增加针对残留失败产物（如 `error-dump.md`）的清理/归档（Archive）动作。

### 1.3 控制流重复接管 (Duplicate Control Flow Handling)
- **现象 A (Info-Insufficient)**: `p1-intake.md` (Step 5) 遇到信息不足时，内部使用了 `<ask>` 标签挂起并在收到回复后 `goto step="2"`。同时，主编排器 `workflow.xml` (Step 4) 中也有 `case if="Info-Insufficient"` 处理逻辑和 `step-pause`。
- **现象 B (Non-Bug)**: `p2-spec-definition.md` (Step 4) 对非 Bug 判定使用了 `<step-pause>` 并定义了内部的 `goto step 1` (Reflow) 操作。而 `workflow.xml` 同样在 Step 4 定义了详尽的 `case if="Non-Bug"` 的 Reflow 次数控制与流转。
- **冲突**: Phase 文件（子流程）与 `workflow.xml`（主编排器）都在试图接管同一个暂停和路由逻辑。若 Phase 内部通过 `goto` 实现了循环，主编排器的状态机捕获将变成死代码（Dead Code）；若两者同时生效，会导致用户被重复提问或状态计数错乱。
- **优化**: 严格执行“**子流程只负责状态标记，主编排器负责挂起与路由**”的原则。移除 `p1-intake.md` 和 `p2-spec-definition.md` 中的 `<ask>`、`<step-pause>` 和 `goto` 逻辑，仅在子流程中将 `current_state` 设置为特定值并直接结束当前 Phase，将挂起与恢复的权力完全交还给 `workflow.xml`。

### 1.4 已废弃 Agent 的声明冲突 (Deprecated Agent References)
- **现象**: `core-rules.xml` 中明确将 `functionality-deep-dive` 分组下的 `context-reconstructor`、`state-analyst` 等标记为 "已废弃，仅供历史会话恢复"。
- **冲突**: 在 `p3-root-cause.md` (Step 6) 中，触发专项分析时，直接加载了 `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`。如果该子工作流内部仍然存在对这些废弃角色的隐式调用，或者共享基座（如 `shared-arbiter-base.md` 中 `scene=DEEP_DIVE`）的接口未及时对齐新的 Analyst 体系，会导致子工作流崩溃。
- **优化**: 彻底清理 `core-rules.xml` 中的废弃声明（若已完全弃用则直接删除节点），并确保 `functionality-deep-dive/core/workflow.xml` 与当前存活的 `deep-dive-structure-analyst` 等新角色完全对齐。

---

## 2. 语义描述与 PE 问题 (Semantic & Prompt Engineering Issues)

### 2.1 契约溯源“前置门禁”的执行主体错位
- **现象**: `system-prompt.md` 和 `p5-fix-impl.md` 在描述中都强调了“[硬性前置门禁] 契约溯源走查 — 未产出 Contract Checklist 则禁止进入编码实施”。
- **问题**: 在实际执行中，`p5-fix-impl.md` (Step 5) 是作为一个黑盒将所有输入透传给 `coder-agent` SubAgent。主流程无法在 SubAgent "编码前" 进行拦截，只能在 SubAgent "执行完" (Step 6) 检查 `contract-checklist.md` 是否存在。PE 语义上说的“前置门禁”，在物理流转上变成了“后置产物校验”。
- **优化**: 修正 PE 描述。在 `p5-fix-impl.md` 中明确说明“门禁由 `coder-agent` 内部强制执行，主工作流负责后置的产物完整性校验（Artifact Validation）”。

### 2.2 Shared Base 输出格式约束不一致
- **现象**: `shared-challenger-base.md` 的模板中硬编码了 `recommendation: Accept / Revise / Reject`。
- **问题**: `challenger.md` (包装层) 中规定：当 `scene = FIX` 时，recommendation 应该是 `Adopt / Revise / Reject`。这与 Base 模板硬编码的字面量冲突，导致大模型输出时容易产生幻觉或格式校验失败。
- **优化**: 将 `shared-challenger-base.md` 中的模板修改为 `recommendation: [Accept/Adopt] / Revise / Reject`，并在 wrapper 中通过指令明确对应关系。

### 2.3 Monolithic `system-prompt.md` 与 SubAgent 架构的割裂
- **现象**: `system-prompt.md` 标榜为“不支持外部文件引用的纯 Chat 对话”准备的内联版。但其内部（如 Phase 3）依然包含对 `investigator`、`challenger` 和 `arbiter` 的 "共享调用显式注入" 等高度依赖 SubAgent 架构的描述。
- **问题**: 纯 Chat 模式下的单体大模型无法在一次推理中“分身”调用共享基座，它只能扮演一个全能型角色。这种描述会让单体大模型在执行到 P3 时试图模拟出多个独立角色的交互，极其消耗 Token 且容易丢失上下文。
- **优化**: 针对 `system-prompt.md`，应剥离 SubAgent 相关的编排术语，将 P3 和 P4 的逻辑简化为“内部多视角自我博弈（Self-Reflection）”，而不是“调用子 Agent”。

### 2.4 “反事实校验”与“边界精化”缺失明确的执行指引
- **现象**: `p3-root-cause.md` (Step 5) 提到“执行反事实校验；若发现更精确边界，则 `current_state = Boundary-Refined`”。
- **问题**: Prompt 中对“如何执行反事实校验”缺乏明确的步骤或工具链定义（例如，是否需要切到历史 Commit 跑测试？是否依赖特定的 `Search` 逻辑？），这使得大模型只能基于当前代码做纯脑补，极少能真正触发 `Boundary-Refined` 状态。
- **优化**: 在 RCA 阶段增加明确的 `Counterfactual Verification Protocol`，指导 Agent 如何利用 Git 历史或日志锚点进行版本区间二分查找（Bisection），以确保边界精化真实可用。

---

## 3. 全面优化行动方案 (Actionable Optimization Plan)

1. **统一状态机路由权 (Fix Control Flow)**
   - 编辑 `p1-intake.md` 和 `p2-spec-definition.md`，移除 `<ask>` 和 `<step-pause>`。统一替换为：`<action>设置 current_state = XXX，当前阶段挂起，返回主编排器</action>`。
2. **修复 P5 死循环缺陷 (Fix P5 Infinite Loop)**
   - 在 `p5-fix-impl.md` Step 3 加入清理逻辑：`<action>若为重入或重试，清理工作区残留的 error-dump.md 与旧版 impl-report.md</action>`。
3. **隔离变量命名空间 (Namespace Isolation)**
   - 在 `p4-fix-design.md` 中，移除对 `fanout_mode` 的覆写，保留 `fix_strategy_mode` 即可；`workflow.xml` 中关于重试与路由的逻辑同时校验 `rca_fanout_mode` 与 `fix_strategy_mode`。
4. **统一术语与模板 (Terminology Alignment)**
   - 同步 `shared-challenger-base.md` 和包装层的输出枚举值。
   - 对齐 `system-prompt.md` 的前置/后置门禁描述，使其符合实际的黑盒调用物理规律。
5. **废弃资产清理 (Deprecation Cleanup)**
   - 从 `core-rules.xml` 中移除不再使用的 V1/V2 历史恢复专属 Analyst，减轻主工作流的上下文负担。
