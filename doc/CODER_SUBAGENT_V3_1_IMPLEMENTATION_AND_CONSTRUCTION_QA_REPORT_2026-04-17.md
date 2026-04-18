# Coder SubAgent V3.1 实现分析与施工方案质检报告

- 评审日期: 2026-04-17
- 评审范围:
  - 技术方案: `https://bytedance.larkoffice.com/docx/JqH3dacSMoAEW9x5v1EcgRxtngb`
  - 施工方案: `https://bytedance.larkoffice.com/docx/YPSEdLM7Bo2HXKx96KAc5xDenOe`
  - 代码仓库: `/Users/bytedance/Code/loupe`
- 评审约束: 只读分析, 不修改代码

## 1. 执行摘要

### 1.1 总体结论

本次评审结论分为两部分:

1. **V3.1 技术方案本身方向正确, 架构设计完整, 具备较强可实施性。**
2. **当前工程实现尚未接入该方案的核心改造链路, 不能按“已落地”验收。**
3. **施工方案总体方向正确, 但仍存在 4 个需要先修订的执行级问题, 否则极易在施工阶段引入假通过或联调偏差。**

### 1.2 最终判定

- 技术方案质量: **通过**
- 当前工程落地状态: **不通过**
- 施工方案可直接开工性: **有条件通过**

建议口径:

> 当前仓库已具备 SubAgent 机制、Deep-Dive 回注、Eval 基础框架等承接条件, 但 Coder SubAgent V3.1 的核心链路尚未接入。现状应定义为“基础具备, 方案正确, 落地未完成”; 施工方案在修正本文列出的执行级问题后方可作为正式施工蓝图。

## 2. Findings

### F1. 高风险: `artifact-checklist.yaml` 施工片段与现有解析器/配置结构不兼容, 照单施工会导致条件产物规则失效

