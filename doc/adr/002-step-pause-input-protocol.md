# ADR-002: `<step-pause>` 必备 `<input-protocol>` 子标签

> **状态**：active
> **关联决定**：D2（v1.0 review 拍板）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

`<step-pause>` 等待用户输入后由 LLM 解析回复并写入对应字段。早期实现把"如何解析回复"散落在各处提示词中，导致解析行为漂移、parse-error 处理不一致。需要在 DSL 层面统一协议。

## 2. 决定

`<step-pause>` 必备 `<input-protocol>` 子标签，规定：
- LLM 解析提示模板：`请用 <key>=<value> 回复`（中文 / 英文等价均允许）
- 解析失败时的 fallback：回显允许值白名单 + 计数 `parse_error_count += 1`（详见 ADR-018）
- 解析成功后：写入 `user_inputs.<key>` + 顶层镜像（详见 ADR-008 / ADR-015）

## 3. 替代方案

- **方案 X**（每个 `<step-pause>` 自带提示文本）：被拒绝。理由：① 文本漂移不可控；② 跨 phase 同 key 行为可能不一致；③ 阻碍未来生成器化（ADR-021）。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 标签定义补充 `<input-protocol>` 子标签
- **编排器**：`core/workflow.xml` step 4 内 6 处 `<step-pause>` 全部使用 `<input-protocol>`
- **CI**：`check-step-pause-registry.sh`（PR-5 启用）兜底 `<input-protocol>` 完整性
- **跨平台**：所有平台等价（提示模板纯文本注入）

## 5. 引用

- v2.2 主文档 §6 D2 拍板纪要（v1.0 review 第 1 项）
- ADR-016（`<step-pause>` 必填参数表）
- ADR-018（parse-error 4 类生命周期）
