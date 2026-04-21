# PR-5 施工方案质检报告（v1.0）

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md`
> 评审日期：2026-04-21
> 评审结论：**Needs Fixes**
> 评审口径：按固定 rubric 复核 4 个维度，仅记录已证实问题，不扩展猜测项。

---

## 1. 评审范围与方法

本轮质检聚焦以下固定维度：

- **协议兼容性**：新 DSL 写法是否与现有 `core/core-rules.xml` 契约自洽
- **行为等价性**：`workflow.xml` 的重构是否保留现有状态机副作用
- **CI 可验证性**：DoD 与守门脚本是否一一对应，是否会出现假绿
- **验收可执行性**：demo / 回归步骤是否在当前边界约束下真正可做

交叉核验基线：

- 施工单：[pr-5-d14-step-pause-registry.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md)
- 当前编排器实现：[workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L101-L374)
- 当前 `step-pause` 协议定义：[core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L108-L174)
- 当前状态模板：[workflow-status-template.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L4-L106)
- 当前 CI 入口：[qa-workflow-schema-check.yml](file:///Users/bytedance/Code/loupe/.github/workflows/qa-workflow-schema-check.yml#L280-L370)
- ADR 基线：[ADR-010](file:///Users/bytedance/Code/loupe/doc/adr/010-step-pause-registry-data-driven.md) / [ADR Index](file:///Users/bytedance/Code/loupe/doc/adr/000-index.md)

---

## 2. 总体结论

该施工单的目标、拆分边界和主线思路基本合理，尤其是把 6 个交互态收敛到 registry 的方向是对的；但当前版本仍有 **2 个高风险设计矛盾** 与 **2 个中风险验收/守门缺口**，如果按文档原样实施，存在以下后果：

- 新写法 `<step-pause registry-key="..."/>` 在协议层无法自洽，且会和“旧写法兼容”表述冲突
- `Boundary-Refined` 的现有改态行为会被误删，导致状态机回归
- Check 16 无法兑现文档承诺的“严格相等”，会留下 registry 漂移假绿窗口
- `stop_state demo case` 在当前边界约束下不可直接执行，DoD 可验收性不足

**综合裁定**：当前版本不建议直接开工，建议先修正文档后再进入实施。

---

## 3. Findings

| No. | 严重度 | 问题 | 结论 |
|---|---|---|---|
| 1 | High | `Boundary-Refined` 被错误并入默认流转，破坏现有显式改态语义 | 必须修 |
| 2 | High | `registry-key` 必填方案与现有 `<step-pause>` 必填参数表、以及“旧写法兼容”说明互相冲突 | 必须修 |
| 3 | Medium | DoD 声称“严格相等”，但 Check 16 骨架只验证子集覆盖，不验证无额外项 | 应修 |
| 4 | Medium | `stop_state demo case` 与 enum 守门、文件冻结边界不兼容，当前验收步骤不可直接落地 | 应修 |

### Finding 1

**问题**：`XML-D1` 把 `Boundary-Refined` 归为“未命中 registry 且非 Done → goto step 2”的纯流转态，但当前主干并不是简单 `goto step 2`，而是先显式把 `current_state` 改写为 `RCA-Designing`。

**证据**：

- 施工单新文把 `Boundary-Refined` 放进默认流转集合：[pr-5-d14-step-pause-registry.md:L302-L305](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L302-L305)
- 施工单还明确声称这与现状“等价”： [pr-5-d14-step-pause-registry.md:L310-L310](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L310-L310)
- 当前编排器真实行为是显式改态后再跳转：[workflow.xml:L333-L336](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L333-L336)
- `Boundary-Refined` 仍会被 phase 实际写入：[p3-root-cause.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p3-root-cause.md#L62-L62)

**影响**：

- 会把一个“有副作用的纯路由态”错误降格为“无副作用默认态”
- 下游 step 2 / phase 选择若依赖 `current_state=RCA-Designing`，将出现行为偏移
- 文档中的“100% 行为等价”结论不成立

**建议修法**：

- 保留 `Boundary-Refined` 的显式路由规则，不要直接吞进 default
- 可选方案 A：在 `4c` 中保留一个纯路由特例块，专门处理 `Boundary-Refined -> RCA-Designing -> step 2`
- 可选方案 B：若坚持全数据化，则把 `Boundary-Refined` 也纳入 registry，但它应是“纯路由项”而不是 step-pause 交互项

### Finding 2

**问题**：`TAG-D1` 只提出“给 `<step-pause>` 新增 `registry-key` 必填属性”，但没有同步解决两层冲突：

1. 当前协议里 `title` / `result_field` / `allowed_values` 已是必填；新写法 `<step-pause registry-key="${current_state}" />` 天然不满足旧必填表。
2. 施工单同时声明 `registry-key required="true"` 与“旧写法继续兼容”，两者逻辑上冲突。

**证据**：

- 施工单把 `registry-key` 作为新协议入口：[pr-5-d14-step-pause-registry.md:L12-L13](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L12-L13)
- 施工单建议在 `core-rules.xml` 中新增 `registry-key` 必填项：[pr-5-d14-step-pause-registry.md:L204-L208](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L204-L208)
- 当前协议定义里 `title` / `result_field` / `allowed_values` 均为必填：[core-rules.xml:L126-L145](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L126-L145)
- 当前 ADR-016 口径也仍是“必填参数表 = `title` / `result_field` / `allowed_values`”，施工单未给出同步修订策略

**影响**：

- 新语法在协议层无法被一致解释
- reviewer 与实施者会不知道究竟是“4 个必填参数并存”还是“二选一两套写法”
- “旧写法继续兼容”缺少可执行定义，容易在 PR-6 删除 phase 内联前引入口径冲突

**建议修法**：

- 把 `<step-pause>` 明确定义成两种互斥形态之一：
  - **Inline 形态**：`title + result_field + allowed_values (+ option*)`
  - **Registry 形态**：`registry-key`
- 在文档里显式写清“互斥校验规则”，不要只写“新增一个 required param”
- 同步补 ADR-016/ADR-010 对新旧形态的兼容策略，避免协议文档分叉

### Finding 3

**问题**：DoD `D1` 写的是“registry 6 项 state 与编排器交互态集合严格相等”，但 `SCRIPT-N1` 骨架实际只检查“期望 6 项是否都在 registry 里”，没有检查 registry 是否多出额外条目。

**证据**：

- DoD 要求“严格相等”： [pr-5-d14-step-pause-registry.md:L418-L420](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L418-L420)
- `SCRIPT-N1` 第 ② 类算法描述也是“必须全部 ⊆ registry 的 state 集”： [pr-5-d14-step-pause-registry.md:L324-L326](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L324-L326)
- 骨架实现同样只做 `EXPECTED ⊆ REG_STATES`： [pr-5-d14-step-pause-registry.md:L358-L364](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L358-L364)

**影响**：

- registry 多出未消费项时，CI 仍可假绿
- 文档声称的“权威性强约束”会退化成“至少包含”，无法真正防漂移
- 后续 `stop_state` demo 或未来临时试验项更容易误留在主干

**建议修法**：

- 第 ② 类校验改成双向比较：`EXPECTED == REG_STATES`
- 输出差集：`missing` 与 `unexpected` 分开报错，便于 reviewer 判断是漏项还是误增项
- 若设计上允许 future-facing 预注册项，则必须把 DoD 文案从“严格相等”改成“至少覆盖 + 明确 allowlist”

### Finding 4

**问题**：`B6 / DEMO-V1` 要求“仅在 `step-pause-registry.yaml` 加 1 项 stop_state 即可生效”，但这与本施工单自身的 enum 守门、文件冻结边界相冲突。

**证据**：

- 施工单明确说本 PR 不引入新的业务交互态，只给 demo 验证步骤：[pr-5-d14-step-pause-registry.md:L21-L22](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L21-L22)
- 同一文档又要求 demo 仅改 registry 一处： [pr-5-d14-step-pause-registry.md:L438-L438](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L438-L438)
- 但 D2 / Check 16 第 ① 类要求 registry state 必须在 enum 集内： [pr-5-d14-step-pause-registry.md:L419-L419](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L419-L419), [pr-5-d14-step-pause-registry.md:L324-L325](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L324-L325)
- 当前 enum 权威源在 `workflow-status-template.yaml` 头注释，且本 PR 明确禁止修改该文件：[workflow-status-template.yaml:L4-L10](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L4-L10), [pr-5-d14-step-pause-registry.md:L37-L37](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-5-d14-step-pause-registry.md#L37-L37)

**影响**：

- demo 若真的引入新 stop_state，将直接违反 enum 守门
- demo 若只是本地临时修改，文档缺少“如何回退 / 是否纳入 CI / 是否允许越界改 template”的操作说明
- 这会让 `B6` 变成不可复现的口头验收项

**建议修法**：

- 二选一收口：
  - **方案 A**：把 demo 改成“使用现有 enum 内状态做最小增量演示”，不引入新状态名
  - **方案 B**：明确这是“本地临时演示，不纳入提交”，并补一段完整步骤：临时加 enum、演示、回滚、确保最终 diff 干净

---

## 4. 已确认的优点

以下内容本轮已确认方向正确，可保留：

- **PR 边界控制清晰**：未把 PR-5 与 PR-6 的 phase 内联删除、system-prompt 首次构建混在一个施工单里，符合 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L181-L200) 的 H3 串行约束
- **主线目标明确**：registry 数据化、4a/4b/4c 拆段、Check 16 守门三件事收束得比较清楚
- **对 `mirror_to_top` 的过渡边界有意识**：没有在 PR-5 提前删除 `workflow-status-template.yaml` 顶层镜像字段，避免和 PR-6 纠缠
- **ADR 收口方向正确**：ADR-010 从 `draft` 切到 `active` 的时机放在 PR-5，而不是 PR-1，逻辑上成立

---

## 5. 最终裁定

**裁定**：`Needs Fixes`

**建议先修的最小集合**：

1. 修正 `Boundary-Refined` 路由设计，恢复显式改态语义
2. 重写 `TAG-D1`，把 `<step-pause>` 新旧两种形态的互斥契约讲清楚
3. 把 Check 16 第 ② 类从“子集覆盖”改成“严格相等”或同步下调 DoD 文案
4. 重新定义 `B6 / DEMO-V1`，让它在当前 enum/边界约束下可实际执行

若以上 4 点收口，本施工单即可进入下一轮定向复审；在此之前，不建议直接按当前版本实施。
