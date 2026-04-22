# ADR-015: `user_inputs` 顶层镜像白名单受限双写

> **状态**：active
> **关联决定**：D15（v2.1 review 拍板）
> **关联 PR**：v4.1 PR-1 + PR-2（已合入）

## 1. 背景

ADR-008 定义了"`user_inputs.<key>` 总写 + 顶层镜像双写"的过渡方案，但若按通用 `{key}` 无条件镜像顶层，会随 step-pause 数量增加污染顶层 schema。需要受控边界。

## 2. 决定

**白名单受限双写**：
1. **写入端规则**：`<step-pause>` 触发的写回 = `user_inputs.<key>` 总写 + 顶层 `<key>` **仅当 key 在白名单内时才写**
2. **白名单位置**：`core/workflow-status-template.yaml` 头部注释"⚠️ 顶层镜像字段白名单"标记的字段集
3. **v4.1 起步白名单** = `{non_bug_user_choice}`（仅 1 个条目；未来扩展需更新白名单 + 同步 ADR）
4. **CI 守门**：`Check 3 — D15 顶层白名单守门`（已落地，error 级）双向校验：① 顶层引用必须注册；② 不在白名单的 result_field 不允许有顶层镜像定义

## 3. 替代方案

- **方案 X**（无条件双写）：被拒绝。理由：① 长期污染顶层 schema；② 难以统计"哪些字段是真业务字段，哪些是 mirror 残留"。
- **方案 Y**（仅写 `user_inputs.*`，编排器改读 `{user_inputs.<key>}`）：被推迟到 v4.2 收敛阶段（登记 v4.2 遗留 #3）。

## 4. 影响

- **协议层**：`core/workflow-status-template.yaml` 头部注释定义白名单格式（锚点 `^# ⚠️ 顶层镜像字段白名单`）
- **编排器**：`core/workflow.xml` step 4 case 写回逻辑显式按白名单分支
- **CI**：`Check 3` 双向守门
- **未来扩展**：新增镜像字段必须 ① 加入白名单注释 ② 加入 status-template 顶层 ③ 在编排器 step 4 case 中显式双写 ④ 在本 ADR 引用清单更新

## 5. 引用

- v2.2 主文档 §6 D15 拍板纪要
- ADR-008（双写过渡总框架）
- ADR-017（non_bug_context 是镜像白名单的兼容字段，单独 ADR 描述）

## 6. v4.2 PR-6 修订段 — 顶层镜像白名单全量下线（O12 收尾 / 2026-04-22）

**变化背景**：v4.1 起步白名单 = `{ non_bug_user_choice }`（仅 1 项）的"白名单元协议"维护成本
（PR Review + CI 4 个 Check + 跨文档说明）显著高于其收益。v4.2 PR-6 完成 O12 收尾：
保留双写实现已不必要（编排器 4a 改为单写 user_inputs.<key>），同步删除顶层镜像字段定义。

**收口动作**：
1. `core/workflow-status-template.yaml` 删除顶层 `non_bug_user_choice` 字段（TPL-D2）；
2. `core/workflow-status-template.yaml` 删除"⚠️ 顶层镜像字段白名单"注释段（TPL-D2）；
3. `core/workflow.xml` step 4a 删除 mirror_to_top 双写分支（XML-D1）；
4. `core/step-pause-registry.yaml` 删除 Non-Bug 项 mirror_to_top 标记（REG-D1）；
5. `core/core-rules.xml` `<input-protocol>` rule n=5 简化为单写描述（RULES-D1）；
6. `system-prompt.md` 全量重写后不含"白名单受限双写"段（SP-N1，由 Seg-2 完成）；
7. `PLATFORM-GUIDE.md` 删除顶层镜像白名单说明（DOC-D1）；
8. CI Check 3 / Check 4 全部下线（依赖白名单段已不存在 / 由 Seg-3 完成）。

**收口后契约**：
- 编排器 4a 解析 step-pause 用户回复后**仅写入** `user_inputs.<result_field>`（单写）；
- phase / system-prompt / PLATFORM-GUIDE 引用用户回复值时，统一使用 `{user_inputs.<key>}` 形式；
- 历史镜像字段恢复路径：若未来需要恢复某字段顶层镜像（罕见），需通过新 ADR 评估，绑定 schema 复活 + 编排器双写改造 + CI 守门重建。

**关联**：
- ADR-008（v4.2 PR-6 修订段：顶层镜像协议正式退役）
- ADR-014 §7 PR-6 收口纪要
- ADR-019 superseded
