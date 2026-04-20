# PR-5+6 施工方案 Review

> 审查对象：`construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md`
>
> 对照基线：
> - `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`
> - 当前工程实现：`functionality-deep-dive/core/default-config.yaml` / `core/default-config.yaml` / `phases/p2-spec-definition.md` / `phases/p4-fix-design.md` / `phases/p6-verification.md` / `templates/verification-report.md`
> - 相关协议与契约：`core/core-rules.xml` / `agents/shared-arbiter-base.md` / `agents/shared-challenger-base.md`
>
> 审查口径：仅评估施工方案的正确性、协议闭环、与当前仓库状态及主文档的一致性；**不修改代码**

## 结论

- 结论：**方向部分正确，但当前版本不宜直接作为最终施工依据。**
- 判定：存在 **1 个 Critical**、**3 个 Major** 问题；其中 C9 模板闭环问题会直接影响方案可实施性，其余问题会导致 DoD、CI 契约与回滚口径失真。
- 正向确认：
  - B3 的问题识别是准确的：当前 `Deep-Dive` 子配置里三个 `emit_*` 默认值确实仍为 `false`，见 [default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml#L16-L18)。
  - C2 的字段命名在本方案里与当前 shared base 契约是对齐的：arbiter 使用 `base_score`，challenger 使用 `confidence_input`，见 [shared-arbiter-base.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/agents/shared-arbiter-base.md#L5-L10) 与 [shared-challenger-base.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/agents/shared-challenger-base.md#L5-L10)。
  - 现状盘点“真正的 phase 内 step-pause 标签”目前确实只有 P2 与 P4 两处，`functionality-deep-dive/phases/**` 当前无命中，见 [p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L46-L63) 与 [p4-fix-design.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L132-L142)。

## Findings

| No. | 严重度 | 问题 | 结论 | 关键证据 |
|---|---|---|---|---|
| 1 | Critical | C9 把“中间态/正态切换”下沉到模板，但当前模板协议没有条件渲染能力 | 方案声称“仅改模板即可形成完整闭环”，但 `template-output` 当前只有 `file`/`template` 两个参数，且 P6 成功与失败路径复用同一模板；新增静态段落后，成功路径也会带出“中间态报告”，与“验证通过可省略”相冲突 | [pr5-6-deep-dive-and-agents-templates.md:L390-L452](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L390-L452), [core-rules.xml:L175-L177](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L175-L177), [p6-verification.md:L88-L107](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L88-L107), [verification-report.md:L95-L111](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/templates/verification-report.md#L95-L111) |
| 2 | Major | allowlist 的“基于实际 grep 结果”陈述与仓库现状不符 | 子文档给出的原始命令是 `grep -rn '<step-pause' ...`，并断言“实际命中 2 条”；但当前 P2 文件中除真实标签外，还存在多处注释/说明文本含有字面量 `<step-pause>`，原始 grep 会多于 2 条，只有加过滤条件后才可能得到 2 | [pr5-6-deep-dive-and-agents-templates.md:L176-L225](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L176-L225), [pr5-6-deep-dive-and-agents-templates.md:L466-L472](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L466-L472), [p2-spec-definition.md:L50-L53](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L50-L53), [p2-spec-definition.md:L77-L78](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L77-L78), [p4-fix-design.md:L136-L142](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L136-L142) |
| 3 | Major | 文件范围、回滚拆 commit 方案与当前基线/自身元信息不一致 | 子文档元信息写“涉及文件 6 个”，但回滚章节又要求额外做 README 与主文档 §4 的“联动小修”提交；更关键的是，这两处索引在当前仓库里已经指向合并后的子文档，`commit 3` 既未计入范围，也不再建立在当前基线上 | [pr5-6-deep-dive-and-agents-templates.md:L55-L58](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L55-L58), [pr5-6-deep-dive-and-agents-templates.md:L493-L545](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L493-L545), [README.md:L12-L14](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/README.md#L12-L14), [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md:L498-L499](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L498-L499) |
| 4 | Major | 回滚兼容性假设“allowlist 缺失时 PR-8 CI 降级 warn”与主文档 D19 守门口径冲突 | 子文档两处把“文件被回滚删除后 CI 应 warn 不阻塞”当作既定前提，但主文档对 PR-8 的描述是显式检查 allowlist “存在且非空”；如果这里不统一，回滚预案会建立在一个未被主文档批准的 CI 行为上 | [pr5-6-deep-dive-and-agents-templates.md:L227-L230](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L227-L230), [pr5-6-deep-dive-and-agents-templates.md:L511-L516](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L511-L516), [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md:L477-L483](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L477-L483), [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md:L523-L529](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L523-L529) |

## 详细说明

### 1. C9 目前还没有形成真正可执行的“模板侧闭环”

- 子文档明确把 C9 的关键设计定为：
  - 不新增 `mode='intermediate'`
  - 由 `phases/p6-verification.md` 继续调用同一个 `<template-output ... verification-report.md>`
  - “中间态/正态”切换下沉到模板内部，由 `verification_failure_type` 决定，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L390-L446)。
- 但当前协议层对 `<template-output>` 的定义只有 `file` 与 `template` 两个参数，没有任何模式、变量绑定、条件块或分支渲染能力，见 [core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L175-L177)。
- 当前 P6 失败分支与成功分支都调用同一个模板，见 [p6-verification.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L94-L107)。
- 当前模板本体也是一段静态 markdown，没有任何“当 `verification_failure_type != null` 时才展开此段”的协议痕迹，见 [verification-report.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/templates/verification-report.md#L1-L111)。

这意味着：

- 如果按子文档直接落地，仅仅把“中间态报告”静态插入模板，那么**成功路径**生成的 verification report 也会包含该段落及占位字段，和“验证通过场景可省略”不一致。
- 如果想继续坚持“成功场景不渲染”，那就还缺一个被协议层承认的开关机制；当前方案不能自证“完整闭环”。

建议：

- 二选一并显式写回方案：
  - 方案 A：承认 v4.1 只做到“模板统一增段”，成功/失败都输出该段，但成功场景允许留空或标记 `N/A`
  - 方案 B：把条件渲染机制显式补回协议层或 phase 调用层，再重新定义 PR-6 边界
- 在收口之前，不建议把“C9 完整闭环”写进 DoD。

### 2. allowlist 的盘点命令与结论没有严格对齐

- 子文档把“真实性”建立在原始命令 `grep -rn '<step-pause' ...` 上，并直接写“实际命中 2 条”，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L209-L220)。
- 但当前仓库中的 `p2-spec-definition.md` 至少有两处注释/说明文本包含字面量 `<step-pause>`，见 [p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L50-L53) 与 [p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L77-L78)。
- 这说明“原始 grep = 2”并不成立。子文档后面的 `A5` 自检脚本实际上也已经偷偷补了过滤条件，说明作者自己也意识到 raw grep 不等于 2，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L577-L583)。

风险：

- D19 的权威输入文件是要交给 PR-8 CI 消费的；如果“盘点方法”和“验收方法”不是同一套语义，后续极容易出现“人工盘点通过、CI 数量不一致”的争议。

建议：

- 统一改成“**只统计真实 XML 标签，不统计注释/说明文字中的字面量**”，并把过滤条件前置写进 §2.A.3，而不是只藏在 §5 自检脚本里。
- DoD 中的“当前 grep `<step-pause` 命中数 = 2”也应同步改成“当前**过滤后**命中数 = 2”。

### 3. 范围与回滚方案已经出现“写的是一套，基线是另一套”

- 元信息把本 PR 记为“6 个文件”，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L55-L58)。
- 但回滚章节又要求额外存在 README 与主文档 §4 的联动提交，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L530-L541)。
- 更关键的是，这两个“联动小修”在当前仓库基线里已经存在：
  - README 已经把 PR-5+6 指向合并文档，见 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/README.md#L12-L14)
  - 主文档 §4 也已经把 PR-5 与 PR-6 都指向同一施工单，见 [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L498-L499)

