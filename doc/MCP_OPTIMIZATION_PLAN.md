# Mobile QA Workflow: MCP 工具误调问题分析与优化施工方案

## 1. 背景与问题现象

在执行 `mobile-qa-workflow` 工作流的初始化阶段时，大模型（Agent）出现了一次意外的外部工具调用。具体表现为：
工作流引擎在解析形如 `<load target="mobile-qa-workflow/core/core-rules.xml" prompt="..."/>` 的 XML 指令时，**错误地将本地文件加载请求路由到了 `mcp_capcode-mcp_get_prompt` MCP 工具**。
随后该工具报错（缺少环境变量），Agent 通过内部回退机制改用标准的 `Read` 工具才使流程得以继续。

## 2. 根本原因分析（Root Cause Analysis）

这是一次典型的由**“工具名称/描述语义吸附（Semantic Adhesion）”**引发的 Agent 路由越权。

### 2.1 语义高度重合
- **工作流 DSL 定义**：当前工作流中用于加载子流程或模板的标签被定义为 `<load target="...">`。
- **MCP 工具描述**：环境中可用的 `mcp_capcode-mcp_get_prompt` 工具，其描述恰好为“CapCode 加载流程文件，根据 key 获取 prompt 内容”，且参数名也是 `key`。
- **Agent 决策逻辑**：Agent 在执行时，发现工作流指令的动作（load）、意图（加载流程文件）以及参数名称（key）与该 MCP 工具完美契合，因此做出了“自作聪明”的优化，优先调用了该工具。

### 2.2 全局约束的缺失
在工作流的核心规范文件 `core-rules.xml` 中，针对 `<load>` 标签的定义仅说明了其功能，**未对 Agent 使用何种工具（Tool Routing Guardrails）进行显式约束**，导致 Agent 在可用工具池中自由发散。

## 3. 架构优化考量（Trade-offs）

在制定优化方案时，面临以下架构权衡：

### 3.1 方案 A：全局一刀切（Global Blacklist）
- **做法**：在全局 `core-rules.xml` 的顶层添加 `<mandate>严禁使用任何 MCP 工具</mandate>`。
- **缺点**：致命的扩展性缺陷。二期方案需要接入飞书文档解析、APM 崩溃日志查询等 MCP 工具，全局封杀会导致二期方案无法落地。

### 3.2 方案 B：强语义隔离（Semantic Isolation）
- **做法**：设计两套甚至多套标签，如本地加载用 `<read-local file="...">`，外部加载用 `<fetch-remote url="...">`。
- **缺点**：
  1. **开发成本激增**：开发者必须在不同的业务场景中反复抉择和切换标签。
  2. **历史包袱重**：需要对所有存量工作流脚本进行全局替换。
  3. **心智负担重**：随着接入数据源的增加，标签字典会无限膨胀，既增加大模型的理解难度（Token 消耗与注意力分散），也容易引发大模型的“幻觉”（如将 A 标签的参数错配给 B 标签）。

### 3.3 最终选型：极简 DSL + 属性去魅 + 局部防呆路由
这是兼顾一期稳定性与二期扩展性的最佳实践：
- **属性去魅**：切断大模型向特定 MCP（如 `mcp_get_prompt`）联想的语法抓手。
- **极简 DSL**：维持单一的 `<load>` 标签，屏蔽底层数据源差异。
- **局部防呆（Guardrails）**：在标签说明中，明确教导大模型如何根据目标路径的特征（本地相对路径 vs 绝对 URL）**自主且正确地路由**到对应的工具（本地 Read 工具或外部 MCP）。

---

## 4. 施工方案（Implementation Plan）

### 4.1 核心规范定义修改（`core-rules.xml`）

修改 [core-rules.xml](file:///Users/bytedance/Code/vega/.trae/skills/mobile-qa-workflow/core/core-rules.xml#L61-L67) 中关于 `<load>` 标签的定义，注入工具路由防呆规则：

```xml
<!-- 修改前 -->
<tag name="load">
    <rule>加载并执行指定文件的内容，严格遵循其描述执行</rule>
    <params>
        <param name="key">加载文件的路径</param>
        <param name="prompt">加载意图或传递的参数</param>
    </params>
</tag>

<!-- 修改后 -->
<tag name="load">
    <rule>加载并获取目标内容，严格遵循其描述执行</rule>
    <rules>
        <rule critical="true">【工具路由防呆与白名单】
            1. 本地加载：若 target 包含本地文件后缀（如 .xml, .md, .yaml）或为相对路径/绝对路径，强制且唯一使用本地 [Read] 工具读取文件内容，严禁调用 mcp_get_prompt 等任何外部 MCP 平台工具。
            2. 外部加载：若 target 包含 'http' 或特定系统前缀，才允许使用对应的 MCP/外部网络工具。
                - 飞书文档（如 bytedance.larkoffice.com）：优先使用 mcp_lvcc_get_lark_doc_content 工具。
                - 其他外部链接：使用标准的 WebFetch 等网络工具获取。
            3. 错误恢复：若调用某个工具获取内容失败（如缺少环境变量、协议不支持），必须立即检查是否选错了工具类型（本地错用MCP/外部错用本地），并自动切换工具重试。
        </rule>
    </rules>
    <params>
        <param name="target">要加载的本地相对/绝对路径，或外部系统链接/ID</param>
        <param name="prompt">加载意图或传递的参数</param>
    </params>
</tag>
```

### 4.2 存量工作流脚本的全局替换

需要对 `mobile-qa-workflow` 目录下的所有相关文件执行一次全局的批量替换操作：

**目标目录**：当前工作区内的 `mobile-qa-workflow` 目录（例如 `./mobile-qa-workflow/` 及其子目录 `core/`, `phases/`, `agents/` 等）。*注意：实际执行脚本时，请获取当前真实的根路径，避免硬编码报错。*

**替换规则**：
使用正则表达式匹配以防误伤其他无关的 XML 标签：将所有的 `<load\s+key="` 替换为 `<load target="`。

同时，必须同步检查并替换以下文件中包裹在子 Agent prompt 字符串内的 `<load>` 标签（如 `invoke-subagent` 节点内透传的模板字符串）。

**受影响的核心文件示例**：
- `core/workflow.xml`
- `core/core-rules.xml` (内部的示例和子Agent调用说明)
- `phases/p1-intake.md`
- `phases/p2-spec-definition.md`
- `phases/p3-root-cause.md`
- ...及其他所有涉及工作流编排的文件。

## 5. 预期收益
1. **彻底阻断一期报错**：通过属性名变更（`key` -> `target`）和局部路由防呆规则，Agent 将严格使用本地 `Read` 工具加载工作流文件，消除 `capcode-mcp` 的误调现象。
2. **完美兼容二期扩展**：在二期引入外部数据时，开发者无需学习新标签，继续使用 `<load target="https://larkoffice...">`，Agent 会凭借“路由防呆”规则，智能匹配并调用对应的飞书 MCP 工具，实现了 DSL 层面的“接口统一”。
3. **极低的开发与认知成本**：无需设计复杂的语义隔离体系，保持了工作流编排语言的优雅和极简。
