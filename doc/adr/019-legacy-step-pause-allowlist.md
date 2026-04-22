# ADR-019: legacy phase `<step-pause>` allowlist 实体化交付

> **状态**：superseded-by-v4.2-PR-6（v4.2 D14 整改清零 / 详见 ADR-014 §7）
> **关联决定**：D19（v2.2 review 第 P1-3 项）
> **关联 PR**：v4.1 PR-5 + PR-8（已合入）+ v4.2 PR-6 退役（详见 §6）

> **语义复用**：本 ADR 同时承载 v4.2 PR-1 落地的 v3-legacy agent 归档退役（详见 v4.2 PR-1 §2.3 DD-A1~A5 + DD-D1）。"legacy" 一词在本 ADR 内同时覆盖：① v3 现存的 phase 内 step-pause 条目；② v3-legacy 会话恢复专用的 deep-dive agent。两者共享同一退役治理框架。

## 1. 背景

D14（ADR-014）的 CI/DoD 已经依赖 `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 作为现存 phase 内 `<step-pause>` 的白名单输入，但 PR-5/PR-8 的交付清单里没有任何一处负责创建和维护这个文件。CI 守门会依赖一个未纳入施工清单的关键产物。

## 2. 决定

**实体化交付**：
1. **PR-5** 负责根据现状盘点生成 `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 首版内容
2. **文件格式**：`<path>:<line>:<semantic-id>`（每行一条；line 容许 ±5 行漂移；CI 仅校验 path 与 semantic-id）
3. **首版条目** = 2 个（P2 step 4 Spec-Uncertain / P4 step 6 Fix-Designing）
4. **PR-8** 的 CI（`Check 2 — D14 调度作用域 + D19 allowlist 双向匹配` + `Check 6 — D19 allowlist 存在/非空/格式`）以该文件为权威输入
5. **v4.3 物理删除前提**（合并 v3-legacy agent 退役 / v4.2 PR-1 DD-D1 复用）：
   - 所有持久化会话的 `schema_version >= 4`
   - 90 天内零 v3-legacy 流量（按 `workflow_version=v3-legacy` + `legacy_flow_mode=true` 标记的会话计数为 0；**注意**：主流程 `core/workflow.xml` 默认值是 `workflow_version = legacy`，与 deep-dive 的 `v3-legacy` 是不同字符串值，统计需双侧累加）
   - 主流程与 deep-dive 子流程均无 `<load target="archive/v3-legacy/...">` 残留引用（grep 验证）

## 3. 替代方案

- **方案 X**（CI 内嵌硬编码 allowlist）：被拒绝。理由：① CI 与数据耦合；② 维护人需要改 yml；③ 违反"数据驱动"原则。

## 4. 影响

- **CI**：固化条目数 == 2（`Check 6` 守门）；超出该数需要本 ADR + CI 同步评审
- **DoD**：v4.2 / v4.3 任何 phase 内 step-pause 调整必须同步 allowlist + 本 ADR
- **v3-legacy 会话恢复**（v4.2 PR-1 引入）：deep-dive agent 归档至 `functionality-deep-dive/agents/archive/v3-legacy/`，恢复时按动态 name 解析或显式 `<load>` 加载

## 5. 引用

- v2.2 主文档 §6 D19 拍板纪要
- ADR-014（D14 调度作用域 / 与本 ADR 双向绑定）
- ADR-006（Deep-Dive 键名映射延后 / workflow_version 双侧差异）
- v4.2 PR-1 §2.3（DD-A1~A5 + DD-D1 / v3-legacy agent 归档）
- v4.2 PR-1 v1.1 §6 议题 H2（双侧 workflow_version 默认值差异统计口径）

## 6. 退役纪要（v4.2 PR-6 / 2026-04-22）

**退役条件**：
- D14 整改清零（O13 + O14 / phase 内联 step-pause 0 处）→ allowlist 文件中 2 条条目均无对应源码命中；
- ADR-014 §7 PR-6 收口纪要承接本 ADR 的"D14 例外清单"管理职责（v4.2 PR-6 起无任何例外）。

**物理动作**：
1. `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 物理删除（FILE-D1）；
2. CI Check 1 / Check 2 / Check 6 全部下线（CI-D1）；
3. `scripts/check-io-contract.sh` 删除 allowlist 加载与豁免分支（SCRIPT-D1），mutex 段保留作为 inline 形态回潮兜底防线；
4. `scripts/check-step-pause-form.sh` 新增（SCRIPT-D6 / Check 17 / error）作为 single-form 强守门。

**v4.3 演进**：本 ADR 完整退役（无后续动作）；ADR-014 §7 与 ADR-016 v4.2 修订段 #2 共同承接 D14 治理职责。
