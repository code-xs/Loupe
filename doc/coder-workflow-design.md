# Mobile QA 修复工作流与 Coder Agent 技术方案

## 1. 背景与痛点

在当前的 `mobile-qa-workflow` 中，主 Agent 承担了从需求受理（Intake）、根因分析（RCA）到修复实施（Fix Impl）的全链路任务。然而，在真实的移动端工程修复场景中，我们观察到以下致命痛点：

1. **上下文灾难与“经验主义幻觉”**：
   - 主 Agent 在经历了漫长的推理和上下文收集后，记忆负担极重。在生成代码时，极易产生“跳步推理”和“概率拼凑”。
   - **典型案例**：将 Kotlin 源码中的枚举常量名 `AI_FEATURE` 直接推测为 XML 的属性值 `ai_feature`，而未去检索 `attrs.xml` 中的真实定义（`aigc`），导致低级的 AAPT 编译报错。
2. **缺乏隔离的微验证闭环**：
   - 主 Agent 直接修改代码并尝试编译。一旦报错，大量的错误栈 Log 会瞬间淹没主 Agent 的上下文，导致其遗忘修复初衷或产生更严重的幻觉。
3. **防御性编程与契约对齐的执行力不足**：
   - 虽然 `p4-fix-design.md` 提出了“四重形式化论证”，但在实施阶段，缺乏一种机制来**强制**校验 API 签名、资源 ID 和 XML 枚举的合法性。

---

## 2. 方案目标

本方案旨在设计一套**标准化、流程化的修复范式**，通过引入专职的 **Coder SubAgent**，将修复实施阶段（Phase 5）彻底黑盒化与下沉。
**核心目标**：
- **消灭低级幻觉**：用“强制查字典（溯源）”代替“想当然的猜测”。
- **解压主 Agent**：将编译报错的噪音隔离在 SubAgent 沙盒内。
- **提升一次修复通过率**：建立“溯源 -> 编码 -> 本地编译验证 -> 内部纠错”的自治闭环。

---

## 3. 核心架构设计

### 3.1 角色定义：Coder Agent（极端严谨的代码实施专员）

- **人设**：你是一个极度严谨、没有任何主观臆测的“编译器思维”执行者。
- **核心信念**：不相信任何凭空出现的变量名、资源 ID 或 XML 属性值。所有使用的 API 契约必须在代码库中有明确的声明（Declaration）支撑。
- **输入**：`fix-design.md` (修复方案，**必须包含具体修改文件的绝对路径，严禁让 Coder Agent 猜测修改目标**) 和 `spec.md` (预期行为)。
- **输出**：编译/静态检查通过的代码变更，并生成 `impl-report.md`。
- **关键工具权限**：`SearchCodebase`, `Grep`, `Read`, `Write`, `SearchReplace`, `RunCommand`。

### 3.2 修复实施工作流 (Coder Workflow) 的四个标准化阶段

Coder Agent 被唤起后，必须严格按以下四个阶段执行，形成闭环：

#### 阶段 1：契约溯源与防幻觉走查 (Pre-compile Contract Walkthrough)
**在写下任何一行代码之前，必须完成契约验证。**
- **动作约束**：
  1. **跨模块依赖与 API 签名**：若调用了其他类、组件或模块的新 API，强制使用 `SearchCodebase`/`Grep` 检索目标类的定义（Declaration），确认方法签名（参数数量、类型、可空性、返回值）及访问权限（Public/Internal）。
  2. **配置文件与资源契约**：若修改涉及 UI 布局、多语言字符串、图片资源或路由配置，强制检索其对应的定义源（如 Android 的 `declare-styleable`/`strings.xml`，iOS 的 `.xcassets`/`Localizable.strings`，Web 的 `package.json`/`tsconfig` 等），确认使用的键名、枚举值和路径绝对匹配。
  3. **数据结构与序列化模型**：若修改涉及网络请求或本地存储的数据结构，强制确认 JSON 字段名与代码中的实体模型属性名（如 `@SerializedName`/`@JsonProperty`）保持一致。
  4. **同名冲突消歧义**：当检索到多个同名定义（如多个模块均包含 `strings.xml` 或 `Utils.kt`）时，必须结合 `fix-design.md` 中的模块路径上下文进行交叉比对，绝不盲目使用第一个搜索结果。
- **产出**：内部生成一份 `Contract-Checklist`，全部打钩后方可进入编码阶段。

#### 阶段 2：精确编码实施 (Precise Coding)
- **动作约束**：
  - 严格遵循 `fix-design.md` 的“最小修改原则”，绝不夹带私货（搭便车修改）。
  - 使用 `SearchReplace` 进行精准的局部替换，避免使用 `Write` 覆写全文件导致意外丢失代码。
  - 落实防御性编程要求（如添加 null 检查、状态断言），并在注释中标注 `[DEFENSIVE-FIX]`。

