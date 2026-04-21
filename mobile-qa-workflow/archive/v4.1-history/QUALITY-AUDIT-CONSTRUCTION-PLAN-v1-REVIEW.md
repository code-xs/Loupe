# Mobile B2C 质量工作流 — 施工文档 v1 Review

> 审阅对象：[`QUALITY-AUDIT-CONSTRUCTION-PLAN-v1.md`](./QUALITY-AUDIT-CONSTRUCTION-PLAN-v1.md)
>
> 审阅基线：`mobile-qa-workflow/` 当前源码现状
>
> 审阅日期：2026-04-20

---

## 总体评价

- `QUALITY-AUDIT-CONSTRUCTION-PLAN-v1.md` 相比 v0.1 的最大进步是“先拍板协议再拆 PR”：
  - 明确采用 `current_phase_result` 运行时变量方案 A
  - 补齐 step-pause 的可执行输入协议
  - 澄清 tag 白名单边界
  - 把“9 条主修复 + 5 项配套包装”拆成双口径
- 但 v1.0 仍有 3 个会直接影响落地正确性的缺口：
  - `fanout_mode` 命名体系前后不一致
  - step-pause 写回落地后与编排器读取点不对齐
  - `schema_version = 4` 升级在 PR-1 修改清单里缺显式动作

---

## P0 阻塞问题

### P0-1：`rca_fanout_mode` 在 DoD/迁移里出现，但 PR-1 schema 清单未定义该字段，命名体系不一致

- 证据：
  - PR-1 的 status-template 变更只列了 `fix_fanout_mode`、`phase_history`、`rca_fanout_mode_snapshot`、`user_inputs`
  - 但 DoD 要求“只允许 `rca_fanout_mode`”
  - 迁移决策表也要迁移到 `rca_fanout_mode`
- 风险：
  - 实施时会出现“文档说要有 `rca_fanout_mode`，schema 却没定义”的双轨语义
  - PR-4、迁移脚本、CI 校验三处会各自实现出不同口径
- 建议：
  - 二选一并全篇统一
  - 更建议保留现有 `fanout_mode` 作为 RCA 字段，只新增 `fix_fanout_mode` 做隔离
  - 把所有提到 `rca_fanout_mode` 的地方改回 `fanout_mode`
  - `rca_fanout_mode_snapshot` 可以继续保留作为快照兜底字段

### P0-2：step-pause 写回后落入 `user_inputs.*`，但编排器当前读取的是顶层字段，未对齐

- 源码事实：
  - 编排器 `Non-Bug` 分支读取 `{non_bug_user_choice}`
  - 当前状态模板没有 `non_bug_user_choice` 字段
- v1.0 方案：
  - PR-2 计划把用户选择写入 `workflow_status.user_inputs.<key>`
  - 动态用例也按 `user_inputs` 断言
- 风险：
  - 即便 PR-2 完成写回，主编排器仍可能读不到现有分支逻辑依赖的字段
  - B2/C11 会以“实现了写回容器，但业务分支仍断链”的形式残留
- 建议：
  - PR-2 必须明确写回策略
  - 最稳方案：过渡期同时写两份
    - `workflow_status.user_inputs.<key> = <value>` 作为统一容器
    - 对现有读取点同步镜像到顶层字段（至少覆盖 `non_bug_user_choice`）
  - 待 v4.2 再统一收敛到 user_inputs-only

### P0-3：`schema_version: 4` 的升级在 PR-1 修改清单里缺显式动作

- 证据：
  - 迁移脚本和回归矩阵都以 `schema_version = 4` 为目标
  - 但 PR-1 的 status-template 修改清单没有明确写“`schema_version: 3 → 4`”
- 风险：
  - 实施时容易漏改 template 版本号
  - 会让迁移脚本、DoD、文档同步三者失去统一版本锚点
- 建议：
  - 在 PR-1 里显式增加一条：`workflow-status-template.yaml` 的 `schema_version: 3 → 4`
  - PR-7 文档同步也同步引用这一版本升级动作

---

## P1 重要问题

### P1-1：step-pause 的“无需 LLM 猜测”表述过强，建议改成“最小可判定”

- 当前实现仍由 LLM 执行“解析用户回复”的 `<action>`
- 输入协议只能降低歧义，不能严格保证零推断
- 建议：
  - 所有 step-pause 标题固定追加一行：`请用 <key>=<value> 回复`
  - parse-error 时回显允许值白名单
  - 文档表述从“无需 LLM 猜测”改成“最小可判定、低歧义、可审计”

### P1-2：`phase_history` 的结构未定型，容易出现“写了但不可用”

- v1.0 多处依赖 `phase_history`
  - C10 迁移
  - P3 step 7 写入
- 但当前文档没有定死数组元素结构
- 建议：
  - 在 PR-1 的 status-template 注释里增加最小结构约束
  - 建议至少包含：
    - `phase`
    - `timestamp`
    - `fanout_mode`
    - `note`（可选）

---

## 建议修改

- 统一 RCA fanout 命名体系：`fanout_mode` / `rca_fanout_mode` / `rca_fanout_mode_snapshot` 只能保留一套主语义
- 在 PR-2 段落补充“兼容性写回规则”：哪些 key 写入 `user_inputs`，哪些需要镜像到顶层字段
- 在 PR-1 修改清单补上 `schema_version` 升级条目，避免实施时漏改

---

## 建议拍板的 2 个问题

1. v4.1 最终保留的 RCA fanout 字段名是 `fanout_mode` 还是 `rca_fanout_mode`？
2. step-pause 写回是“只写 `user_inputs.*`”还是“`user_inputs.*` + 顶层镜像（过渡期）”？

---

## 结论

- v1.0 已经从“可讨论的大纲”提升到了“接近可施工的大纲”。
- 但在正式展开 PR-1 之前，建议先修正上述 3 个 P0 问题，否则后续 PR 会在字段命名和写回协议上反复返工。