- 施工方案 `C-7/C-8` 要求新增如下结构: `file`, `min_size_bytes`, `required: conditional`, `condition.field/value`, `on_missing: fail`。
- 但当前仓库中的产物配置实际使用 `path` 和 `min_size` 字段, 解析器也只读取这两个字段, 见 [artifact-checklist.yaml](file:///Users/bytedance/Code/loupe/eval-framework/artifact-checklist.yaml#L4-L103) 和 [artifact_checker.py](file:///Users/bytedance/Code/loupe/eval-framework/artifact_checker.py#L104-L156)。
- 如果施工人员仅按方案中的 YAML 片段新增规则, 而没有同步重构解析器字段兼容层, 新增的 `contract-checklist.md` / `error-dump.md` 规则将大概率不会被正确识别, 形成“文档已写、门禁未生效”的假落地。

结论:

- 这不是文案问题, 而是**会直接导致 Eval 硬门禁失效的执行级缺陷**。

修订建议:

- 明确二选一:
  - 方案 A: 延续现有 schema, 新规则统一使用 `path` / `min_size`
  - 方案 B: 显式声明 `artifact_checker.py` 需要完成 schema 迁移兼容, 同时支持旧字段和新字段
- 未补齐前, 不建议进入 Phase C 施工。

### F2. 中风险: P5 Step 6 的失败分支缺少显式终止/跳转语义, 可能在 Human-Review 后继续落入 Step 7

- 施工方案将 Step 6 定义为“文件哨兵法三优先级判定”, 但在 Human-Review / Incomplete 分支下未显式要求 `goto` 或阶段终止。
- 当前工作流文件中已有显式跳转用法作为先例, 例如 [p5-fix-impl.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p5-fix-impl.md#L89-L93) 在跳过静态验证时会明确 `goto step="6"`。
- 若开发者按施工方案字面实现 Step 6, 再沿用“保留 Step 7 状态流转”的写法, 就存在失败路径继续执行 Step 7 并写回 `Verifying` 的风险。

结论:

- 这是**状态机控制流不封闭**问题, 会污染 `current_state` 和后续验收。

修订建议:

- 在施工方案中显式增加:
  - Human-Review 分支: 立即结束当前阶段
  - Incomplete 分支: 立即结束当前阶段
  - 仅 Success 分支允许进入 Step 7

### F3. 中风险: `repair_route` / `execution_status` 的读取口径未被明确规格化, 产物条件判断存在实现歧义

- V3.1 方案要求在 `impl-report.md` 中写入 `Repair-Route` 和 `Execution-Status` 元信息。
- 施工方案 C-8 又要求 `artifact_checker.py` 从 `impl-report.md` 中读取 `repair_route` / `execution_status`。
- 当前仓库没有任何现成的元信息解析器或字段规范化逻辑, 见 [artifact_checker.py](file:///Users/bytedance/Code/loupe/eval-framework/artifact_checker.py#L31-L102)。
- 也就是说, 施工方案没有明确:
  - 是按原文标题匹配 `Repair-Route` / `Execution-Status`
  - 还是读取后标准化成 `repair_route` / `execution_status`
  - 还是通过 frontmatter / YAML 块统一承载

结论:

- 这是**契约键命名未规格化**问题, 后果是条件门禁可能随机失效或误判。

修订建议:

- 在施工方案中补充唯一解析标准, 推荐:
  - `impl-report.md` 保持展示字段 `Repair-Route` / `Execution-Status`
  - `artifact_checker.py` 内部统一标准化映射:
    - `Repair-Route` -> `repair_route`
    - `Execution-Status` -> `execution_status`

### F4. 中风险: Skill 镜像漂移已经真实存在, 但施工方案把同步放到 Phase D 末端, 风险分级偏低

- 施工方案把镜像同步安排到 Phase D, 默认前置 A/B/C 均以根目录为唯一事实源。
- 但当前仓库根目录与 `.cursor` / `.trae` 副本已存在真实差异, 不是理论风险。`diff -rq` 结果显示:
  - `mobile-qa-workflow/templates/context-bundle.md`
  - `.cursor/skills/mobile-qa-workflow/templates/context-bundle.md`
  - `.trae/skills/mobile-qa-workflow/templates/context-bundle.md`
  已不一致。
- 证据见根目录模板 [context-bundle.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/templates/context-bundle.md#L16-L24), 其中存在 `Specialized Workflow Inputs` 段; 镜像版本 [context-bundle.md](file:///Users/bytedance/Code/loupe/.cursor/skills/mobile-qa-workflow/templates/context-bundle.md#L16-L23) 与 [context-bundle.md](file:///Users/bytedance/Code/loupe/.trae/skills/mobile-qa-workflow/templates/context-bundle.md#L16-L23) 缺失该段。

结论:

- 当前已经不是“改动后需同步”, 而是**仓库现状已漂移**。

修订建议:

- 将镜像一致性从 Phase D 的建议动作提升为:
  - Phase A 完成后一次同步
  - Phase B/C 完成后再同步
  - Phase E 前做最终差异校验

## 3. V3.1 技术方案拆解与当前工程映射

### 3.1 方案模块完整度

V3.1 技术方案覆盖的模块是完整且闭环的, 主要包括:

1. **角色层**
   - `coder-agent` 人设
   - 输入契约 / 输出契约
   - 命名规范
   - 工具白名单 / 黑名单

2. **实施层**
   - 契约溯源
   - 精确编码
   - 微验证与 3 轮自愈
   - 产出移交

3. **产物层**
   - `impl-report.md`
   - `contract-checklist.md`
   - `error-dump.md`

4. **编排层**
   - `core-rules.xml` 注册
   - `default-config.yaml` 产物路径
   - `p5-fix-impl.md` 路由与 SubAgent 调用
   - `workflow.xml` io-contract
   - `p6-verification.md` 消费闭环

5. **平台降级层**
   - `system-prompt.md`
   - `PLATFORM-GUIDE.md`
   - Full / Limited / Minimal 三档策略

6. **评测层**
   - 评分链路 6 文件联动
   - 产物完整性硬门禁 2 文件联动
   - 9 维度权重与 baseline 观测指标

7. **治理层**
   - 三份 Skill 镜像一致性
   - 验收门槛
   - 冒烟路径

结论:

- 从设计完备性看, V3.1 不是局部 patch, 而是一套**从 P5 到 Eval 的全链路升级方案**。

### 3.2 当前工程真实实现状态

#### A. 已具备的承接基础

- SubAgent 机制已经成熟存在, 并支持属性式 `invoke-subagent`, 见 [core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L85-L115)。
- Deep-Dive 回注 P5 已打通, `defensive-fix-design.md` 可被消费, 见 [p5-fix-impl.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p5-fix-impl.md#L25-L44)。
- Eval 基础框架已经存在, 包括评分引擎、Judge、对比器、报告器和产物校验器, 见 [judge.py](file:///Users/bytedance/Code/loupe/eval-framework/judge.py#L1-L157), [scoring_engine.py](file:///Users/bytedance/Code/loupe/eval-framework/scoring_engine.py#L50-L82), [artifact_checker.py](file:///Users/bytedance/Code/loupe/eval-framework/artifact_checker.py#L31-L102)。

#### B. 尚未落地的核心改造

- `coder-agent` 文件不存在, 仓库检索结果为空。
- `core-rules.xml` 未注册 `coder-agent`, 当前仅有 `curator/investigator/challenger/arbiter/fix-proposer`, 见 [core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L93-L109)。
- P5 仍是主 Agent 直接改代码, 未切到黑盒 SubAgent, 见 [p5-fix-impl.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p5-fix-impl.md#L60-L87)。
- 默认配置没有 `output_contract_checklist` / `output_error_dump`, 见 [default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/default-config.yaml#L10-L18)。
- 工作流 io-contract 仍是旧口径, P5 只输出 `impl-report.md`, P6 也不接 `contract-checklist.md`, 见 [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L9-L16)。
- P6 验证阶段没有任何 `contract-checklist.md` 交叉验证逻辑, 见 [p6-verification.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L25-L35)。
- `impl-report.md` 模板未扩展 `Execution-Status` / `Repair-Route` / 溯源记录 / 纠错记录 / 防御性修复记录, 见 [impl-report.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/templates/impl-report.md#L6-L58)。
- `verification-report.md` 模板未新增 “契约溯源交叉验证结果” 节, 见 [verification-report.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/templates/verification-report.md#L14-L80)。
- `platform-checklist.md` 仍只有平台专项列表, 缺少通用溯源约束头部章节, 见 [platform-checklist.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/reference/platform-checklist.md#L1-L60)。
- `system-prompt.md` 仍是旧版 P5/P6 摘要, 未包含 Limited 平台契约溯源门禁, 见 [system-prompt.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/system-prompt.md#L275-L337)。

#### C. Eval 改造现状

- 评分维度仍是 6 维, 未扩展到 `contract_first_pass_accuracy` / `hallucination_interception` / `self_healing_rate`, 见 [scoring-rubric-base.yaml](file:///Users/bytedance/Code/loupe/eval-framework/scoring-rubric-base.yaml#L12-L20), [judge.py](file:///Users/bytedance/Code/loupe/eval-framework/judge.py#L90-L157), [scoring_engine.py](file:///Users/bytedance/Code/loupe/eval-framework/scoring_engine.py#L55-L62)。
- 产物硬门禁仍只覆盖旧产物, 未纳入 `contract-checklist.md` / `error-dump.md`, 见 [artifact-checklist.yaml](file:///Users/bytedance/Code/loupe/eval-framework/artifact-checklist.yaml#L4-L103)。
- `artifact_checker.py` 也尚不支持 `conditional` 产物规则, 见 [artifact_checker.py](file:///Users/bytedance/Code/loupe/eval-framework/artifact_checker.py#L64-L102)。

## 4. 18 项必须项核验表

| # | 验收项 | 结论 | 说明 |
|---|---|---|---|
| 1 | 新增 `agents/coder-agent.md` | 不通过 | 仓库无该文件 |
| 2 | `core-rules.xml` 注册 `coder-agent` | 不通过 | 仅注册现有 5 个主工作流 Agent |
| 3 | `p5-fix-impl.md` 使用属性式调用 `coder-agent` | 不通过 | P5 仍为主 Agent 直改代码 |
| 4 | `default-config.yaml` 新增 2 个输出键 | 不通过 | 无 `output_contract_checklist` / `output_error_dump` |
| 5 | `workflow.xml` 使用“条件必需” io-contract | 不通过 | P5/P6 仍为旧 I/O 契约 |
| 6 | `templates/impl-report.md` 含 5 个新增字段/节 | 不通过 | 模板仍为旧版 |
| 7 | `templates/contract-checklist.md` 存在且满足 5 必填字段 | 不通过 | 文件不存在 |
| 8 | `templates/error-dump.md` 存在 | 不通过 | 文件不存在 |
| 9 | `platform-checklist.md` 顶部含通用溯源规则 | 不通过 | 只有平台专项检查项 |
| 10 | `system-prompt.md` 含 Limited 降级溯源门禁 | 不通过 | 仍为旧版 P5 摘要 |
| 11 | `p6-verification.md` 含 Checklist 消费和 Repair-Route 分支 | 不通过 | 无此逻辑 |
| 12 | `templates/verification-report.md` 含交叉验证结果节和 `SKIPPED` | 不通过 | 无该节 |
| 13 | 评分体系 6 文件联动改造完成 | 不通过 | 仍是 6 维旧版本 |
| 14 | `artifact-checklist.yaml` 含新产物条件规则 | 不通过 | 无 `contract-checklist.md` / `error-dump.md` 规则 |
| 15 | `artifact_checker.py` 支持条件必需产物校验 | 不通过 | 无 `conditional` 分支 |
| 16 | 三份 Skill 镜像一致 | 不通过 | 已发现 `context-bundle.md` 漂移 |
| 17 | `invoke-subagent` 仅出现属性式写法 | 通过 | 当前检索结果均为属性式 |
| 18 | P5 Step 4 含输出路径初始化 | 不通过 | 现有 Step 4 未初始化任何新输出路径 |

### 4.1 核验汇总

- 通过: **1 / 18**
- 不通过: **17 / 18**

结论:

- 若按 V3.1 “必须项”口径验收, 当前仓库**明确不能作为已完成实现验收**。

## 5. 对施工方案的综合评价

### 5.1 通过项

- 施工方案对仓库现状的主判断总体正确:
  - 已识别 `coder-agent` 缺失
  - 已识别 P5 仍是主 Agent 实施
  - 已识别 Eval 需要 6 文件评分链路 + 2 文件硬门禁链路改造
- 分阶段拆解较完整:
  - Phase A 聚焦新增
  - Phase B 聚焦编排与模板
  - Phase C 聚焦 Eval
  - Phase D 聚焦镜像
  - Phase E 聚焦联调
- 与 V3.1 技术方案的章节映射基本完整, 没有明显的大块遗漏。

### 5.2 需要修订后再执行的点

- 必须先修订本文 `F1` 到 `F4`
- 建议在施工方案正文中增加一节“执行前置约束”, 明确:
  - 产物 schema 是否迁移
  - 状态机失败分支如何终止
  - 元信息字段如何标准化解析
  - 什么时候必须同步镜像

## 6. 结论

本次质检的严谨结论如下:

1. **V3.1 技术方案是对的。**
2. **当前工程尚未实现 V3.1 的核心改造。**
3. **施工方案可以继续推进, 但必须先修正执行级歧义和 schema 不兼容问题。**

建议最终验收口径:

> 当前 Loupe 工程已具备承接 Coder SubAgent V3.1 的基础设施, 但核心链路尚未接入, 实现状态不应被描述为“已完成落地”。本次施工方案方向可通过, 但须先修正 Eval 条件产物 schema、P5 失败分支控制流、元信息字段解析口径及镜像同步时机, 然后再进入正式开发与联调阶段。
