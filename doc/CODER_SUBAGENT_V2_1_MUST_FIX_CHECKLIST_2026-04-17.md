# Coder SubAgent 方案 V2.1 必改清单

> 文档日期：2026-04-17  
> 审阅对象：飞书方案《Coder SubAgent 技术方案 V2》  
> 审阅结论：继续只做审阅，不修改代码；本清单用于指导 V2 -> V2.1 的方案修订  
> 目标：将 V2 修订为可直接指导落地实施的“低歧义、低阻断、可验收”版本

---

## 1. 结论摘要

V2 相比 V1 已有明显提升，已经补齐了以下关键能力：

- Contract Checklist 的反空泛规范
- Error Dump 标准模板
- Phase 6 对 Contract Checklist 的消费闭环
- Skill 镜像一致性管理策略
- Eval 新维度与收益度量思路
- Full / Limited / Minimal 平台差异化策略

从方案完整度看，V2 已经接近可实施版本。  
但本次复审确认，**V2 仍残留若干会在实际落地时触发阻断或歧义的关键问题**。  
这些问题如果不先修正，实施阶段大概率会在以下三个方面卡住：

1. DSL 写法与现有 `core-rules.xml` 不一致
2. 新增产物链路缺少配置与变量承载层
3. Eval 适配被低估为“只改 rubric”，实际需要联动修改多个代码文件

因此，本次建议结论为：

> **V2 方向正确，但仍不建议直接开工；应先完成 V2.1 级别的方案修订。**

---

## 2. 必改项总览

以下问题按优先级分为：

- P0：阻断实施，必须修
- P1：高风险，强烈建议修
- P2：建议修，避免后期返工

### P0 阻断项

1. 统一 `invoke-subagent` 写法，消除文档内部 DSL 自相矛盾
2. 补齐新增产物 `contract-checklist.md` / `error-dump.md` 的配置承载与变量来源
3. 扩展 Eval 改造范围定义，不能只停留在 `scoring-rubric-base.yaml`

### P1 高风险项

4. 明确主 Agent 如何判定 Coder SubAgent 成功 / Human-Review 的返回契约
5. 修正“幻觉识别率”的指标定义，避免错误激励
6. 明确 P6 消费 Contract Checklist 后如何影响验证结论与报告输出

### P2 建议项

7. 统一方案中的路径变量命名，避免 `contract_checklist` / `output_contract_checklist` 混用
8. 在文件总览中显式纳入被间接影响的配套文件，避免实施时遗漏
9. 增加“方案修订完成后的最小联调验证步骤”

---

## 3. P0 阻断项

## 3.1 必改项 1：统一 `invoke-subagent` 写法

### 问题描述

V2 文档内部对 `invoke-subagent` 给出了两种写法：

#### 写法 A：块状写法

文档中存在如下片段：

```xml
<invoke-subagent subagent_type="coder-agent">
  <load target="mobile-qa-workflow/core/core-rules.xml"/>
  <load target="mobile-qa-workflow/agents/coder-agent.md"/>
  输入：...
</invoke-subagent>
```

#### 写法 B：属性式写法

文档中又存在如下片段：

```xml
<invoke-subagent subagent_type="coder-agent" subagent_prompt="
    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
    <load target='mobile-qa-workflow/agents/coder-agent.md' prompt='加载角色定义'/>
    ...
"/>
```

而当前仓库中的 `core-rules.xml` 已明确定义：

- `invoke-subagent` 的关键参数为：
  - `subagent_type`
  - `subagent_prompt`
- 主 Agent 必须将 `subagent_prompt` 作为黑盒字符串原样透传

这意味着当前框架语义更接近**属性式写法**，而不是块状 XML 子节点写法。

### 风险

若不统一：

- 实施人员可能按块状写法修改 `p5-fix-impl.md`
- 最终与现有 `core-rules.xml` 语义不兼容
- 文档本身会出现“同一方案给出两套不一致落地方式”的问题

### V2.1 必改要求

在整份 V2 文档中：

1. **删除所有块状 `<invoke-subagent>...</invoke-subagent>` 示例**
2. **统一改为 `subagent_prompt="..."` 的属性式写法**
3. 在“Review 问题追踪表”中，把“DSL 兼容性”状态更新为：
   - “V2.1 已统一为属性式写法，与当前 `core-rules.xml` 一致”

### 建议修订文件位置

- 飞书方案 §4.3 `p5-fix-impl.md` 改造方案
- 飞书方案 §4.5 主流程 `workflow.xml` 调用示例
- 飞书方案附录或示例中所有 `invoke-subagent` 代码块

### 验收标准

- 整份方案中 `invoke-subagent` 只出现一种写法
- 该写法与现有 `core-rules.xml` 参数定义一致

---

