# Coder SubAgent 技术方案 V3 质检报告

> 报告日期：2026-04-17  
> 审核对象：飞书文档《Coder SubAgent 技术方案 V3》  
> 审核方式：静态方案审阅，不修改任何代码  
> 结论用途：用于判断 V3 是否达到“可直接实施”标准

---

## 1. 执行摘要

本次质检基于最新版本《Coder SubAgent 技术方案 V3》，结合当前仓库中实际存在的工作流 DSL、配置文件、Phase 5/Phase 6 链路和 Eval 框架进行对照审查。

相较前一版本，V3 已经显著完善，关键改进包括：

- 统一了 DSL 写法方向
- 补入了新增产物的配置承载思路
- 明确了 SubAgent 返回判定协议
- 补充了 P6 对 Contract Checklist 的消费逻辑
- 修正了评分指标定义
- 扩展了 Eval 联动改造范围
- 增加了变量命名规范和最小联调验证路径

综合判断如下：

1. **V3 已经非常接近可实施版本。**
2. **当前不再存在方向性错误。**
3. **但仍残留 1 个阻断项和 2 个中风险不一致点。**
4. **在当前状态下，不建议立即开工改代码。**
5. **将剩余 3 个问题补齐后，大概率可进入“通过终审、允许实施”的状态。**

本次审查结论可以概括为：

> V3 方向正确、结构完整、质量明显提升，但仍需修正少量“最后一公里”的实现兼容性问题，当前建议结论为“接近通过，但暂不建议直接实施”。

---

## 2. 审核范围

本次审阅覆盖以下对象：

