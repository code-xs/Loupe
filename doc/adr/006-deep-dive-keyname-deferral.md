# ADR-006: Deep-Dive 键名映射延后

> **状态**：active
> **关联决定**：D6（v1.0 review 拍板）
> **关联 PR**：v4.1 不动 / v4.3 评估

## 1. 背景

`functionality-deep-dive/core/workflow.xml` 与主流程 `core/workflow.xml` 之间存在键名映射约定（如 deep-dive 写 `workflow_version=v3-legacy`，主流程写 `workflow_version=legacy`，详见 PR-1 v1.1 §6 议题 H2）。这种映射是历史演进遗留，理论上应在某次大版本统一。

## 2. 决定

v4.1 / v4.2 **不动** Deep-Dive 与主流程的键名映射，延后到 v4.3 立项时统一评估：
- v4.1 / v4.2 的所有 SKILL 改动**必须保留**两侧的字面差异（不得擅自统一）
- v4.3 立项时，由 ADR-020（v4.3 长期演进）评估"键名收敛 vs 保留双侧"的取舍

## 3. 替代方案

- **方案 X**（v4.1 立即统一）：被拒绝。理由：① 双侧老会话恢复链路均依赖各自字面值（兼容性触达面广）；② v4.1 是小迭代定位；③ 统一需要双侧迁移脚本，超出 v4.1 预算。

## 4. 影响

- **DSL 层**：两侧 `core/workflow.xml` 的 v3 兼容默认值保留差异（主流程 `legacy` vs deep-dive `v3-legacy`）
- **统计口径**：v3-legacy 流量统计需双侧累加（详见 ADR-019 删除前提 + PR-1 v1.1 议题 H2）
- **CI**：`check-state-enum.sh` 仅校验状态名（不涉及 workflow_version 字符串），不冲突

## 5. 引用

- v2.2 主文档 §6 D6 拍板纪要
- v4.2 PR-1 v1.1 §6 议题 H2（双侧 workflow_version 默认值差异）
- ADR-019（v3-legacy allowlist 与本 ADR 同源）
