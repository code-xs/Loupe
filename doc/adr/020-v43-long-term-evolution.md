# ADR-020: v4.3 长期演进规划占位

> **状态**：superseded-by-v4.3-plan（v4.3 立项启动时升级）
> **关联决定**：D20（占位 / 无 v2.x 拍板纪要）
> **关联 PR**：**v4.3 PR-N（待立项）**

## 1. 背景

v4.1 / v4.2 是小迭代定位，存在多项延后到 v4.3 评估的演进项（如 ADR-006 Deep-Dive 键名收敛 / ADR-008 user_inputs-only 收敛 / ADR-019 v3-legacy 物理删除 / install_trae.sh shim 删除等）。需要一个汇总入口便于 v4.3 立项时统一评估。

## 2. 决定（占位，v4.3 立项时 finalize）

v4.3 长期演进项汇总：
- **协议层收敛**：ADR-006 Deep-Dive 键名映射收敛 / ADR-008 user_inputs-only 收敛
- **历史清理**：ADR-019 v3-legacy 物理删除（满足 3 项前提后）/ ADR-012 install_trae.sh shim 删除
- **新功能**：v4.2 遗留 #1-#6 评估纳入 v4.3 范围

## 3. 替代方案

- **方案 X**（不留占位，v4.3 时再评估）：被拒绝。理由：① 散落在多个 ADR / 遗留清单中难以汇总；② 占位 ADR 提供 single point of evolution。

## 4. 影响

- **v4.3 立项**：本 ADR 是 v4.3 README §1 入口
- **状态切换**：v4.3 立项时本 ADR 升级为 active 或 superseded（按实际拆分情况）

## 5. 引用

- ADR-006 / ADR-008 / ADR-012 / ADR-019（被本 ADR 汇总）
- v4.2 README "v4.2 遗留 #1-#6"（待评估清单）
