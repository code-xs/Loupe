# 专家级评估报告：Loupe AI 自检自测系统设计方案

**评估人**: 移动端质量专家（10年+ AI自动化测试与质检经验）
**评估对象**: [Loupe AI 自检自测系统设计方案](https://bytedance.larkoffice.com/docx/T1xYdURy3oY85vxkmAsczRL5nwh)
**结合工程**: 当前目录下的 `mobile-qa-workflow` 项目结构及编排逻辑

---

## 一、 总体评价 (Executive Summary)

整体而言，这是一份**具备极高专业成熟度与业界前瞻性的 AI Agent 评测架构方案**。方案敏锐地捕捉到了当前 Prompt 工程和多 Agent 工作流的核心痛点：**难以进行传统单元测试、回归验证成本高、缺乏客观量化的 Benchmark**。

通过引入四链路横向对比、LLM-as-a-Judge 细粒度评分，以及自动化的“低分归因 -> Prompt 改进 -> 回归验证”闭环（Optimizer），该方案从根本上解决了 AI 分析工作流“效果不可证”和“迭代靠感觉”的难题。架构设计上完全做到了**非侵入式外挂**，与当前 `mobile-qa-workflow` (P1-P6 主工作流及 F1-F5 专家模式) 的核心文件完全解耦，落地可行性极高。

**最终结论：强烈推荐推进落地（Go）。但在具体的执行引擎（Test Runner）和案例库（Case Bank）建设上，存在显著的工程实现风险，需要在第一阶段进行技术验证（POC）。**

---

## 二、 架构与设计亮点 (Strengths & Highlights)

1. **科学的横向评测基准 (Benchmarking System)**
   - **设计**: 同一个 Case 并行跑 Loupe 主流程、专家模式、外部 B2C（如 Cursor/Devin）、LLM 裸跑（Zero-shot）。
   - **价值**: 这一设计直击痛点。LLM 裸跑作为“下界”，能有效证明多 Agent 复杂编排的**工程增量价值**，避免“伪工程”（即花了大力气编排，效果还不如直接问 Claude/GPT-4o）。
2. **多维与细粒度评分体系 (Granular & Stage-Level Scoring)**
   - **设计**: 不仅有端到端的综合评分（归因准确率 35%、修复方向 20% 等权重极具业务合理性），还支持拆解到 F1-F5 的独立评分。
   - **价值**: 使得“低分归因”成为可能。当系统表现下降时，不再是盲目调整主 Prompt，而是精准定位到比如“F3 时序竞态分析”阶段的缺陷。
3. **安全可控的自动迭代闭环 (Auto-Optimizer with Guardrails)**
   - **设计**: Optimizer 结合低分归因 Agent 自动修改 Prompt/Reference，并强制要求全量回归，满足净提升 ≥ 0.5 且无劣化（Regression）才合并。
   - **价值**: 有效防范了 Prompt 工程中极易出现的 **“Prompt 漂移”**（修复一个边缘 Case，导致 10 个主流 Case 变差），极大降低了人工调参成本。

---

## 三、 结合当前工程的落地风险分析 (Risks & Feasibility Analysis)

结合当前 `mobile-qa-workflow` 目录结构（大量 `.md` 和 `workflow.xml` 声明式规则），落地过程中存在以下主要风险：

### 1. 执行引擎 (Test Runner) 与 IDE 的解耦风险（🔴 高风险）
- **现状分析**: 当前工程 `mobile-qa-workflow` 的执行高度依赖于底层智能体框架（如基于 Trae / Cursor 提供的运行时机制），通过解析 `workflow.xml` 中的 `<step>`, `<switch>`, `<load>` 标签进行状态流转。
- **潜在风险**: 方案中提出用 Python 编写 `runner.py` 实现“四链并行”。但在脱离 IDE 交互界面的情况下，如何 Headless（无头）地驱动和解析这些自定义 XML 规则并正确调度 LLM API？如果需要重新用 Python 写一套完整的 XML 解析和 Agent 调度引擎，工作量将非常庞大。
- **专家建议**: Phase 1 的首要任务必须是验证 **Test Runner POC**。建议先写一个轻量的 Python 解析器，仅跑通最简单的一个 P1 -> P2 流程，确认脱离 IDE 也能正确闭环。

### 2. 案例库 (Case Bank) 构建的“成本墙”（🟡 中等风险）
- **现状分析**: 方案建议初始规模为 70 个高质量 Case，且要求人工标注 Ground Truth（主根因、贡献因子、修复方向、评分标尺）。
- **潜在风险**: 构建 1 个能完全复现、日志齐全且包含多维 Ground Truth 的移动端复杂 Bug Case，通常需要资深工程师耗费数小时。70 个 Case 的启动成本极高。
- **专家建议**: 开发一个**案例采编脚本 (Case Collector)**。当日常使用 Loupe 解决了一个真实问题后，提供一键命令（如 `bash collect-case.sh <issue-id>`），自动将当前的上下文、对话记录和最终正确的 RCA 报告打包转换为 Case 骨架，再由人工微调 Ground Truth，以此降低冷启动门槛。

### 3. LLM-as-a-Judge 的同源偏见与对齐问题（🟡 中等风险）
- **现状分析**: 方案指出使用更高阶的模型（如 Claude Opus / GPT-4o）作为 Judge。
- **潜在风险**: 如果测试链路（Chain A/B/D）底层也大量依赖同系模型（如 Claude Sonnet），Judge 模型极易出现“自偏好（Self-Preference Bias）”，给同系模型生成的内容打高分，影响横向对比（Chain C 外部方案）的客观性。
- **专家建议**: 引入 **Judge 校验集 (Meta-Eval)**。在前期，必须让人类专家对 Judge 给出前 20 个打分进行盲审，校准 Judge 的 Scoring Prompt。

---

## 四、 架构与实施细节的专业优化建议 (Expert Recommendations)

除了方案本身的完善性，结合行业最佳实践，建议在以下细节进行补充优化：

1. **引入“Prompt 膨胀监控”**: 
   - 自动迭代（Optimizer）虽然会验证准确率，但 LLM 往往倾向于通过“加字”来修复问题。长期迭代会导致 Prompt 越来越长，不仅增加 Token 成本，还会引发 Attention 稀释。
   - **建议**: 在 `artifact_checker.py` 中加入 Prompt 长度监控，当单个阶段 Prompt 超过预设 Token 阈值时，触发“精简重构”报警，人工介入进行逻辑抽象。
2. **测试分级与成本控制**: 
   - 全量并行跑 70 个 Case（每 Case 3 次）单次成本极高。
   - **建议**: 将 Case Bank 分为 `Smoke` (冒烟, 5-10 个) 和 `Full` (全量, 70+ 个)。PR 级别（`.github/workflows/eval.yml`）只跑 Smoke 集以防极度劣化，只有在 Weekly 或 Monthly 发版前才跑 Full 集。
3. **外部竞品（Chain C）对比的自动化演进**: 
   - 虽然目前采用人工录入，但长远看，可以通过 Playwright 等 UI 自动化框架驱动外部 Web 端 Agent 执行标准 Prompt 输入，定期自动获取产出录入 Evaluator，实现完全无人的外部 Benchmark。

---

## 五、 结论与下一步行动 (Next Steps)

整体架构思路极其清晰，是高质量的“AI工程化”范本。结合当前工程结构，建议**立即启动 Phase 1**，但需对原路线图做轻微调整：

- **Week 1 调整为**：完成 **Test Runner 核心驱动机制的 POC 验证**（使用 1 个极简 Case 跑通 `workflow.xml` 的 Headless 执行）。
- 验证通过后，按原计划铺开基础设施搭建。