这会导致三个问题：

- 文件数与工作量口径不稳：到底是 6 个还是 8 个文件。
- commit 拆分规则不稳：`commit 3` 可能根本没有可提交内容。
- 回滚说明不稳：所谓“README 与主文档 §4 索引行回到待展开双行状态”并不是当前基线的自然回退结果。

建议：

- 先基于当前 `main` 重刷一次“真实待改文件清单”。
- 如果 README / 主文档索引已完成，就把 `commit 3` 与相关回滚描述整段删除。
- 如果确实仍需索引联动，就把它正式计入范围、文件数、工作量与 DoD，而不是放在“联动小修”的阴影区。

### 4. 回滚兼容性里塞入了一个未被主文档批准的 PR-8 行为

- 子文档两处把“allowlist 缺失时，PR-8 CI 应降级为 warn 不阻塞”写成预期前提，见 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L227-L230) 与 [pr5-6-deep-dive-and-agents-templates.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L511-L516)。
- 但主文档对 PR-8 的定义是：
  - D14 守门按 allowlist 白名单执行，见 [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L477-L483)
  - DoD 明确要求 allowlist “必须存在且非空”，见 [QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#L523-L529)

这不是文字小偏差，而是会直接影响回滚策略的判断：

- 如果主文档口径为准，那么回滚删除 allowlist 后，PR-8 CI 更可能是 **fail**，不是 **warn**。
- 如果子文档口径为准，那就等于 PR-5+6 反向替 PR-8 做了新的 CI 行为决策，但主文档并未批准这一变更。

建议：

- 不要在 PR-5+6 子文档里擅自承诺 PR-8 的降级策略。
- 统一改为中性表述：`allowlist` 缺失后的 CI 行为**由 PR-8 明确定义**；在该定义落地前，回滚影响应视为“未知，需要联动确认”。

## 建议裁定

- 裁定：**暂不建议直接批准当前版本 PR-5+6 子方案。**
- 通过条件：
  - 先收口 C9 的条件渲染/输出模式问题，明确“成功路径是否真的能省略中间态报告”
  - 先统一 allowlist 的盘点方法、DoD 计数口径与自检脚本语义
  - 先基于当前基线重刷一次真实文件范围、commit 拆分与回滚说明
  - 先移除或上提“PR-8 CI 缺失 allowlist 时降级 warn”的未决假设

## 附注

- 当前方案里有一处次级一致性问题，虽然未列入前 4 个阻塞项，但建议顺手修正：子文档多次引用“§2.2 联动小修”，实际正文中并不存在 `§2.2` 这一小节，见 [pr5-6-deep-dive-and-agents-templates.md:L493-L545](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v2.2/pr5-6-deep-dive-and-agents-templates.md#L493-L545)。
- 若后续需要，我可以继续基于这份 review，给出一个“最小修改版施工单修订建议清单”，仍然只改文档、不碰代码。
