# ADR-018: `parse_error_count` 持久化 + 4 类生命周期动作

> **状态**：active
> **关联决定**：D18（v2.2 review 第 P0-2 项）
> **关联 PR**：v4.1 PR-1 + PR-2（已合入）

## 1. 背景

`parse_error_count` 被 PR-2 设计成"连续 3 次解析失败后转 Human-Review"的跨回合计数器，但既未入 schema、也未定义为运行时变量，3 次熔断协议悬空。

## 2. 决定

**走持久化字段路线**：
1. **PR-1**：`core/workflow-status-template.yaml` 显式新增 `parse_error_count: 0`，迁移脚本补齐默认值
2. **PR-2**：明确 4 类生命周期动作（CI `Check 8 — D18 parse-error 4 类生命周期动作闭合` 守门）：
   - **a. 解析失败 +1**：`parse_error_count += 1`
   - **b. 解析成功清零**：`parse_error_count = 0`（D18 解析成功）
   - **c. 进入新 step-pause 前清零**：`parse_error_count = 0`（D18 进入新）
   - **d. 熔断后清零**：`parse_error_count = 0`（D18 熔断；同步切换 `current_state = Human-Review`）
3. **熔断阈值**：`parse_error_count >= 3` 触发 Human-Review

## 3. 替代方案

- **方案 X**（运行时变量，单轮内有效）：被拒绝。理由：连续 3 次跨回合计数语义需要持久化。
- **方案 Y**（无熔断 / 无限重试）：被拒绝。理由：用户输入不可控时会陷入死循环。

## 4. 影响

- **协议层**：`core/workflow-status-template.yaml` 新增字段
- **编排器**：`core/workflow.xml` step 4 内 4 类生命周期动作分散落地
- **CI**：`Check 8` 4 类动作闭合校验（已落地，error 级）
- **跨平台**：所有平台等价（持久化字段在所有 platform 下读写一致）

## 5. 引用

- v2.2 主文档 §6 D18 拍板纪要
- ADR-002（input-protocol 解析协议 / parse-error 触发点）
- ADR-016（step-pause 必填参数表 / allowed_values 是 parse 校验输入）