#### 阶段 3：微验证与自我纠错沙盒 (Micro-Verification & Self-Healing Loop)
**这是本方案提升修复质量的核心杀手锏。**
- **动作约束**：
  - 触发本地的静态检查。**首选使用 IDE/LSP 级别的快速诊断（如 GetDiagnostics）**获取秒级反馈；仅在涉及跨模块资源链接等 LSP 无法完全覆盖的场景时，才回退到轻量级编译命令（如 `./gradlew processDebugResources` 或 `xcodebuild`）。
  - **若发生报错**：
    1. **解析错误栈**：提取报错文件、行号和具体的错误原因（如 "is incompatible with attribute..."）。
    2. **状态回滚（重要防线）**：如果代码已被修改得面目全非或引发了级联错误，在进行下一次尝试前，**必须撤销上次的错误修改（通过文件还原或 git checkout）**，确保基于干净的基线进行重试。
    3. **强制溯源**：带上报错信息，**重新使用 `SearchCodebase` 去寻找正确的定义**。
    4. **应用修复**：执行 `SearchReplace` 纠正错误。
    5. **重新验证**：再次触发检查命令。
  - **防死循环机制**：此纠错循环最多执行 **3 次**。若 3 次仍失败，生成带报错现场的 `Error-Dump` 抛出 `Human-Review`。

#### 阶段 4：产出与移交 (Output & Handoff)
- **动作约束**：
  - 确认代码修改无误（或完成自我纠错）后，生成标准化的 `impl-report.md`。
  - 报告中必须详细记录：变更的文件、行数、**遇到的编译报错及自我修复过程**（例如：“修正了枚举值幻觉：`ai_feature` -> `aigc`”）。
  - 通知主 Agent 接管，进入 Phase 6 (Verification)。

---

## 4. 工作流集成方案 (对 `mobile-qa-workflow` 的改造)

### 4.1 主流程 `workflow.xml` 的改造
在主工作流的 Phase 5 (`qa-fix-impl`) 节点，将原来的“主 Agent 直接改代码”逻辑替换为黑盒化的 `<invoke-subagent>` 调用：

```xml
<case if="qa-fix-impl">
    <!-- 主 Agent 仅作为路由网关下发任务 -->
    <invoke-subagent subagent_type="coder-agent" subagent_prompt="
        [角色定义] 你是一个极度严谨的代码实施专员（Coder Agent）。
        [核心原则] 凡事溯源，拒绝推测。
        
        请严格按以下四阶段执行修复实施：
        1. 契约溯源：在编码前，使用 Search/Grep 检索 fix-design 中涉及的所有 XML 自定义属性（查 attrs.xml）、方法签名和资源 ID，确保它们真实存在且拼写/枚举值绝对正确。
        2. 精确编码：依据 fix-design 使用 SearchReplace 修改代码，保持最小变更。
        3. 验证与纠错：优先运行 LSP 静态检查或轻量编译。若报错，请自行解析错误栈，**若需要大幅修改，先撤销上次的错误修改**，然后重新检索正确定义并修复（最多重试 3 次）。
        4. 报告输出：完成后将变更清单和纠错记录写入 {output_impl_report}。
        
        [输入文档]
        - fix-design: {fix-design}
        - spec: {spec_file}
    "/>
    
    <!-- 主 Agent 挂起等待，收到结果后更新状态机 -->
    <action>读取 {output_impl_report}，更新 workflow_status，进入 Verifying 阶段。</action>
</case>
```

### 4.2 `platform-checklist.md` 的增强约束
在现有的平台检查清单中，补充针对大模型幻觉的通用硬性约束：
> **[新增规则] 跨层契约与资源引用溯源约束**：
> 1. **严禁臆测机制映射**：绝不能基于上层业务代码的变量名/常量名，直接推测底层或跨层配置文件（如 XML、JSON、YAML、Plist）中的键名或枚举值。
> 2. **强制定义溯源**：任何跨越语言或框架边界的引用（如 Kotlin/Java 调用 XML 属性、Swift 访问 XIB 标识、TS 读取配置树），必须使用检索工具查阅该标识在源文件中的**精确定义 (Declaration)**，并确保拼写与大小写严格 1:1 匹配。

---

## 5. 方案收益预期

1. **根除低级幻觉报错**：通过“编码前强制查字典（契约溯源）”，从根本上消灭因大模型概率猜测导致的拼写错误和枚举不匹配。
2. **保护主 Agent 上下文**：复杂的编译报错 Log 和多次试错的代码修改全被隔离在 `coder-agent` 的沙盒中。主 Agent 始终保持清醒的头脑，专注于高层架构的把控。
3. **真正的一次性高质量交付**：内部的“微验证纠错循环”赋予了 AI 自我进化的能力，最终交付给用户的将是经过编译器检验的“Ready to PR”级别的代码，避免用户被迫参与多轮人肉 Debug。