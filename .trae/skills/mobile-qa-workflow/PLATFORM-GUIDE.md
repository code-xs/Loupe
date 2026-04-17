# Mobile QA Workflow — 平台集成指南

## 概述

本工作流采用 **XML 标签化 DSL**（`<flow>` / `<step>` / `<check>` / `<switch>` / `<goto>` / `<step-pause>`）
进行编排，与 Capilot/CapCode 使用相同的标签语义。

## 入口文件

| 文件 | 用途 |
|------|------|
| `SKILL.md` | **Cursor / CapCode / Windsurf** 等支持 Skill 机制的 IDE Agent 入口 |
| `system-prompt.md` | **Dify / Coze / OpenAI API / 纯 Chat** 等无文件系统访问的平台入口 |
| `core/workflow.xml` | 核心编排逻辑（被 `SKILL.md` 加载，无需直接使用） |
| `phases/p1~p6-*.md` | 各阶段详细逻辑（被 `workflow.xml` 调度，无需直接使用） |
| `agents/*.md` | 子 Agent 定义（被阶段文件通过 `invoke-subagent` 调用） |

## 集成方式

根据平台能力分为两个等级：

| 能力等级 | 平台示例 | 入口文件 | 说明 |
|---------|---------|---------|------|
| **Full**（文件系统 + 子 Agent + Git） | Cursor / CapCode / Windsurf | `SKILL.md` | 通过 Skill 机制注册，运行时加载 `core/`、`phases/`、`agents/` 下的文件 |
| **Limited**（仅 System Prompt） | Dify / Coze / OpenAI API / 纯 Chat | `system-prompt.md` | 全量内联，单文件包含所有逻辑、模板和参考知识 |

---

## Full 能力平台

### Cursor

1. 运行安装脚本，将 Skill 注册到 Cursor：
   ```bash
   bash mobile-qa-workflow/install.sh
   ```
2. 重启 Cursor，在对话中描述质量问题即可触发 `mobile-qa-workflow` Skill
3. Skill 入口 `SKILL.md` 会自动初始化工作区、检测环境能力、调度六阶段工作流

### CapCode / Windsurf

与 Cursor 类似，将 `mobile-qa-workflow/` 目录注册为 Skill：
- CapCode：将目录放入 `~/.capcode/skills/` 或按平台文档配置
- Windsurf：将目录放入 Skill 注册路径，确保 `SKILL.md` 可被发现

### AutoGen / CrewAI

- Orchestrator → 主 Agent，System Prompt 为 `SKILL.md` + `core/workflow.xml` 的内容
- 每个 Phase → 独立 Agent，System Prompt 为对应 `phases/pN-*.md`
- Root Cause 阶段的 Investigator / Challenger / Arbiter → 3 个子 Agent，定义在 `agents/*.md`
- Fix Design 阶段的 Fix-Proposer / Challenger / Arbiter → 类似子 Agent 配置

---

## Limited 能力平台

### Dify

1. 创建 Agent 应用
2. 将 `system-prompt.md` 全文粘贴到 System Prompt
3. 状态管理：使用 Dify 的 **Conversation Variable** 存储 `current_state`、`stepsCompleted`
4. 每轮对话末尾由 AI 输出状态更新摘要，下轮自动附带

### Coze

1. 创建 Bot，在 Persona & Prompt 中粘贴 `system-prompt.md`
2. 利用 **Long Term Memory** 存储状态（`current_state`、`stepsCompleted`、产物摘要）
3. 如有 Plugin 能力，可配置 Lint 工具调用

### OpenAI Assistants API

```python
assistant = client.beta.assistants.create(
    name="Mobile QA Agent",
    instructions=open("system-prompt.md").read(),
    model="gpt-4o",
    tools=[{"type": "code_interpreter"}]
)
```
- 每个 Issue 一个 Thread，状态存在 Thread Metadata
- 利用 Code Interpreter 执行 AST 验证

### LangChain / LangGraph

```python
from langchain_core.prompts import ChatPromptTemplate

system_prompt = open("system-prompt.md").read()
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])
```

若使用 LangGraph，可将阶段序列映射为 Graph 节点，
`core/workflow.xml` 中的状态路由映射为 Edge 条件，复用 `phases/` 下的阶段内容作为节点指令。

### 纯 Chat 平台

1. 直接粘贴 `system-prompt.md` 作为首条消息
2. 每轮对话末尾 AI 输出 `[状态: xxx | 已完成: xxx]` 便于人工追踪
3. 产物通过 Markdown 代码块内嵌在回复中
