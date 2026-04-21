# PR-2 施工方案质检报告（v1.1 复审）

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-2-sync-debt-and-system-prompt-generator.md`
> 评审版本：`v1.1`
> 评审日期：2026-04-21
> 复审结论：**较 v1.0 明显改进，但当前版本仍不建议直接开工**
> 评审方式：对照上一轮 Review 逐项复核修订项，并继续校验新增方案在当前仓库语境下是否真正可执行。

---

## 1. 复审结论

本次修订有明显进步，上一轮指出的 4 个关键方向里，已有 3 个得到实质性收敛：

- O5 已从“直接升 error”改为“先修提取器，再升 error”
- CI-U2 已删除，避免把 `check-io-contract.sh` 的宽松模型误升为强门禁
- 生成器口径已明确改成“最小完整实现”，不再在“骨架 / 完整实现”之间摇摆

同时，O7 也不再停留在“假设已有读端”的状态，而是补了 READ-N1 / READ-N2 / TEST-N1，方向上是正确的。

但复审后，当前版本仍有 **1 个阻断项** 和 **2 个高优先级问题**：

- SCRIPT-FIX1 / CI-N1 的新正则无法从 `core/workflow.xml` 中提取 `allowed_values="Confirm"`，O5/H1 新方案按文实现会直接失效
- READ-N1 / READ-N2 的落点描述与当前真实文件结构没有完全对齐，容易误导实施
- `system-prompt.md` 的改动边界仍存在自相矛盾描述

**综合裁定**：`仍需小修一版后再开工`

---

## 2. 本轮可确认已修复项

### 2.1 上轮 Blocking 1 已基本收口

- v1.0 最大问题是 O7 直接删除 `rca_fanout_mode_snapshot`，却没有真实读端。
- v1.1 已明确新增：
  - READ-N1：P3 反查 `phase_history`
  - READ-N2：补读 `phase_history`
  - TEST-N1：给出等价回放测试
- 这至少把“凭空假设已有读端”改成了“显式交付读端闭环”，方向正确。

### 2.2 上轮 Blocking 2 已基本收口

- v1.0 是“先升 error，再想办法解释 warning”。
- v1.1 已改为：
  - 先修 `check-system-prompt-sync.sh` 提取器
  - 再升级 severity
  - 并增加“实跑零 warning 才能升级”的硬前置条件
- 这个顺序是合理的。

### 2.3 上轮 Major 1 / Major 3 已明显改进

- `check-io-contract.sh` 不再在本 PR 内强升 error，这个取舍是对的。
- 生成器改成“最小完整实现”，DoD 也同步加强，这比 v1.0 清晰得多。

---

## 3. Blocking Finding

### 3.1 阻断问题：SCRIPT-FIX1 / CI-N1 的提取正则无法匹配 `core/workflow.xml` 中带引号的 `allowed_values`

**结论**：v1.1 虽然把 H1 和 sync 提取方案从“首个命中”改成了“锚点提取”，方向正确；但当前给出的正则本身写错了，按文实现后无法从 `core/workflow.xml` 中提取 `allowed_values="Confirm"`，会让 O5 和 CI-N1 两条主链都直接失效。

**事实依据**：

- 施工单在 SCRIPT-FIX1 中给出的新提取：

```bash
grep -oE 'allowed_values=[^[:space:],"<)]+' 
```

- CI-N1 中给出的函数提取：

```bash
grep -oE 'allowed_values=[^[:space:],"`<)]+'
```

- 但当前真实 `core/workflow.xml` 的 Spec-Uncertain 写法是：

```xml
allowed_values="Confirm"
```

- 这两条 regex 在 `=` 之后都**不允许双引号作为首字符**，因此不会命中 `allowed_values="Confirm"` 这类 XML attribute。

**直接后果**：

- `SU_CORE` / `CORE_SU` 会是空字符串
- SCRIPT-FIX1 无法达到“实跑零 warning”
- CI-N1 的 DoD `sp=1|2|S / core=Confirm` 按当前正则实际上不可达

**修订建议**：

- 直接把提取正则改成同时兼容：
  - `allowed_values="Confirm"`
  - `allowed_values=1|2|S`
- 更稳妥的做法是允许可选引号，例如先提整段，再统一去引号：

```bash
grep -oE 'allowed_values="?[^[:space:],"`<)]+"?'
```

然后再用 `sed` 去掉 `allowed_values=` 与外围引号。

在这个问题修掉之前，v1.1 仍不能视为可实施版本。

---

## 4. Major Findings

### 4.1 高优先级问题 1：READ-N1 / READ-N2 的落点描述与真实文件结构未完全对齐

**结论**：v1.1 虽然正确意识到要补读端，但具体落点描述仍有两处与当前仓库结构不一致，容易误导实施者。

**事实依据**：

- 施工单写 READ-N1 时说：
  - “在 step 4 头部（原 step 4 第一行 `<action>读取 {issue_card}...</action>` 不动）”
- 但当前真实 `p3-root-cause.md` 中：
  - `读取 {issue_card}、{spec_file}、{context_bundle}、{workflow_status}` 在 **step 1**
  - `step 4` 的第一行其实是“读取 Issue_Boundary_Level”

- 施工单写 READ-N2 时说：
  - `core/workflow.xml` **step 1** 读字段列表追加 `phase_history`
- 但当前真实编排器中，读取 `workflow_status` 字段列表的动作发生在 **step 2**，不是 step 1。

**风险**：

- 实施者照着施工单找代码时会定位错位置。
- reviewer 也难以通过“原文 / 新文对照”快速确认是否改对。
- READ-N2 的必要性表述也偏弱，因为当前 P3 自己在 step 1 已经读取了整个 `{workflow_status}`。

**修订建议**：

- 把 READ-N1 的插入点说明改成“插在 `p3-root-cause.md` step 4 第一个边界策略动作之前”。
- 把 READ-N2 统一改成“编排器 step 2 读字段列表追加 `phase_history`”。
- 最好再补一句：READ-N2 是“为编排器和 Limited 平台显式暴露字段”，不是 P3 读取该字段的唯一前提。

---

### 4.2 高优先级问题 2：`system-prompt.md` 的修改边界描述仍然自相矛盾

**结论**：v1.1 已经明确引入 ANCHOR-N1，但 `2.5 文件 E` 的总约束仍写着“本 PR 只允许对 `system-prompt.md` 做 O7/O8 字段名替换，不允许任何其他改动”，这与下文新增锚点的方案冲突。

**事实依据**：

- `2.5 文件 E` 开头写的是：
  - “本 PR 只允许对 `system-prompt.md` 做 O7/O8 字段名替换，不允许任何其他改动”
- 但 v1.1 后文又明确新增：
  - ANCHOR-N1：在 `system-prompt.md` 中插入 `<!-- ANCHOR: spec-uncertain-allowed-values -->`
- DoD 里也承认：
  - `system-prompt.md` 改动 = REF-D5 + ANCHOR-N1

**风险**：

- reviewer 在读 2.5 时会以为 ANCHOR-N1 违反范围边界。
- 实施者可能为了满足“只做 O7/O8”而误删锚点，反过来导致 CI-N1 失效。

**修订建议**：

- 把 2.5 开头那句统一改成：
  - “本 PR 只允许对 `system-prompt.md` 做 REF-D5 + ANCHOR-N1 两类改动”
- 同时明确：
  - REF-D5 = 字段表 / 写回描述改名
  - ANCHOR-N1 = H1 稳定锚点

---

## 5. 次要问题

### 5.1 fixture 文件名与内容语义相反

- 文件名是 `p3-reentry-with-snapshot-but-no-history.yaml`
- 但示例内容实际上是：
  - `fanout_mode: null`
  - `phase_history` 存在
  - 并没有 `snapshot`

建议改名为更符合内容的名字，例如：

- `p3-reentry-null-fanout-with-phase-history.yaml`

这不影响方案方向，但会减少误解。

### 5.2 O7 DoD 的 grep 口径仍略有歧义

- DoD 写“`rca_fanout_mode_snapshot` 命中 0 处（仅注释允许提及）”
- 如果注释允许提及，就不应写“命中 0 处”

建议改成：

- “运行时主链文件内非注释命中 0 处”
- 或“schema / phase / 对外文档正文命中 0 处，ADR/施工单注释除外”

---

## 6. 最终裁定

**裁定**：`Needs one more revision`

**当前状态判断**：

- 相比 v1.0：**明显进步**
- 是否已经可直接实施：**还差最后一轮小修**

**必须修掉的点**：

1. 修正 H1 / SCRIPT-FIX1 中提取 `allowed_values` 的 regex，确保兼容 XML 引号形式
2. 校正 READ-N1 / READ-N2 的真实落点描述
3. 统一 `system-prompt.md` 的允许改动范围表述

如果你把这 3 处再修一下，我倾向于下一轮可以给出“通过，可开工”的结论。