## 3.2 必改项 2：补齐新增产物的配置承载与变量来源

### 问题描述

V2 已新增以下产物：

- `contract-checklist.md`
- `error-dump.md`

并且在方案中要求：

- P5 输出这些产物
- 主 Agent 在 Step 6 读取这些产物
- P6 消费 `contract-checklist.md`

但 V2 目前只修改了：

- `workflow.xml`
- `p5-fix-impl.md`
- `p6-verification.md`
- 模板文件

却没有把以下承载层纳入改造总览：

1. `core/default-config.yaml`
2. 相关变量命名规范
3. 配置更新动作

当前仓库中 `default-config.yaml` 仅定义了：

- `output_issue_card`
- `output_spec`
- `output_context_bundle`
- `output_rca_report`
- `output_fix_design`
- `output_impl_report`
- `output_verification_report`
- `output_knowledge_card`

并没有：

- `output_contract_checklist`
- `output_error_dump`

### 风险

如果这一层不补：

- 主 Agent 中读取 `{contract_checklist}` / `{output_contract_checklist}` 没有统一来源
- `config_source` 无法记录新产物路径
- 工作流恢复、阶段协作和调试都无法稳定依赖这些产物

### V2.1 必改要求

在“需新增/修改的文件总览”中，新增：

1. `core/default-config.yaml`
   - 新增 `output_contract_checklist`
   - 新增 `output_error_dump`

2. 若需要状态层辅助判断，也要明确是否修改：
   - `core/workflow-status-template.yaml`

3. 在 P5 / P6 相关步骤中明确写出：
   - 更新 `config_source`：`output_contract_checklist = ...`
   - 更新 `config_source`：`output_error_dump = ...`（失败场景）

### 建议变量命名

建议统一使用以下命名：

- `output_contract_checklist`
- `output_error_dump`

避免在方案中混用：

- `contract_checklist`
- `output_contract_checklist`
- `contract-checklist`

### 建议修订文件位置

- 飞书方案 §4.1 文件总览
- 飞书方案 §4.3 P5 改造方案
- 飞书方案 §4.4 `workflow.xml` io-contract 更新
- 飞书方案 §4.10 P6 消费链路闭环

### 验收标准

- 方案中所有新增产物都有统一的配置承载字段
- 所有读取动作都能对应到明确变量来源
- 不再出现“只定义文件名，不定义路径来源”的情况

---

## 3.3 必改项 3：扩展 Eval 改造范围定义

### 问题描述

V2 已经提出在 `scoring-rubric-base.yaml` 中新增评分维度，这是对的。  
但当前仓库中的 Eval 系统并不是“纯配置驱动”，而是“配置 + 代码常量 + prompt 模板”共同驱动。

当前实现中，至少以下文件仍写死了旧维度集合：

- `eval-framework/scoring_engine.py`
- `eval-framework/judge.py`
- `eval-framework/report_generator.py`
- `eval-framework/comparator.py`
- `eval-framework/weakness_detector.py`
- 以及可能的 `__init__.py` 维度文档说明

例如：

- `ScoringEngine.DIMENSIONS` 是写死的
- `LLMJudge` 默认权重是写死的
- Judge Prompt 只要求输出 6 个旧维度
- 报告与对比器可能也只识别旧维度

### 风险

如果只修改 `scoring-rubric-base.yaml`：

- 新维度可能不会被真正评估
- 评分 prompt 不会要求模型输出新维度
- 加权逻辑不会纳入新维度
- 对比报表不会展示新维度

最终出现“方案里写了评分维度，Eval 实际没生效”的假闭环。

### V2.1 必改要求

将 Eval 适配从“改配置”升级为“配置 + 代码联动改造”，在方案中明确新增一个小节：

#### Eval 实施影响文件

至少列出：

- `eval-framework/scoring-rubric-base.yaml`
- `eval-framework/scoring_engine.py`
- `eval-framework/judge.py`
- `eval-framework/report_generator.py`
- `eval-framework/comparator.py`
- `eval-framework/weakness_detector.py`

并说明各自职责：

- `scoring-rubric-base.yaml`：权重与维度定义
- `scoring_engine.py`：维度集合与加权统计
- `judge.py`：评分 prompt、解析与默认权重
- `report_generator.py`：新维度报告展示
- `comparator.py`：改造前后对比
- `weakness_detector.py`：薄弱项分类与归因

### 建议修订文件位置

- 飞书方案 §6 Eval 体系适配
- 飞书方案 §4.1 文件总览（如需体现影响范围）

### 验收标准

- Eval 改造不再只描述 rubric
- 方案明确指出需要联动修改的代码文件
- 评测维度从“建议”升级为“可实施改造范围”

---

## 4. P1 高风险项

## 4.1 必改项 4：定义 SubAgent 返回契约

