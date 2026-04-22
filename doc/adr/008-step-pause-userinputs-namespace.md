# ADR-008: `<step-pause>` 写入 `user_inputs.*` 命名空间 + 顶层镜像双写过渡

> **状态**：active
> **关联决定**：D8（v1.0 review 第 P0-2 项 / 双写过渡方案）
> **关联 PR**：v4.1 PR-2（已合入）

## 1. 背景

`<step-pause>` 收到用户回复后写回到 `user_inputs.<key>` 是天然命名空间，但编排器读取保持现状（顶层 `{non_bug_user_choice}` 等），业务分支会断链。需要在协议层定义双写过渡。

## 2. 决定

v4.1 起采用**双写过渡**方案（v4.2 收敛到 `user_inputs.*`-only）：
1. **写入端**：`<step-pause>` 写回时**同时写** `user_inputs.<key>` + 顶层 `<key>`
2. **读取端**：编排器保持现状（继续读顶层 `{non_bug_user_choice}` 等），无破坏性修改
3. **顶层镜像受白名单约束**（详见 ADR-015）：`v4.1` 起步集合 = `{non_bug_user_choice}`，未来扩展需更新白名单
4. **v4.2 后续收敛**：移除顶层镜像，编排器改读 `{user_inputs.<key>}`（登记 v4.2 遗留 #3）

## 3. 替代方案

- **方案 X**（v4.1 立即收敛到 user_inputs-only）：被拒绝。理由：编排器需要同步改造，超出 v4.1 范围。
- **方案 Y**（永久双写）：被拒绝。理由：长期会污染顶层 schema 表面积。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 协议补充"双写规则 + 白名单引用"
- **编排器**：`core/workflow.xml` step 4 case 写回逻辑显式双写
- **状态模板**：`core/workflow-status-template.yaml` 顶层镜像白名单注释（D15）
- **CI**：`check-system-prompt-sync.sh` 兜底白名单一致性

## 5. 引用

- v2.2 主文档 §6 D8 拍板纪要
- ADR-015（白名单受限双写）
- ADR-002（`<input-protocol>` 解析协议）

## v4.2 PR-6 修订段（2026-04-22）

**变化**：v4.1 起步的"双写过渡总框架"已于 v4.2 PR-6 完成单写收口（详见 ADR-015 §6）。
编排器 4a 现在统一走 `user_inputs.<key>` 单写路径，顶层镜像字段全量下线。

**当前契约**：
- `<step-pause>` 触发的写回 = `user_inputs.<result_field>` 单写；
- 引用方统一用 `{user_inputs.<key>}` 形式；
- v4.3 不再有镜像扩展计划（如未来需重新引入镜像，需通过新 ADR 评估）。
