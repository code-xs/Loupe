# PR-7 施工方案 Review 报告（v1.0）

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md`
> 评审日期：2026-04-22
> 评审结论：**Needs Fixes**
> 评审口径：基于 V1.1 方案基线、v4.2 主控约束与当前 PR-7 施工设计稿做静态一致性审查，仅记录已证实问题。

---

## 1. 评审范围与方法

本轮 review 聚焦 4 个维度：

- **方案一致性**：PR-7 施工设计是否与 V1.1 的 B4 / B4.5 / B5、v4.2 主控 README 的 PR-7 范围与 DoD 保持一致
- **兼容性闭环**：`core-rules.xml` / `coder-agent.md` / `reasoning-chain.md` 拆分后是否仍保留足够明确的兼容入口
- **CI 与验收可执行性**：DoD、CI 守门、token 指标与跨平台回归是否有明确可执行的检查口径
- **生成器与平台一致性**：`build-system-prompt.py`、Full / Limited 路径、SubAgent / 非 SubAgent 路径是否存在分叉风险

交叉核验基线：

- 施工单：[pr-7-structural-convergence-token-and-modularization.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md)
- 主控方案：[README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L203-L211)
- 方案基线：[MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1356-L1404)
- 风险与兼容性条目：[V1.1 风险表](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1478-L1479) / [V1.1 兼容性重分类](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1608-L1611)

---

## 2. 总体结论

该施工单的主方向是合理的：把 O15 / O16 作为结构收敛，把 O23 / O24 / O25 作为 token 精准优化主线，把 O11+ / O19+ 作为 agents 模块化与 shared-input-guard 收敛主线，这一拆法与主控 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L203-L211) 以及 V1.1 的批次设计 [V1.1.md](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1356-L1358) 总体一致。

但当前版本仍有 **7 个 Major 级设计缺口**，主要集中在“二选一方案未定版”与“DoD 不可复现”两类问题。如果按文档原样实施，存在以下明确风险：

- `coder-agent.md` 的入口路径、stub 角色与 P5/P6 加载策略未收敛为唯一规范，容易导致 Limited 与 Full 路径分叉
- O25 对 Limited 平台到底是否生效没有定版，和 V1.1 的“范围限定”判断存在冲突
- O23 / O24 / O25 拆分后的 `<load>` 路径缺少强校验门禁，运行时/生成器漂移可能在 CI 中漏检
- Token 指标虽被列为 PR-7 核心 DoD，但缺少明确的测量基线、命令和统计边界，验收不可复现
- O16 的兼容策略未落到“写新读旧 / 保留一个版本周期 / 迁移脚本”级别，和 V1.1 §4.3 不对齐
- `core-rules.xml` 聚合方式、`reasoning-chain` 分类/fallback 规则均停留在“二选一/必要时”层面，实施者解释空间过大

**综合裁定**：当前版本不建议直接开工，建议先修正文档后再进入实施。

---

## 3. Findings

| No. | 严重度 | 问题 | 结论 |
|---|---|---|---|
| 1 | High | `coder-agent.md` 入口/路径/聚合策略未定版，存在 Limited 与 P5/P6 断链风险 | 必须修 |
| 2 | High | O25 在 Limited 平台的落地/收益决策不唯一，和 V1.1 “范围限定”口径冲突 | 必须修 |
| 3 | High | 缺少 `<load>` 目标存在性校验门禁，O23/O24/O25 路径拆分风险未形成 CI 闭环 | 必须修 |
| 4 | High | Token DoD 缺少可复现的测量口径，当前验收不可执行 | 必须修 |
| 5 | High | O16 键名收敛的兼容策略不落地，未对齐 V1.1 §4.3 的“写新读旧 / 保留周期”要求 | 必须修 |
| 6 | High | `core-rules.xml` 聚合实现停留在二选一，影响生成器与兼容入口一致性 | 必须修 |
| 7 | High | O24 分类加载的权重/多分类/fallback 规则未规格化，存在 schema 对不齐风险 | 必须修 |

### Finding 1

**问题**：文档虽然多次强调 `coder-agent.md` 必须保留为入口，但没有把“入口文件路径”“入口是否内嵌三件套”“P5/P6 调用方究竟加载哪一个文件”收敛成唯一规则。当前同时存在“保留薄入口”“P5 显式 load `coder-agent.md`”“追加 workflow / checklist 两段 load，或入口内嵌”的并列写法，容易导致实现者做出不同版本。

**证据**：

- 映射表要求保留 `coder-agent.md` 为薄入口：[pr-7-structural-convergence-token-and-modularization.md:L20-L20](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L20-L20)
- 硬约束要求保留单入口供 Limited 单 prompt 依赖：[pr-7-structural-convergence-token-and-modularization.md:L43-L43](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L43-L43)
- O11+ 设计又允许“入口 include 或固定顺序 `<load>` 两段”：[pr-7-structural-convergence-token-and-modularization.md:L154-L159](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L154-L159)
- P5 处继续写成“显式 load coder-agent.md；若现已是，则追加两份 load，或入口内嵌”： [pr-7-structural-convergence-token-and-modularization.md:L161-L163](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L161-L163)
- 主控 README 明确要求保留 `coder-agent.md` 入口文件：[README.md:L207-L210](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L207-L210)
- V1.1 明确要求 B5 保留原 `coder-agent.md` 为 stub，v4.3 再删：[V1.1.md:L1403-L1403](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1403-L1403)

**影响**：

- Full / Limited / P5 / P6 可能各自走不同加载组合，形成新的同步债
- P5 调 coder-agent 与 P6 只读 checklist 的路径边界不清，DoD 容易“口头成立、实现分叉”
- reviewer 无法据文档判断“唯一正确做法”，后续 diff 也难以做一致性审查

**建议修法**：

- 直接定版“唯一入口策略”：调用方永远 `load agents/coder-agent.md`
- `agents/coder-agent.md` 作为稳定 stub / 聚合入口，内部再按固定顺序加载 `coder-workflow` 与 `contract-checklist-spec`
- P6 只读 checklist 的场景单独明确为“直接 load checklist 文件”的唯一特例，不再保留“追加两段 load / 入口内嵌”双写口径

### Finding 2

**问题**：O25 对 Limited 平台的策略没有唯一结论。文档一处说 Limited `env_subagent=false` 时“镜像相同裁剪规则或保持显式全量块”，另一处又指出如果生成器仍内联完整 `core-rules`，则 O25 在 Limited 的收益为 0；而 V1.1 的兼容性重分类表明确写的是“仅适用于支持 SubAgent 的 Full 平台，Limited 不适用”。

**证据**：

- O25 映射表对 Limited 的写法是“镜像相同裁剪规则或保持显式全量块”： [pr-7-structural-convergence-token-and-modularization.md:L24-L24](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L24-L24)
- GEN-PR7 又承认若 Limited 仍内嵌完整 core-rules，则收益为 0，需要生成器层替换或显式说明： [pr-7-structural-convergence-token-and-modularization.md:L173-L176](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L173-L176)
- V1.1 明确把 O25 归类为“范围限定，仅适用于支持 SubAgent 的 Full 平台；Limited 不适用”： [V1.1.md:L1608-L1611](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1608-L1611)

**影响**：

- 文档既承诺了 O25 能带来整体 token 收益，又没有统一说明 Limited 是否计入收益统计
- 生成器实现者可能做“Limited 裁剪版”，也可能保留“Limited 全量版”，导致产物行为与预算不可比
- reviewer 无法判断 token DoD 中的“3 类 LLM”是否应包含 Limited 上的 O25 收益

**建议修法**：

- 二选一收口为唯一策略：
  - 方案 A：明确 O25 仅影响 Full 平台，Limited 通过 O17+ 间接受益但不计 O25 收益
  - 方案 B：明确 Limited 也裁剪，并写清 build-system-prompt 的具体替换规则、验证方法与回退策略
- 无论选 A 还是 B，都要在 Token DoD 中写清“按平台分别统计”的口径

### Finding 3

**问题**：V1.1 已把“拆错文件路径导致 phase / SubAgent 加载失败”列为 O23/O24/O25 的明确风险，并要求加 `<load>` 路径有效性校验；但 PR-7 的 CI 设计只给了一个可选的 `check-core-rules-loads.sh` 建议，且内容偏“比例统计/策略校验”，没有形成所有 `<load target="...">` 目标都存在且可解析的强闭环。

**证据**：

- V1.1 风险表明确要求“CI 加 `<load>` 路径有效性校验”： [V1.1.md:L1478-L1478](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1478-L1478)
- PR-7 的 CI 章节只把 `check-core-rules-loads.sh` 标成可选建议，且目标是统计 essential 比例与 subagent 不加载全量： [pr-7-structural-convergence-token-and-modularization.md:L180-L189](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L180-L189)
- v4.2 主控 README 的 CI 守门表也未新增这类路径有效性脚本：[README.md:L102-L114](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L102-L114)

**影响**：

- phase / agent / reference / core 任一 `<load>` 路径写错时，可能要到 runtime 或生成器拼装后才暴露
- 文档写了大规模拆分，却没有与风险等级相匹配的自动校验，评审闭环不足
- O23/O24/O25 的“低风险”判断缺少相应工程护栏支撑

**建议修法**：

- 把 `<load>` 路径存在性校验升级为 PR-7 必做项，至少 warning 起步
- 校验范围覆盖 `phases/**`、`agents/**`、`reference/**`、`core/**` 与生成器引用源
- 统计类脚本可以保留，但应作为第二层优化检查，不能替代“文件存在性/可达性”主守门

### Finding 4

**问题**：PR-7 把“P3 complex 路径 token 下降 ≥ 25%”列为核心 DoD，但没有提供基线 commit、采样 case、统计边界、测量命令或工具；更弱的是，DoD 中还允许用“字符/token 或行数前后对比”支撑 O25 收益，这会使结果无法复现。

**证据**：

- 硬约束写明 P3 complex 路径相对 PR-6 baseline 下降 ≥ 25%：[pr-7-structural-convergence-token-and-modularization.md:L46-L46](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L46-L46)
- PR-level DoD 继续要求 Token ≥25% 下降，但未补具体测量方法： [pr-7-structural-convergence-token-and-modularization.md:L219-L220](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L219-L220)
- O25 DoD 甚至允许“字符/token 或行数前后对比”： [pr-7-structural-convergence-token-and-modularization.md:L219-L219](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L219-L219)
- 主控 README 把 token 实测达标列为 PR-7 DoD：[README.md:L209-L210](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L209-L210)
- V1.1 也把 B4.5 的 token 指标设为强制门槛：[V1.1.md:L1388-L1390](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1388-L1390)

**影响**：

- reviewer 无法复现“≥25%”是否成立，只能相信主观描述
- 不同人可能用不同 tokenizers、不同 prompt 边界、不同样本，结论不可比
- 若后续做 PR-7.1 / rollback，无法判断收益是否回退

**建议修法**：

- 明确 baseline：PR-6 合入后某个固定 commit 或 tag
- 明确样本：至少 1 个固定 P3 complex case，最好补 seed-10 子集
- 明确口径：统计输入 prompt token，是否含系统拼装、是否含 subagent prompt、是否含输出
- 明确工具与命令：不要再允许“字符/行数代替 token”

### Finding 5

**问题**：O16 计划将 deep-dive 子工作流的 `emit_*` 键改成 `deep_dive_optional_artifacts.*`，并删除/清零 `known_legacy_aliases`；但文档只给出“若线上已有工作区，可选一次性兼容；否则可声明新会话只认新 key”的松散表述，没有落到 V1.1 §4.3 要求的“写新读旧 / 保留一个版本周期 / 迁移脚本 / 强 CI 校验”级别。

**证据**：

- O16 目标包括删除或清零 alias：[pr-7-structural-convergence-token-and-modularization.md:L94-L100](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L94-L100)
- 迁移策略只写成“可选一次性兼容”或“文档声明新会话只认新 key”： [pr-7-structural-convergence-token-and-modularization.md:L103-L105](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L103-L105)
- V1.1 §4.3 明确要求 schema 变更遵守“写新读旧”“旧字段保留一个版本周期”“强 CI 校验”： [V1.1.md:L1397-L1404](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1397-L1404)

**影响**：

- 旧 deep-dive 工作区、旧配置文件、已有脚本若仍写 `emit_*`，可能在没有迁移说明的情况下静默失效
- 文档中的“完全等价”判断缺少兼容策略支撑
- reviewer 无法判断 alias 删除是本 PR 允许的，还是应先经历 deprecated 周期

**建议修法**：

- 明确兼容政策：至少保留一个版本周期 alias，或强制提供迁移脚本并在 DoD 中验证
- 在 O16 DoD 中加入“旧配置/旧会话兼容”专项验收
- 如果确认不存在线上 deep-dive 工作区，也应把“为何可直接切断兼容”写成明确前提，而不是可选描述

### Finding 6

**问题**：O23 对 `core-rules.xml` 的聚合实现给出了“两段 `<load>` 聚合”或“字面拼接为单根 `<core-rules>`”两种方案，但没有在施工单里定版。这不是实现细节，而是会影响生成器读取逻辑、兼容入口行为、后续 grep 习惯和 reviewer 对差异的判断。

**证据**：

- O23 章节明确把 `core-rules.xml` 聚合方式写成二选一： [pr-7-structural-convergence-token-and-modularization.md:L117-L120](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L117-L120)
- GEN-PR7 又要求 `build-system-prompt.py` 同步改 L1 读取逻辑： [pr-7-structural-convergence-token-and-modularization.md:L169-L176](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L169-L176)
- V1.1 的兼容要求只规定“保留聚合入口”，并未允许实现阶段保持二义性： [V1.1.md:L1192-L1194](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1192-L1194)

**影响**：

- 不同实施者可能各自选择不同聚合方式，导致生成器、phase 加载与文档引用结果不一致
- 后续若出现 system-prompt diff 异常，难以判断是拆分策略问题还是聚合方式问题
- “兼容入口仍可用”在没有定版实现时，只是目标陈述，不是可执行设计

**建议修法**：

- 在文档中直接定版一种聚合方式，不再保留并列口径
- 同步补一句“生成器按何方式解析聚合入口”，避免 `build-system-prompt.py` 再自行推断
- 如需保留另一方案，应该明确标记为 rejected alternative，而不是让实施时再选

### Finding 7

**问题**：O24 章节把 `reasoning-chain` 的分类加载描述为“按 `issue_card.主分类` 读取，遇多分类取权重最高，必要时 fallback 全量”，但没有把主分类字段、权重来源、fallback 触发条件做成规范化协议；DoD 也只写“与 `issue_card` 字段对齐主模板”，仍缺少执行级定义。

**证据**：

- O24 仅笼统写“读完 `issue_card.主分类` 后，load core + 命中 guide；多分类取权重最高，其余必要时 fallback 全量”： [pr-7-structural-convergence-token-and-modularization.md:L134-L138](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L134-L138)
- DoD 仅要求“P3 子分类加载逻辑与 `issue_card` 字段对齐主模板”： [pr-7-structural-convergence-token-and-modularization.md:L218-L218](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/pr-7-structural-convergence-token-and-modularization.md#L218-L218)
- V1.1 对 O24 的表述同样是“权重最高一类，必要时 fallback 全量”，但这更要求施工单把具体字段与实现规则写清： [V1.1.md:L1228-L1234](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1228-L1234)

**影响**：

- 不同实现者可能使用不同字段名、不同权重定义、不同 fallback 触发条件
- 这类隐性分叉会直接影响 P3 推理质量，却难以被普通 diff 看出
- “OVHSC 与公式一句不减”虽然被强调，但分类选择错误仍会造成实质质量回归

**建议修法**：

- 把 `issue_card` 中用于分类的字段名、枚举值、权重来源写成明确规范
- 把 fallback 触发条件收敛成固定规则，例如“主分类缺失 / 置信度并列 / 多分类差值低于阈值时 fallback 全量”
- 最好在 PR-7 文档里补一个最小 truth table，便于 reviewer 与实现者使用相同判定逻辑

---

## 4. 已确认优点

以下方向本轮确认是正确的，可保留：

- **分批次组织合理**：B4 / B4.5 / B5 的顺序与主控 [README.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/construction-plans/v4.2/README.md#L203-L211) 及 V1.1 [批次表](file:///Users/bytedance/Code/loupe/doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md#L1356-L1358) 一致
- **兼容入口意识正确**：明确保留 `core-rules.xml` 聚合入口、`coder-agent.md` 入口文件，这一点方向是对的
- **生成器联动意识较强**：能显式列出 GEN-PR7 清单，说明已意识到 `build-system-prompt.py` 不是被动后置项
- **砍 scope 预案可用**：若时间盒不足，优先保 O23 / O24 / O25 + 最小 O11+ 的裁剪逻辑是合理的
- **实施前补 grep 附录的要求正确**：先生成精确触达面再开工，符合 v4.2 子文档“rebase 后对齐锚点”的管理方式

---

## 5. 最终裁定

**裁定**：`Needs Fixes`

**建议先修的最小集合**：

1. 对 `coder-agent.md` / O25 / `core-rules.xml` 三处“二选一方案”直接定版，删除并列口径
2. 给 O16 补齐兼容策略，至少与 V1.1 §4.3 同级别
3. 把 `<load>` 目标存在性校验纳入 PR-7 必做 CI，而不是可选建议
4. 把 Token DoD 改写成可复现的 SOP：baseline、样本、命令、统计边界、平台口径全部固定
5. 给 O24 补齐分类字段、权重和 fallback 的明确决策表

若以上 5 点收口，本方案即可进入下一轮定向复审；在此之前，不建议按当前版本直接实施。