### 问题描述

V2 在 P5 Step 6 中写到：

- 检查 SubAgent 返回状态
- 成功则进入 Verifying
- Human-Review 则读取 `error-dump.md`

但当前输出契约只定义了文件产物，没有定义：

- 状态字段
- 返回枚举
- 哨兵文件
- 主 Agent 如何做机读判定

### 风险

如果没有统一契约：

- 主 Agent 只能靠“某文件是否存在”推断状态
- 存在“半成功、部分失败、文件落盘不完整”的灰区
- 实施者会各自理解“成功”的含义

### V2.1 必改要求

在方案中补一段“SubAgent 返回判定协议”，至少定义以下任一种方式：

#### 方案 A：文件哨兵法

- 成功：必须生成 `impl-report.md`
- 成功且有溯源：必须生成 `contract-checklist.md`
- 失败：必须生成 `error-dump.md`

主 Agent 判定规则：

1. 若存在 `error-dump.md` -> Human-Review
2. 若存在 `impl-report.md` 且不存在 `error-dump.md` -> Success
3. 若仅部分文件存在 -> Incomplete，视为流程异常

#### 方案 B：报告状态字段法

在 `impl-report.md` 顶部增加：

- `Execution-Status: Success | Human-Review | Incomplete`

两者任选一种，但必须统一。

### 验收标准

- 主 Agent 能不依赖猜测地判定 SubAgent 返回结果
- 成功 / 失败 / 不完整 三类状态定义明确

---

## 4.2 必改项 5：修正“幻觉识别率”定义

### 问题描述

V2 目前将“幻觉识别率”定义为：

> `contract-checklist.md` 中 ❌ 转 ✅ 的记录

这个定义存在明显偏差：

- 如果模型一开始就完全正确，没有 `❌ -> ✅`，反而无法得分
- 如果模型先犯错再纠正，会更容易形成该类记录

这会产生错误激励。

### 风险

指标会鼓励“先出错再修正”的行为，而不是“首次就正确”。

### V2.1 必改要求

建议将该维度改名并拆分：

#### 推荐拆分方式

1. **契约首轮正确率**
   - 定义：首轮 checklist 中 “期望值 = 实际值” 的比例

2. **幻觉拦截命中数**
   - 定义：本应产生资源/签名/枚举幻觉，但在溯源阶段被发现并修正的次数

3. **自纠错成功率**
   - 保留在微验证阶段，用于度量编译/静态检查失败后的恢复能力

如果不拆，至少应把“幻觉识别率”改成：

> “契约溯源阶段发现并拦截的潜在错误引用比例”

而不是简单写成 `❌ -> ✅` 条数。

### 验收标准

- 指标不会惩罚首轮正确
- 指标定义与名称一致
- 不再把“纠错行为”误当成“识别能力”

---

## 4.3 必改项 6：明确 P6 如何把 Checklist 结论写入 Verification Report

### 问题描述

V2 已经规定 P6 Step 2 会读取 `contract-checklist.md` 并校验：

- 源文件是否存在
- 行号是否真实
- 条数是否覆盖引用数
- 模糊路径是否标记 `[SUSPICIOUS]`

但还没有进一步说明：

- 这些异常是否会影响 L1 通过与否
- 是否需要在 `verification-report.md` 中新增一节
- `[SUSPICIOUS]` 是 warning 还是 fail

### 风险

P6 虽然“消费了 checklist”，但最终报告层可能完全看不出结果。  
这样就会出现“验证逻辑存在，但不可审计”的问题。

### V2.1 必改要求

在方案中明确：

1. `verification-report.md` 增加“契约溯源交叉验证结果”节
2. 定义异常等级：
   - `PASS`：路径、行号、条数、值匹配均正常
   - `WARNING`：存在 `[SUSPICIOUS]` 但未影响最终代码正确性
   - `FAIL`：溯源记录不足、路径失真、关键值不匹配
3. 定义对验证结论的影响：
   - `FAIL` -> L1 不通过
   - `WARNING` -> L1 通过但需在报告中保留风险

### 验收标准

- P6 对 checklist 的消费结果能体现在最终报告
- 验证结论与异常等级有明确映射

---

## 5. P2 建议项

## 5.1 必改项 7：统一变量命名

### 问题描述

V2 中同时出现了：

- `contract-checklist.md`
- `{contract_checklist}`
- `output_contract_checklist`

这是正常的“文件名 / 模板变量 / 配置键”三层差异，但文档中没有把它们映射说明写清楚，阅读时容易混淆。

### V2.1 建议

增加一个“变量命名映射表”：

| 层级 | 命名 |
|------|------|
| 文件名 | `contract-checklist.md` |
| 配置键 | `output_contract_checklist` |
| 运行时变量 | `{output_contract_checklist}` |

