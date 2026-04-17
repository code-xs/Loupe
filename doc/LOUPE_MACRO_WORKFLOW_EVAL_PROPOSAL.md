# Loupe Eval 批量评测轻量化方案：宏工作流驱动法 (Macro-Workflow Driver)

本方案旨在解决原《Loupe AI 自检自测系统设计方案》中，构建独立 Headless 执行引擎（Test Runner）开发成本过高、易与 IDE 原生执行环境脱节的风险。

本方案的核心思想是：**放弃在外部复刻 XML 解析与状态机，直接将批量评测逻辑（Test Runner）编写为一个新的 IDE 原生工作流。** 

通过“大模型解析 Case 列表文件 + 循环调度目标工作流”的方式，实现零代码开发的自动化串行评测。

---

## 一、 核心设计思路

利用 IDE 现有的 `<task>`、`<step>` 和 `<load>` 等声明式标签指令，构建一个“母工作流” (例如 `eval-batch-runner.xml`)。大模型将充当天然的执行调度器：

1. **状态持久化与任务队列**：维护一个待测 Case 列表文件（如 `eval-cases/pending-list.txt`）。
2. **循环遍历执行**：大模型读取该列表，取出一个 `case_id`，利用现有的 `<load>` 指令，以无交互的静默模式触发目标 `mobile-qa-workflow` 完整跑完 P1-P6。
3. **闭环评分与记录**：单 Case 跑完后，`<load>` Judge Prompt（LLM-as-a-Judge）对产物进行打分，并将结果追加到统计报表（如 `eval-results/summary.csv`）。
4. **状态更新与递归流转**：将跑完的 `case_id` 移入 `done-list.txt`，递归触发自身（`<goto step="1">`）进入下一个 Case。

### 概念演示伪代码

```xml
<!-- eval-batch-runner.xml (概念模型) -->
<task id="batch-eval">
    <step n="1" goal="读取待测 Case 列表">
        <action>读取 eval-cases/pending-list.txt，获取第一个未测试的 case_id</action>
        <check if="列表为空">
            <action>结束测试，输出最终报告</action>
        </check>
    </step>

    <step n="2" goal="执行单 Case 测试">
        <!-- 核心：把待测 Case 塞进正常的 workflow 里跑 -->
        <load target="mobile-qa-workflow/core/workflow.xml" prompt="以 {case_id} 为输入，无交互静默执行到结束"/>
    </step>

    <step n="3" goal="执行打分并记录">
        <load target="eval-framework/judge.md" prompt="对比 {case_id} 的结果与 ground truth"/>
        <action>将得分追加到 eval-results/summary.csv</action>
    </step>

    <step n="4" goal="循环流转">
        <action>将 {case_id} 从 pending-list.txt 移到 done-list.txt</action>
        <goto step="1"/> <!-- 递归调用自己，实现串行批处理 -->
    </step>
</task>
```

---

## 二、 方案优势分析 (Pros)

1. **真正的零开发成本 (Zero Code)**：完全复用现有的 XML 语法体系和 IDE 能力，不需要写任何脱离 IDE 的 Python 调度引擎或状态流转解析器。
2. **100% 真实执行环境 (High Fidelity)**：这种方式跑出来的结果，与真实用户在 IDE 会话中交互执行的效果是完全对应的，不存在“测试环境 vs 生产环境”不一致导致的误差。
3. **天然断点续传 (Resilient)**：通过读写文本文件（`pending-list` / `done-list`）记录状态指针，即使中间大模型卡死或网络中断，下一次重新触发也能从中断点继续，不会丢失进度。

---

## 三、 潜在挑战与应对策略 (Cons & Mitigations)

### 挑战 1：上下文窗口溢出 (Context Window Bloat)
*   **问题描述**：大模型在一个对话 Session 中连续执行几十个 Case，不断读取庞大的 Log、代码和历史中间产物，极易导致对话的 Context 爆满。这会引发严重的幻觉（Hallucination），甚至直接超出 Token 限制报错。
*   **应对策略**：**分批次执行 (Batch Chunking)**。绝对不能在一个对话窗口中一次性跑完 70 个 Case。建议将全量 Case 拆分为若干子集（如 5-10 个为一组），由开发者手动在新的、干净的 IDE 对话窗口中分别触发 `执行组 A`、`执行组 B`，确保每次运行的上下文都是清晰的。

### 挑战 2：大模型的“偷懒”和“跳步”现象 (LLM Laziness & Compression)
*   **问题描述**：在执行长序列循环任务时，LLM 极易出现“压缩执行”行为。例如，它可能在实际只跑了 2 个 Case 后，就直接虚构出一个包含 70 个 Case 结果的总结报告，告诉你“我已经全跑完了，结果都很好”。
*   **应对策略**：**强约束与半自动化卡点 (Strict Mandates & Manual Gates)**。
    1. 在 XML 中加入极其严厉的 `<mandate>` 约束。
    2. 设立人工确认机制：要求大模型在完成一个 Case 的打分并写入记录后，必须停止并输出明确的标识（如 `[Case X Completed]`），强制等待开发者确认（敲回车/回复“继续”）后才能进入下一个循环。用极低的人工干预成本换取执行的绝对可靠性。

### 挑战 3：串行执行耗时极长 (High Sequential Latency)
*   **问题描述**：IDE 环境下的生成是单线程串行的。一个复杂的 Case 跑完 6 个 Phase 并完成打分，可能需要 3-5 分钟。70 个 Case 串行跑完需要长达 4-6 个小时。
*   **应对策略**：**定位为夜间回归 (Nightly Run)**。这种方案更适合作为不需要即时反馈的全量回归测试。开发者在下班前触发批量脚本，保持 IDE 开启运行，第二天早上直接验收汇总的评分报告即可。日常的高频迭代调试，应针对单一或 2-3 个 Case 进行。

---

## 四、 结论

“宏工作流驱动法（文档存储解析 + 串行宏工作流）”是一个极具工程智慧的解法。它巧妙地将“调度逻辑”转嫁给了 LLM 本身，通过文件状态机管理循环进度，并辅以合理的分批策略防止上下文溢出。这是在不投入昂贵外部工具开发成本的前提下，实现高保真批量 Eval 的最优轻量化落地路径。