- 飞书方案《Coder SubAgent 技术方案 V3》
- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/phases/p5-fix-impl.md`
- `mobile-qa-workflow/phases/p6-verification.md`
- `mobile-qa-workflow/templates/verification-report.md`
- `eval-framework/scoring_engine.py`
- `eval-framework/judge.py`
- `eval-framework/artifact-checklist.yaml`
- `eval-framework/artifact_checker.py`

---

## 3. 审核方法

本次质检采用“方案文档 vs 仓库真实实现约束”的对照审查方式，重点核查以下内容：

1. 方案是否与当前 DSL 语义兼容
2. 新增产物是否具备配置层承载
3. 主 Agent 与 Coder SubAgent 的协作协议是否自洽
4. P5 与 P6 的 I/O 契约是否一致
5. Eval 评分链路与产物完整性链路是否一起覆盖
6. 方案是否仍存在实施当天会触发返工的隐性问题

---

## 4. V3 相比前版的改进确认

V3 已经修复了此前大部分关键问题，这一点需要明确肯定。

### 4.1 已确认修复的点

1. **DSL 写法问题已大幅收敛**
   方案已明确向属性式 `invoke-subagent` 收口，不再延续早期双写法混用的问题。

2. **新增产物已有配置承载意识**
   方案已纳入：
   - `output_contract_checklist`
   - `output_error_dump`

3. **SubAgent 返回判定协议已显式定义**
   已从“隐式推断”升级为“文件哨兵法”。

4. **P6 已开始消费 Contract Checklist**
   方案已定义交叉验证逻辑，并将异常等级与 L1 结果关联。

5. **评分指标定义已修正**
   方案已不再简单使用“`❌ -> ✅` 条数”来代表幻觉识别能力。

6. **Eval 改造范围已扩展**
   已明确涉及：
   - `scoring-rubric-base.yaml`
   - `scoring_engine.py`
   - `judge.py`
   - `report_generator.py`
   - `comparator.py`
   - `weakness_detector.py`

从方案成熟度视角看，这一轮修订质量是明显进步的。

---

## 5. 当前剩余问题总览

本次复审确认，V3 仍残留以下问题：

### P0 阻断项

1. 输出路径变量的引用时序仍不自洽

### P1/P2 之外的中风险项

2. Phase I/O 契约与 Success 判定协议仍存在不一致
3. Eval 改造虽覆盖评分链路，但仍遗漏产物完整性硬门禁链路

---

## 6. 详细问题分析

## 6.1 P0 阻断项：输出路径变量时序不自洽

### 问题描述

V3 方案在 P5 的返回判定逻辑中，要求主 Agent 按以下顺序检查文件哨兵：

1. 若 `{output_error_dump}` 存在，则进入 `Human-Review`
2. 若 `{output_impl_report}` 和 `{output_contract_checklist}` 均存在，且 `{output_error_dump}` 不存在，则视为 `Success`

但同一段流程中，`output_contract_checklist` 和 `output_error_dump` 又是在后一步才写回 `config_source`。

也就是说，当前文档语义表现为：

- 先用变量判定文件是否存在
- 再把这些变量的路径写入配置

### 为什么这是问题

当前真实仓库中的 `default-config.yaml` 只对既有产物提供固定配置承载。  
即便 V3 已提出新增配置键，如果在运行时没有先初始化这些输出路径，主 Agent 在进入判定时实际上拿到的仍可能是：

- `null`
- 空值
- 未定义运行时变量

这会导致“文件哨兵法”在真正执行时缺少可判定的有效路径来源。

### 风险

这是实施阻断项，原因包括：

- 主 Agent 无法稳定判定 Coder SubAgent 成败
- 判定逻辑可能在运行时退化为“对空路径做文件检查”
- 文档虽定义了协议，但协议执行前提没有成立

### 质检结论

- 风险级别：**P0**
- 当前是否阻断实施：**是**

### 修订建议

V3 应补充以下任一条，且必须写清：

#### 方案 A：P5 进入前初始化固定输出路径

在 P5 启动时，由主 Agent 先写入：

- `output_impl_report = {workspace_folder}/impl-report.md`
- `output_contract_checklist = {workspace_folder}/contract-checklist.md`
- `output_error_dump = {workspace_folder}/error-dump.md`

然后 SubAgent 只负责写文件，不再负责定义这些路径。

#### 方案 B：判定逻辑直接使用固定文件路径

不要先读 `{output_contract_checklist}`，而是直接检查：

- `{workspace_folder}/contract-checklist.md`
- `{workspace_folder}/error-dump.md`
- `{workspace_folder}/impl-report.md`

判定完成后，再同步回 `config_source`。

### 推荐做法

推荐使用 **方案 A**，因为它与当前工作流“配置文件承载路径”的设计风格更一致。

---

## 6.2 中风险项：Phase 契约与 Success 协议不一致

### 问题描述

V3 中的 Success 判定已经明确要求：

- `impl-report.md`
- `contract-checklist.md`

两者同时存在，且 `error-dump.md` 不存在，才算成功。

但在 Phase 5 / Phase 6 的 I/O 契约描述中，`contract-checklist.md` 仍被标记为“可选产物/可选输入”。

### 为什么这是问题

如果契约层写成“可选”，而成功协议层写成“必需”，就会出现三套不同理解：

1. 编排器视角：可以没有 checklist
2. 实施视角：没有 checklist 不算成功
3. 评测视角：可能无法判断缺 checklist 是否应失败

这种不一致会在以下环节造成口径分裂：

- 主流程状态流转
- 产物完整性校验
- Eval 结果解释
- 方案验收标准

### 风险

这不是纯文案问题，而是协议层不一致。

### 质检结论

- 风险级别：**中**
- 当前是否阻断实施：**接近阻断，但可通过文档修订快速消除**

### 修订建议

建议二选一：

#### 方案 A：将 `contract-checklist.md` 改为条件必需

在契约中写明：

- 对“代码修复”路径：`contract-checklist.md` 为必需
- 对“远端漂移/协调修复/纯非代码修复”路径：可选或不要求

#### 方案 B：保持全局可选，但下调 Success 条件

即：

- Success 只要求 `impl-report.md`
- checklist 只作为增强产物

### 推荐做法

推荐 **方案 A**。  
因为若保留全局可选，飞书方案最核心的“编码前契约溯源”价值会被削弱。

---

## 6.3 中风险项：Eval 仍遗漏产物完整性硬门禁链路

### 问题描述

V3 已经把评分相关文件列得较完整，说明方案已经意识到：

> Eval 不是纯 YAML 配置驱动，而是配置 + 代码 + Prompt 联动。

这一点是对的。

但当前仓库里除了评分链路外，还有一条**独立且更硬的产物完整性校验链路**：

- `eval-framework/artifact-checklist.yaml`
- `eval-framework/artifact_checker.py`

这条链路会直接决定：

- 哪些文件是标准必需产物
- 文件最小尺寸要求
- 缺失产物时是否需要重试
- 是否标记失败

当前这条链路仍主要面向旧产物：

- `impl-report.md`
- `verification-report.md`

尚未把：

- `contract-checklist.md`
- `error-dump.md`

明确纳入新的标准产物/条件产物规则中。

### 为什么这是问题

如果评分系统能看见新维度，但产物完整性门禁看不见新产物，会出现：

1. 评分层认为 checklist 很重要
2. 产物完整性层却不要求 checklist 存在
3. 最终 Eval 可能在缺少 checklist 的情况下仍给出“产物完整性通过”

这会直接削弱方案落地后的制度约束力。

### 风险

属于验收口径不闭环问题，会在联调和评测阶段暴露。

### 质检结论

- 风险级别：**中**
- 当前是否阻断实施：**不完全阻断，但会导致验收口径失真**

### 修订建议

在 V3 文档的 Eval 改造范围中，补充以下文件：

- `eval-framework/artifact-checklist.yaml`
- `eval-framework/artifact_checker.py`

并明确：

1. `contract-checklist.md` 在代码修复路径下属于条件必需产物
2. `error-dump.md` 在 Human-Review 失败分支下属于条件必需产物
3. `artifact_checker.py` 需要支持按路径类型进行条件校验

---

## 7. 本次质检的通过项

尽管仍有问题，V3 已有大量内容达到较高质量，以下项可视为“已通过”：

### 7.1 方案方向通过

- 问题定位准确
- 架构方向合理
- 与当前主工作流兼容性高

### 7.2 Coder SubAgent 核心结构通过

- 契约溯源
- 精确编码
- 微验证纠错
- 产出移交

这四段式闭环已具备实施价值。

### 7.3 SubAgent 返回协议基本通过

尽管仍有路径时序问题，但“文件哨兵法”本身是合理的。

### 7.4 P6 消费链路基本通过

V3 已经不再停留于“P5 生成 checklist，P6 不消费”的状态，说明方案闭环性明显增强。

### 7.5 指标体系方向通过

本轮指标定义已明显优于早期版本，不再把“犯错后修正”错误地等同于“识别能力”。

### 7.6 Eval 改造思路通过

V3 已经认识到必须联动：

- 配置
- 代码
- Prompt

这说明方案已经从“想当然的文档设计”向“可真正实施的工程方案”靠拢。

---

## 8. 风险分级结论

| 问题 | 风险级别 | 是否阻断实施 | 结论 |
|------|----------|--------------|------|
| 输出路径变量时序不自洽 | P0 | 是 | 必须先修 |
| Phase 契约与 Success 协议不一致 | 中 | 接近阻断 | 建议立即修 |
| Eval 遗漏产物完整性硬门禁链路 | 中 | 否 | 建议纳入 V3.1 修订 |

---

## 9. 最终质检结论

### 9.1 当前结论

本次对 V3 的最终结论为：

> **不建议直接开始实施，但已经接近通过终审。**

这不是因为 V3 还有方向性缺陷，而是因为仍存在：

- 1 个会在流程运行时直接导致协议失效的阻断项
- 2 个会在实现和验收阶段造成口径分裂的中风险项

### 9.2 推荐结论文案

建议在评审场景中使用以下表述：

“V3 已经显著优于 V2，核心方案结构、P6 闭环、指标定义和 Eval 适配思路均达到较高质量，方向上可以视为通过。但当前文档仍保留一个输出路径变量时序阻断项，以及两个协议/评测口径不完全一致的问题。建议先完成一轮小幅修订后再开工实施。”

### 9.3 是否建议开工

- 当前是否建议开工：**否**
- 修复剩余问题后是否大概率可开工：**是**

---

## 10. 建议的下一步动作

建议按照以下顺序完成最终收口：

1. 先修正输出路径变量初始化时序
2. 再统一 Phase 契约与 Success 协议
3. 最后补齐 Eval 的产物完整性硬门禁链路

完成上述三项后，建议再做一次“终审版 Review”。  
按当前质量趋势判断，届时大概率可以给出“允许实施”的结论。

---

## 11. 最终一句话结论

> V3 已经从“方案设计”走到了“几乎可实施”的阶段，但还差最后 3 个一致性问题收口；当前结论是“接近通过，暂缓开工”。  