`error-dump.md` 同理。

---

## 5.2 必改项 8：补全受影响文件总览

### 问题描述

当前文件总览已经比 V1 好很多，但仍建议显式加入以下文件：

- `core/default-config.yaml`
- `phases/p6-verification.md`
- `templates/verification-report.md`
- Eval 相关代码文件

否则实施时很容易误以为“模板和 Phase 5 改完就够了”。

### V2.1 建议

把文件总览改为“主改文件 + 配套改文件”两组。

---

## 5.3 必改项 9：新增最小联调验证步骤

### 问题描述

V2 定义了验收门槛，但缺少一段“方案修订完成后如何快速联调验证”的步骤说明。

### V2.1 建议

新增一节“最小联调验证”：

1. 用一个最小 Android 资源枚举错误案例验证 Contract Checklist
2. 用一个编译失败后可自动修复的案例验证微验证留痕
3. 用一个 3 次失败案例验证 Error Dump
4. 用一个 Limited 平台场景验证内联降级逻辑
5. 用一个 Eval Case 验证新维度是否真正进入评分链路

这样能让方案从“文档完备”更进一步提升到“实施前可验证”。

---

## 6. 按文件的 V2.1 必改清单

以下给出按文件组织的修订清单，便于直接修改方案文档。

## 6.1 方案主文档

### 必改

1. 全文统一 `invoke-subagent` 为属性式 `subagent_prompt` 写法
2. 为新增产物补充配置键来源与变量命名说明
3. 扩展 Eval 改造范围，列出涉及代码文件
4. 定义 SubAgent 返回判定协议
5. 修正“幻觉识别率”指标定义
6. 明确 P6 验证结论如何消费 Checklist 结果

### 建议

7. 增加变量映射表
8. 增加最小联调验证步骤

## 6.2 `core/default-config.yaml`

### 必改

1. 新增 `output_contract_checklist`
2. 新增 `output_error_dump`

## 6.3 `phases/p5-fix-impl.md`

### 必改

1. 统一使用属性式 `invoke-subagent`
2. 明确 Step 6 的返回判定规则
3. 明确何时写入 `output_contract_checklist`
4. 明确何时写入 `output_error_dump`

## 6.4 `phases/p6-verification.md`

### 必改

1. 增加 checklist 消费逻辑后，对 L1 结果的影响规则
2. 要求将交叉验证结果写入 `verification-report.md`

## 6.5 `templates/verification-report.md`

### 必改

1. 增加“契约溯源交叉验证结果”节
2. 增加 `PASS / WARNING / FAIL` 记录结构

## 6.6 Eval 相关文件

### 必改

1. `scoring-rubric-base.yaml`
2. `scoring_engine.py`
3. `judge.py`
4. `report_generator.py`
5. `comparator.py`
6. `weakness_detector.py`

### 备注

V2.1 中必须明确：  
“新增评分维度不是纯配置修改，而是评测代码联动改造。”

---

## 7. 修复顺序建议

建议按以下顺序修订 V2.1：

### 第一轮：先消除阻断

1. 统一 `invoke-subagent` 写法
2. 补 `default-config.yaml` 与新增产物路径变量
3. 扩展 Eval 改造范围说明

### 第二轮：补齐闭环

4. 定义 SubAgent 返回判定协议
5. 定义 P6 验证结果写入方式
6. 修正评分指标定义

### 第三轮：提高可执行性

7. 增加变量映射表
8. 增加最小联调验证步骤
9. 完善文件总览与配套影响文件

---

## 8. V2.1 验收标准

当且仅当以下条件都满足时，建议认为 V2.1 达到“可开工实施”的文档质量：

1. 文档中不存在两种 `invoke-subagent` 写法
2. 新增产物都有配置层承载与统一变量来源
3. 主 Agent 能明确判定 Coder SubAgent 的返回状态
4. P6 消费 Contract Checklist 的结果会进入 `verification-report.md`
5. 评分维度定义不会惩罚首轮正确行为
6. Eval 改造范围明确覆盖配置与代码
7. 文件总览覆盖所有真正受影响文件
8. 文档提供最小联调验证路径

---

## 9. 最终建议

V2 已经不再是“方向性草案”，而是接近落地实施说明的版本。  
但要真正成为一份可以直接驱动工程改造的方案，还需要完成 V2.1 级别修订。

本次复审的最终建议是：

> **不要直接基于 V2 开始改代码。先完成本清单中的 V2.1 必改项，再进入实施阶段。**

原因不是 V2 方向错，而是：

- 它已经足够接近实施
- 所以剩下的问题都不再是“大方向问题”
- 而是会直接在实施当天触发返工的“最后一公里问题”

把这些问题在文档阶段解决，成本最低，收益最高。

