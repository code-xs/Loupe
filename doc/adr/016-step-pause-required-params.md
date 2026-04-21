# ADR-016: `<step-pause>` 必填参数表

> **状态**：active
> **关联决定**：D16（v2.1 review 拍板）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

`allowed_values` 已被 PR-3 示例 / DoD / CI 当作 `<step-pause>` 属性使用，但 PR-1 仅显式新增 `result_field`，DSL 参数定义未闭合。需要一次性把参数表完整定义。

## 2. 决定

`<step-pause>` 参数表（DSL schema）：

| 参数 | 是否必填 | 取值 | 用途 |
|---|---|---|---|
| `title` | **必填** | string | LLM 输出给用户的提示标题 |
| `result_field` | **必填** | snake_case 标识符 | 用户回复的存储 key（写入 `user_inputs.<key>` + 可选顶层镜像） |
| `allowed_values` | **必填** | `\|` 分隔的字面值集合（如 `1\|2\|S`） | 解析 LLM 必须把回复 normalize 到该集合内 |
| `option` | 可选 0..* | `<option value="..." label="..." />` | 给 LLM / 用户的选项展开（不影响 result_field 的 allowed_values 校验） |

## 3. 替代方案

- **方案 X**（仅 `title` + `result_field` 必填）：被拒绝。理由：parse-error 时无可校验白名单（详见 ADR-018）。
- **方案 Y**（用 JSON Schema 单独描述）：被推迟到 ADR-010 (PR-5 step-pause-registry) 落地后评估。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 标签 `<supported-tags>` 注释明确 4 个参数
- **CI**：`Check 1 — D16 step-pause 完整参数 (title/result_field/allowed_values)`（已落地，error 级）
- **LLM 解析**：parse-error 时回显 `allowed_values` 白名单（详见 ADR-018 + ADR-002）

## 5. 引用

- v2.2 主文档 §6 D16 拍板纪要
- ADR-002（input-protocol 子标签）
- ADR-010（step-pause-registry 草稿）
- ADR-018（parse-error 4 类生命周期）
