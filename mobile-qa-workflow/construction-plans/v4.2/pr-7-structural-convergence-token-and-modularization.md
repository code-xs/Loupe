# PR-7 · 结构收敛 + Token 优化 + 模块化（O15 / O16 / O11+ / O19+ / O23 / O24 / O25）

> **主控文档**：[`./README.md`](./README.md) §1 PR-7 总览 / §3 依赖 / §4 CI 守门 / §5 跨平台矩阵 / §6 PR-7  
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md)（O11+ / O15 / O16 / O19+ / O23–O25 / B4 / B4.5 / B5 / §4.2 DoD 8–9 条 / §4.3 兼容策略 / §9.2 O25 范围）  
> **v1.1 修订所吸收的 Review**：[pr-7-structural-convergence-token-and-modularization-REVIEW-2026-04-22.md](./pr-7-structural-convergence-token-and-modularization-REVIEW-2026-04-22.md)（**Needs Fixes → 本版收口 7 项**）  
> **前置 PR**：`main` 上 **PR-1～PR-6 已合入**（PR-6：`system-prompt.md` 由 `build-system-prompt.py` 构建；PR-3/3'：`<phase-abort>` 可用。）  
> **状态**：📐 施工方案 **v1.1**（2026-04-22）— **可进实施/复审**；开 PR 前仍建议对 `main` 行号与 grep 触达面 **rebase 对齐**  
> **v1.0 全文**：v1.0 仅保留于 git 历史；**v1.1 在 v1.0 上**替换并列口径、补齐 CI/Token/O24/O16/聚合/加载策略。

---

## 0. v1.0 → v1.1 修订摘要

| ID | 触发（Review / 自审） | v1.0 问题 | v1.1 收口方式 |
|----|------------------------|------------|----------------|
| R1 | Finding 1 | `coder-agent` 多口径并列 | **§2.1 唯一规范**：调用方**仅** `load` 入口 + P6 唯一例外（§2.1） |
| R2 | Finding 2 | O25 vs Limited 与 V1.1 §9.2 打架 | **§2.2 定版方案 A**：O25 收益**仅**计 Full；Limited 不宣称 O25 强约束 |
| R3 | Finding 3 | load 路径 CI 为可选 | **§5.1 必做**：`check-load-targets.sh` error（至少含 phases/agents） |
| R4 | Finding 4 | Token DoD 不可复现 | **§2.3 SOP**：基线、case、工具、统计边界、禁止以行数替代主证据 |
| R5 | Finding 5 | O16 兼容弱于 V1.1 §4.3 | **§3.2.1 分岔 A/B** + DoD 写清 |
| R6 | Finding 6 | `core-rules` 聚合二选一 | **§3.3.1 定版 D-AGG-1** + 生成器约定 |
| R7 | Finding 7 | O24 无决策表 | **§3.4.1 真值表** + 与 `issue_card` 模板字段对齐 |
| — | 结构保留 | v1.0 批次与优点 | 保留 B4/B4.5/B5、GEN-PR7、砍 scope、附录 §A |

---

## 0.1 与主控的映射表

| 主控 §6 PR-7 条目 | V1.1 项 | 本设计中的「可交付物」 |
|------------------|--------|------------------------|
| 子工作流收敛 | **O15** | `phases/p3-root-cause.md`：三档升级早退**面**收敛（§3.1；**不**改 `phase-abort` 语义） |
| 结构收敛 | **O16** | `functionality-deep-dive/**` 键名 + `config-schema`；**§3.2.1** 兼容分岔 |
| invoke + coder 三件 + shared-input-guard | **O11+** | **§2.1** 为唯一规范；`coder-workflow.md` / `contract-checklist-spec.md` / `shared-input-guard.md` |
| wrapper + shared-input-guard | **O19+** | 基座删除重复入参、改 `<load shared-input-guard.md>` |
| core-rules 双文件 | **O23** | **§3.3.1** essential + dsl + 聚合 + phase 只 load essential |
| reasoning 按类拆分 | **O24** | `reasoning-chain-core` + 四 guide；**§3.4.1** `issue_card` 字段与路由规则对齐 |
| SubAgent 轻量规则 | **O25** | `core-rules-subagent.xml`；**§2.2** 仅 Full 路径强制替换 load |

---

## 1. PR 元信息

| 项 | 值 |
|----|-----|
| 建议分支名 | `feat/qa-workflow-v4.2-pr7-structural-convergence` |
| Base | **PR-6 合入且 CI 全绿**的 `main`；Token 基线见 **§2.3** |
| 层级 | 🟡 文件拆分 + 加载路径；**不**改状态机 / Registry / step-pause 语义（O16 仅键名+兼容层） |
| 关联 V1.1 项 | **O15, O16, O11+, O19+, O23, O24, O25** |
| **工作量** | **2.5d**（可部分并行；见 §9） |
| Reviewer | 方案 owner + 平台 owner + 子工作流（deep-dive）owner |

---

## 2. 唯一规范与硬约束（v1.1 核心：禁止并列实现口径）

### 2.1 O11+ · `coder-agent` 唯一加载规范（定版，吸收 Review F1 + V1.1 B5 stub 承诺）

| 规则 | 内容 |
|------|------|
| **P5 / 任意 invoke Coder 路径** | **有且仅有一条**：`<load target="mobile-qa-workflow/agents/coder-agent.md" .../>`（路径以仓库为准，与现有一致）。**禁止**在同一段调用链上再单独 `<load> coder-workflow.md` 或 `contract-checklist-spec.md`（**P6 例外** 除外）。**禁止**在 phase 中采用「仅 load 子文件、不经过入口」或「入口与 phase 各 load 一段」的**双写**口径。 |
| **入口实现** | **定版 E1**：`coder-agent.md` 正文含：角色/契约/工具/命名等「入口必备块」+ 两条**显式**且**固定顺序**的 `<load target=".../coder-workflow.md">` 再 `<load target=".../contract-checklist-spec.md">`。不采用非标准 Markdown include。**rejected**：P5 对子文件**单独** load、入口不含两段下游。 |
| **P6 仅要 Checklist 时** | **唯一例外**：`<load target=".../reference/contract-checklist-spec.md" .../>`；**不** load `coder-agent.md`、**不** load `coder-workflow.md`。 |
| **Limited 单 prompt** | 仍只依赖 `coder-agent.md` **一个**路径入口；子 load 在入口内连续展开，不增加对 Limited 的「多入口」要求。 |
| **v4.3** | 保留与 V1.1 一致：之后可再评估 stub/瘦身，本 PR 不删入口文件。 |

📌 **PR-7 实施已落地（2026-04-22 / O11+ 完成）**：

| 项 | 落地形态 |
|----|----------|
| 新增 | `mobile-qa-workflow/agents/coder-workflow.md`（约 130 行）：四阶段工作流（契约溯源 / 精确编码 / 微验证纠错 / 产出移交）+ Error Dump 标准模板。 |
| 新增 | `mobile-qa-workflow/reference/contract-checklist-spec.md`（约 35 行）：Contract Checklist 反空泛规范（5 项最小必填 + 校验规则 + 4 项空泛检测标准）+ 平台溯源映射表（Android / iOS / Flutter / RN）。 |
| 改写 | `mobile-qa-workflow/agents/coder-agent.md`：从 270 行缩至 109 行；保留入口必备块（角色 / 输入契约 / 输出契约 / 变量命名 / 工具权限 / 返回判定协议）；在「工具权限」段后、「返回判定协议」段前以**固定顺序**插入两条 `<load>`：先 `agents/coder-workflow.md`，后 `reference/contract-checklist-spec.md`。**rejected**：P5 / 任意 invoke 直接 load 子文件（守门拦截）。 |
| Phase 触达 | P5 `phases/p5-fix-impl.md` L87（Full / invoke-subagent）+ L99（Limited / 内联降级）已是 **唯一入口** 形态（仅 `<load coder-agent.md>`，本 PR 不动）；P6 `phases/p6-verification.md` 不 load 任何 coder 子文件（§A 自检结论），P6 例外通路保留为 v4.3 接口。**0 个 phase 文件需要本 PR 修改**——拆分对调用方完全透明。 |
| CI | **Check 22**（`schema-check` workflow）：`bash mobile-qa-workflow/scripts/check-coder-entry.sh` / **error 起步**。三层守门：(a) `coder-workflow.md` / `contract-checklist-spec.md` 仅由入口 `<load>`（含 P6 例外白名单）、(b) 入口内两条下游 `<load>` 顺序合规（workflow 先于 checklist）、(c) P5 `<load coder-agent.md>` 触达存在。Check 18 编号继续保留给 GEN-PR7 的 `check-load-targets.sh`（下游路径可达性 = test -f）。 |
| 单测 | 现有 44 用例全绿；O11+ 不改 build-system-prompt.py / system-prompt.md（system-prompt.md 不内嵌 phase / agent 全文）。 |

---

### 2.2 O25 与平台 · **定版方案 A**（吸收 Review F2 + 对齐 V1.1 §9.2「范围限定」）

| 规则 | 内容 |
|------|------|
| **Full 平台**（`env_subagent=true` 且子对话隔离） | `invoke-subagent` 的 `subagent_prompt` **必须**以 `<load core-rules-subagent.xml/>` 替代对 **完整** `core-rules.xml` 的 load（实现见 §3.5）。**O25 的 token/工程收益**在此路径上统计与宣发。 |
| **Limited 平台**（`env_subagent=false`，内联模拟） | **不**将 O25 计为**单独**的「子 Agent 轻量块」收益；与 V1.1 §9.2 / §3.3.25 **一致**表述为：**O25 不适用于** Limited 子 Agent 形态。Limited 的 token 降幅来自 **O17+ 生成器** 对 L1/L3 的裁剪、**O23/O24** 在单 prompt 中的**间接**节身（`build-system-prompt.py` 已统一收敛）。 |
| **生成器** | `build-system-prompt.py` 在拼装 **内联** SubAgent 段时，应**嵌入**与 `core-rules-subagent.xml` **等价**的文本块（从同一源生成/抽取），**禁止**在 Limited 专段中再嵌一整份主编排用 `core-rules`；若短期无法抽取，**必须在 PR 说明中显式记为技术债**并**不得**将 Limited 的「全量内联 core-rules」算入 O25 完成度。 |
| **Token DoD 口径** | **分平台写**（§2.3、§7）：Full 的「SubAgent 降载」在 **O25 指标**中体现；Limited 的降幅用 **L1/整 prompt** 的 before/after，**不**用 O25 子块强行凑数。 |

**Rejected alternative**：不记录为 v1.1 选项——「O25 对 Limited 也记同一套收益」**除非**已落地生成器子块替换并有单测，否则从本施工单**剔除**，避免与 §9.2 冲突。  

---

### 2.3 Token 验收 SOP（吸收 Review F4 + 主控/ V1.1 B4.5）

以下为 **PR-7 合入门禁** 的**最低**可复现条；**禁止**以「行数/字符**单独**」作为主证据满足 ≥25%（可作为附录辅助）。

| 项 | 定版内容 |
|----|----------|
| **基线** | Git 引用：**PR-6 合入后的 `main` tip**，在 PR-7 描述中粘贴 **基线 commit SHA**；若 PR-7 分支上对比，**注明** cherry-pick 点。 |
| **对比** | 同一 **PR-7 分支** tip vs 基线 **同路径构建** 下的 prompt 规模（见下「统计范围」）。 |
| **环境** | **P3 / `fanout_mode=complex-arbitrated`** 且 `env_subagent=true` 的**合成或真实**工作流一回合（**至少 1 个固定** case；推荐再跑 `eval-cases/seed-10` 子集作回归，但 **≥25% 主数** 来自下面固定 P3 complex case）。 |
| **工具** | **定版 T1**：使用与团队一致的 tokenizer（例如对 Claude 系可用 **cl100k_base** 近似 + 在报告中注明近似；或 Cursor/平台导出 token 若可）。**禁止**仅用 `wc -c` / `wc -l` 作为**唯一**达标证明。 |
| **统计范围（须写进 PR 正文）** | 对比 **同一份** 下列拼接串的 **input token**（**不含** model 输出，**含** P3 本步注入的 `subagent` 多段，若该 case 触发）：(a) 主编排可观测 system+user 边界按你们平台定义；若只能拿到「整包 prompt」，则 **before/after 边界须一致**。**O25 专门对比**：同一 SubAgent 调用在基线为 `load core-rules.xml` 全量、实现后为 `load core-rules-subagent.xml` 时，**该子串**的 token 差。 |
| **门栏** | **P3 complex 路径**（定义：上述固定 case 配置）**input token 合计**相对基线 **≥ 25%** 下降。另：**Claude、Qwen、Doubao** 各 ≥1 个非零分 case 的**质量**不肉眼降级（与主控 PR-7 矩阵一致；**O25 不减分** 不计入 Limited 子 Agent 硬指标）。 |
| **证据形态** | PR 附件：表格「指标 | 基线 tokens | PR-7 tokens | 降幅% | tokenizer | case id | 备注」. |

---

## 2.4 非目标与既有硬约束

1. **OVHSC / Challenger / Arbiter 业务语义** 不删句（O24 仅拆文件+条件 load）。  
2. **H2**：若曾降级 `<phase-abort>`，O15 不强制宏面收敛，改等价显式步（主控 §3 H2）。  
3. 其余见 v1.0 精神：**不**做 O20、**不**改 4a/4b/4c 业务语义。  

---

## 3. 分阶段实施序

```text
B4   O16（键名，优先子树）→ O15（p3 面）
B4.5 O23（essential+dsl+聚合）→ O24（reasoning 拆）→ O25（subagent + invoke）
B5   O19+（shared-input-guard）→ O11+（按 §2.1 改入口与 p5/p6 触达）
```

依赖与 v1.0 同：O25 在 O23 定边界之后；O24 与 `build-system-prompt` 同批可测。  

---

### 3.1 O15

与 v1.0 同：**A** 档 Escalation 表 + 各档保留**逐字** `<phase-abort>`；**B** 为 rejected unless 有 LLM 稳定性数据。验收：`check-phase-abort-structure.sh` + P3 eval 零分不增。  

---

### 3.2 O16 — Deep-dive 主子键名

**目标**：`functionality-deep-dive/core/default-config.yaml` 使用 `deep_dive_optional_artifacts.*` 与主链 `config-schema.yaml` 对齐；`emit_*` 下线路径明确。  

#### 3.2.1 兼容分岔（吸收 Review F5 + V1.1 §4.3）

| 分岔 | 采用条件 | 必须完成的动作 |
|------|----------|----------------|
| **A**（**默认/推荐**，若可证明**无**须保留的线上 / 多团队**旧** deep-dive 工作区只认 `emit_*`） | 在 PR-7 描述中写明 **显式前提**：「**已确认**无**需迁移**的、仍依赖 `emit_*` 的存量配置」 | 删除或清空 `config-schema` 的 `known_legacy_aliases` 中**仅** deep-dive 相关映射；**全**仓库改新键；CI `check-config-schema` 全绿。 |
| **B** | 若前提 A **不**成立 | **读侧** 保留一版 `known_legacy_aliases`（V1.1 写新读旧）+ **可选** `scripts/migrate-deep-dive-config-keys.py` 幂等将 `emit_*` 迁移为新键；DoD 中增加「**跑迁移脚本** + 旧 key 工作区 1 例**回放**」 |

**定版**：实施前在评审单勾选 A **或** B；**不得**长留 v1.0 式「或可选迁移」**而不选**。  

**📌 PR-7 实施已选 A**（决策记录 / 2026-04-22 / 触达表 §A 已自检 4 项前提）：

- **决策依据**：本仓库内 `emit_*` 仅在 4 个文件 / 7 处 grep 命中，均为本 v4.x 主链文件；无跨仓库 / 跨团队 / 跨 release channel 的存量「只认 emit_*」工作区配置；v3-legacy 已物理归档（PR-1 O3）且不引用 emit_*。
- **统一二级键名（定版 K1）**：以主端 `core/default-config.yaml` 为权威，三键固定为 `environment_factor_report` / `deep_dive_topology` / `concurrency_analysis_report`。子端 emit_* → 主端键名映射如下（**A 档无需保留 alias，只是迁移对照表**）：

  | 子端旧键（删除） | 主端新键（保留） |
  |------|------|
  | `emit_environment_factor_report` | `deep_dive_optional_artifacts.environment_factor_report` |
  | `emit_topology_report` | `deep_dive_optional_artifacts.deep_dive_topology` |
  | `emit_concurrency_report` | `deep_dive_optional_artifacts.concurrency_analysis_report` |

- **对应触达**：见 §6 / §A 中 `O16-A` 标记的 3 项改写（`functionality-deep-dive/core/default-config.yaml` 3 行 + `functionality-deep-dive/phases/{f1,f2,f3}.md` 6 行 + `core/config-schema.yaml` 3 行 alias 清空）。
- **CI 守门**：`scripts/check-config-schema.sh`（既存）必须全绿；新增 `scripts/check-load-targets.sh`（§5.1）不直接管键名，但兜底「无残留 emit_* 在主链 phase」。本 PR 内可补一条 grep 守门 `! grep -rn "emit_environment_factor_report\|emit_topology_report\|emit_concurrency_report" mobile-qa-workflow/{core,phases,functionality-deep-dive/core,functionality-deep-dive/phases} 2>/dev/null`，命中即 fail。

---

### 3.3 O23 — `core-rules` 拆分

#### 3.3.1 聚合方式 **定版 D-AGG-1**（吸收 Review F6）

| 项 | 定版 |
|----|------|
| **唯二可编辑源** | `core/core-rules-essential.xml`、`core/core-rules-dsl-reference.xml`（分块内容与 v1.0 表意一致：essential = mandate+工作流结果协议+human-review 等**非**大标签表；dsl = `supported-tags` + `available-agents` 等长表）。 |
| **`core-rules.xml` 全量** | **由脚本生成**（建议 `scripts/sync-core-rules-aggregate.py` 或等效），**在 CI 中校验** `core-rules.xml` 与 `merge(essential, dsl)` 的**内容契约**（例如对规范化空白后的 digest，或**脚本自身为唯一写入口**、PR 中禁止手改 `core-rules.xml`）。**rejected**：长期手改三份、三者漂移。 |
| **聚合根结构** | **定版 G1**：生成后的 `core-rules.xml` 为**单一合法 XML 根**（如 `<mobile-qa-dsl-packet version="1">`），**顺序**先 essential 子树根、再 dsl 子树根，**不**用「两条 `<load>` 占位假 XML」冒充单文件。 |
| **生成器** | `build-system-prompt.py` 读取**全量**规则时，**定版**为：直接 `read("core-rules.xml")` **单路径**。`core-rules.xml` 作为 **D-AGG-1** 的唯一聚合产物，由脚本生成并受 CI 校验；**禁止**在生成器中再读 `essential+dsl` 拼接第二套逻辑，**禁止**再自行从旧 monolith 第三套推断。 |
| **Phase 首步** | **仅** `load essential`；在出现 `invoke-subagent` 的 step 若需标签表，**前插** `load core-rules-dsl-reference.xml`（与 v1.0 同）。 |
| **SKILL / 历史文档** | 仍可引用 `core-rules.xml` **单一**全量；由聚合脚本保证与两源一致。 |

**Rejected alternative D-AGG-0**：`core-rules.xml` 为「两条 `<load>` 指令」的伪 XML 文件 — **不采用**。  

📌 **PR-7 实施已落地（2026-04-22 / O23 完成）**：

| 项 | 落地形态 |
|----|----------|
| 唯二可编辑源 | `mobile-qa-workflow/core/core-rules-essential.xml`（59 行）+ `mobile-qa-workflow/core/core-rules-dsl-reference.xml`（237 行） |
| 聚合脚本 | `mobile-qa-workflow/scripts/sync-core-rules-aggregate.py` 提供 `--check` / `--write` 双模式 |
| 聚合产物 | `mobile-qa-workflow/core/core-rules.xml`（296 行 / **AUTOGEN**，与 PR-6 baseline 字节等价 / build-system-prompt.py + system-prompt.md 零变动） |
| 聚合策略 | **G1' 扁平合并**：essential 用唯一占位 `<!-- AGG-INSERT: core-rules-dsl-reference.xml -->` 标记 dsl 注入点；脚本读两源 → 剥根 + 跳首注释块 → marker 替换 → 再统一包 `<core-rules id="mobile-qa/core-rules.xml" name="...">` 根。**不**新增 `<mobile-qa-dsl-packet>` 包裹元素（避免破坏 build-system-prompt.py 的 `^\s*<X\b` 抽取契约 + system-prompt-sync 守门）。G1 表中"essential 子树根 + dsl 子树根"的描述以本扁平方案落地——根唯一、顺序合规（essential 头 → dsl supported-tags → essential 尾）、生成器单路径读 `core-rules.xml`，与 G1 立法目标完全一致。 |
| Phase 首步 | **本次 PR 内 O23 仅交付源文件 + 聚合脚本 + CI 守门**；§6 表中"phase 首步改 essential / invoke 内按需前插 dsl-reference"作为后续小段独立提交（§3.5 / §6 行号触达），便于 review 切片。聚合产物 `core-rules.xml` 已与 PR-6 baseline 字节相同，所以现存 phase 文件中的 `<load core-rules.xml>` 在 O23 单测节点零回归。 |
| CI | **Check 19**（`schema-check` workflow）：`python3 mobile-qa-workflow/scripts/sync-core-rules-aggregate.py --check` / **error 起步**。任何手改 `core-rules.xml` 或两源漂移都会被拦下并提示 `--write` 修复指引。Check 18 编号继续保留给 GEN-PR7 的 `check-load-targets.sh`。 |
| 单测 | `mobile-qa-workflow/scripts/tests/test_sync_core_rules_aggregate.py`（12 用例）覆盖 `--check` 通过/`--write` 幂等/三类漂移检测/AUTOGEN 头/根重命名/4 处 build-system-prompt 抽取锚点/4 空格基础缩进/与已提交聚合产物字节相同。`Check 14`（`unittest discover`）一次性覆盖 33 个用例（含 build-system-prompt 16 + sync 12 + p3-reentry 5）。 |


---

### 3.4 O24 — `reasoning-chain` 拆分

**文件**：`reference/reasoning-chain-core.md` + `reasoning-guide-functional|ui|network|compat.md`（**OVHSC 等一句不减，挪至 core**）。  

#### 3.4.1 与 `issue_card` 的字段与 **路由真值**（吸收 Review F7）

模板见 [`templates/issue-card.md`](../../templates/issue-card.md)：

- **主分类**行：`- **主分类**: [一级分类] > [二级分类]`
- **次分类**、**分类置信度** 为辅助。

**P3 `step 5` 的规范算法（定版 R24-1）**：

1. 从已加载的 `issue_card` 解析**一级主题**：取 **「主分类」** 中第一个 `>` 左侧的 **一级分类** 子串，去空格。  
2. 映射到 guide 文件（**大小写/同义词在实现时列死一张表，禁止实现者自创**）：

| 一级主题（**包含**即匹配，建议优先整词） | 加载的专项 guide |
|----------------------------------------|------------------|
| `功能` 或 功能* | `reasoning-guide-functional.md` |
| `UI` / `UI/UX` / 交互 | `reasoning-guide-ui.md` |
| `网络` | `reasoning-guide-network.md` |
| `兼容` 或 兼容性* | `reasoning-guide-compat.md` |

3. **未命中**（性能 / 安全 / Crash/ANR/稳定性等 **或** 解析失败 **或** 主分类整行缺失）：**`load` `reasoning-chain-core.md` 仅**；再 **`load` 四份 guide 全文合并块** 作为 **Fallback-Full**（与 V1.1「必要时 fallback 全量」一致）。**rejected**：未命中时随机选一 guide。  
4. **多标签**（`次分类 != 无` 且其次分类**一级主题**与主分类**一级主题**不一致，且 **分类置信度 = High**）：**R24-1b** 定版为：仍按**主分类** 执行 §3.4.1 第 2 步；在 PR 的「风险说明」中注明「争议场景按主分类优先，后续如需更细分歧义治理，再单独引入权重字段/规则」；**不**在 v4.2 PR-7 引入新 schema 字段。  
5. **`reference/reasoning-chain.md`（向后兼容）** 定版 **C1**：保留为 `core` + 四 guide 的**静态拼贴**（同顺序），顶注释 `<!-- 聚合，PR-7 后请优先使用分文件 -->`；`build-system-prompt` 的 L3 以 **与 P3 相同** 的分类逻辑生成（避免 **Limited 与 Full** 再分叉；审查点）。  

📌 **PR-7 实施已落地（2026-04-22 / O24 完成）**：

| 项 | 落地形态 |
|----|----------|
| 唯五可编辑源 | `mobile-qa-workflow/reference/reasoning-chain-core.md`（OVHSC 五步 + 输出格式 + 置信度规则 + `## 分类专项推理引导` 章节头 + `<!-- AGG-INSERT-GUIDES -->` 占位）+ `reasoning-guide-{functional,ui,network,compat}.md`（每文件 file-level header + 加载入口说明 + `<!-- AGG-INJECT-START -->/<!-- AGG-INJECT-END -->` 区块包裹的 `### XX 类问题` 子节）|
| 聚合脚本 | `mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py` 提供 `--check` / `--write` 双模式；注入顺序固定 `functional → ui → network → compat`（与 R24-1 真值表行序一致）|
| 聚合产物 | `mobile-qa-workflow/reference/reasoning-chain.md`（214 行 / **AUTOGEN**，body 部分与 PR-6 baseline 字节等价 / build-system-prompt.py L3 + system-prompt.md 零变动） |
| 聚合策略 | **C1 扁平拼贴**：core 用唯一占位 `<!-- AGG-INSERT-GUIDES -->` 标记 4 guide 注入点；脚本读 5 源 → 剥 core 首部说明注释块 → 抽取 4 guide 的 INJECT body → 用单空行连接 → marker 替换 → 加 AUTOGEN 头。各 guide 文件中区块外的 `# Reasoning Guide ...` 标题与「加载入口」说明仅供独立加载入口阅读，**不**进入聚合产物（避免内容重复与 build-system-prompt L3 抽取混淆）。 |
| Phase 替换 | **本次 PR 内 O24 仅交付源文件 + 聚合脚本 + CI 守门**；§3.4.1 R24-1 算法对应的 `phases/p3-root-cause.md` 4 处 `<load reasoning-chain.md>` 替换为「`core` + 命中 guide / 未命中 fallback」逻辑作为后续小段独立提交（§6 行号触达）。聚合产物 `reasoning-chain.md` 已与 PR-6 baseline body 字节相同，所以现存 `<load>` 在 O24 单测节点零回归。 |
| CI | **Check 20**（`schema-check` workflow）：`python3 mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py --check` / **error 起步**。任何手改 `reasoning-chain.md` 或 5 源漂移都会被拦下并提示 `--write` 修复指引。Check 18 编号继续保留给 GEN-PR7 的 `check-load-targets.sh`，Check 19 = D-AGG-1（O23）。|
| 单测 | `mobile-qa-workflow/scripts/tests/test_sync_reasoning_chain_aggregate.py`（10 用例 + subTest 4 guide）覆盖 `--check` 通过/`--write` 幂等/三类漂移检测（含 4 guide 单独漂移子用例）/AUTOGEN 头/文件级标题保留/marker+inject 标签零残留/3 处 build-system-prompt L3 抽取锚点/4 guide 子节固定顺序/与已提交聚合产物字节相同。`Check 14`（`unittest discover`）一次性覆盖 44 个用例（含 build-system-prompt 16 + sync-core-rules 12 + sync-reasoning-chain 11 + p3-reentry 5）。|

---

### 3.5 O25

与 §2.2 同；**替换** `phases/p3`/`p4` 内 `invoke-subagent` 的 load；**不**动 phase 首步 essential（**除非** 该段 SubAgent 不需要 dsl 表，仍仅 essential+subagent）。单测/ eval 不回归为门禁。  

📌 **PR-7 实施已落地（2026-04-22 / O25 完成）**：

| 项 | 落地形态 |
|----|----------|
| 新增源文件 | `mobile-qa-workflow/core/core-rules-subagent.xml`（44 行 / 含 `<subagent-context>` 5 条 + `<subagent-output-protocol>` 6 条）。仅承载子对话隔离 SubAgent 必备的最小契约：身份/输入约定/输出形态/置信度量化/宏调用边界；**不**收录 `<agent-taxonomy>` / `<WORKFLOW-RULES>` / `<supported-tags>` / `<human-review-protocol>`（由父对话承担）。 |
| Phase 替换 | **20 处** invoke-subagent 内 `<load core-rules.xml>` → `<load core-rules-subagent.xml>`：`phases/p3-root-cause.md` × 6（投诉/反诉路径 invoke 全集）、`phases/p4-fix-design.md` × 7（fix-proposer × 4 + challenger × 2 + arbiter × 1）、`phases/p5-fix-impl.md` × 1（coder-agent invoke）、`functionality-deep-dive/phases/{f1,f2,f3}.md` × 1 each、`f4-isolation-debate.md` × 2（投诉/反诉）、`f5-defensive-fix-design.md` × 1。**与 §A.1 标记的 "O25 命中" 行行对齐**（O15 后 p3 行号已轻微偏移 78/87/116/122/128/138 → 100/109/138/144/150/160，路径策略不变）。|
| Phase 范围边界 | 仅替换**单引号**（`target='...'`，invoke-subagent.subagent_prompt 内）路径；phase 首步**双引号** `<load target=".../core-rules.xml" ...>` 形态全部保留 → 留作后续 essential 小段独立提交（与 O23 / O24 节奏一致，便于 review 切片）。`phases/p2-spec-definition.md` L128 invoke `curator` 内 load 按 §A.1 设计走 essential，不在 O25 范围，本 PR 不动。 |
| Limited 平台 | **本次 PR 内不为 Limited 单 prompt 内嵌 subagent 等价文本块**（属 GEN-PR7 §4 第 3 条任务，将在 build-system-prompt.py 拼装时落地）。Limited 平台 `env_subagent=false` 时 invoke-subagent 整体不执行，phase 内 `<load core-rules-subagent.xml>` 不影响 Limited 行为；O25 token 收益**仅**统计 Full 路径，与 §2.2 表口径一致。 |
| CI | **Check 21**（`schema-check` workflow）：`bash mobile-qa-workflow/scripts/check-subagent-load-target.sh` / **error 起步**。守门 8 个 O25 phase 文件中 invoke-subagent 内 (a) 不得回流 `core-rules.xml`（单引号形态），(b) 命中数 = 期望 20 / 20，(c) p2 L128 essential 边界保持。Check 18 编号继续保留给 GEN-PR7 的 `check-load-targets.sh`，Check 19 = D-AGG-1（O23），Check 20 = D-AGG-2（O24）。 |
| 单测 | 现有 44 用例（build-system-prompt 16 + sync-core-rules 12 + sync-reasoning-chain 11 + p3-reentry 5）一次性回归全绿；O25 不改 build-system-prompt.py / system-prompt.md（system-prompt.md 仅含 1 处 `core/core-rules.xml` 路径串，属 D-AGG-1 聚合产物的标识引用，非 invoke-subagent 内 load）。Check 21 替代单测覆盖路径合规性。 |

---

### 3.6 O19+

`shared-challenger-base` / `shared-arbiter-base`：删除重复入参，改为 `<load target="mobile-qa-workflow/agents/shared-input-guard.md"/>` 并写死 `required_field=confidence_input` / `base_score`。与 V1.1 范文一致。  

📌 **PR-7 实施已落地（2026-04-22 / O19+ 完成）**：

| 项 | 落地形态 |
|----|----------|
| 新增 | `mobile-qa-workflow/agents/shared-input-guard.md`（46 行）：含写死取值表（`confidence_input` / `base_score` 二选一）、参数化校验前置条件 3 条（缺失 / 非数值 / 其它入参 D5 范围口径）、失败语义（**非**业务不确定 / 不触 human-review-protocol / 调用方修复后重试）、与 `check-subagent-params.sh`（调用方端）+ Limited GEN-PR7 的关系说明。 |
| 改写 | `agents/shared-challenger-base.md`：原 18 行「入参完整性校验（v4.1 / C2 wrapper）」段 → 改为 6 行 preamble +「`本 wrapper 写死 required_field = confidence_input`」+ `<load shared-input-guard.md>`。其它段（输入契约 / 统一执行协议 / 维度集 / 输出结构 / 置信度影响格式）一字未动。|
| 改写 | `agents/shared-arbiter-base.md`：同构改写，preamble 写死 `required_field = base_score`。其它段（输入契约 / 统一裁定协议 / 收敛系数 / 统一置信度口径 / 输出结构）一字未动。|
| 净身段 | shared-challenger-base.md：92 → 80 行（净减 12 行 / 13%）；shared-arbiter-base.md：84 → 72 行（净减 12 行 / 14%）；新增 shared-input-guard.md 46 行 = **净减 -22 行/源消除双写漂移面**。|
| CI | 现有 `check-subagent-params.sh`（调用方端 invoke prompt 必传 `confidence_input` / `base_score`）继续生效；本 PR 不新增独立 check（路径可达性纳入 GEN-PR7 的 `check-load-targets.sh` / Check 18，subagent.xml 路径合规已由 Check 21 守门）。 |
| 单测 | 现有 44 用例全绿（build-system-prompt 16 + sync-core-rules 12 + sync-reasoning-chain 11 + p3-reentry 5）；O19+ 不改 build-system-prompt.py 抽取锚点（system-prompt.md 字节相同）。 |

---

## 4. GEN-PR7（`build-system-prompt.py`）

1. L1：从 **essential**（+ 必要时 dsl 摘要句）出，不恢复 monolith 手抄。  
2. L3：O24 逻辑与 **§3.4.1** 同构；`--mode=full` 若需「全量推理参考」，**定版**为与 **C1** 一致，即 `core` + 四 guide 的静态拼贴。  
3. O25 + Limited：见 **§2.2** 最后一条；**嵌入** subagent 等价位块。  
4. 单测 + `check-system-prompt-sync.sh` 全绿。  

---

## 5. CI 与质量门禁

### 5.1 必做 **`scripts/check-load-targets.sh`**（吸收 Review F3）

| 项 | 定版 |
|----|------|
| **必做** | 解析主链 `phases/**/*.md`、主链 `agents/**/*.md`（**不含**子目录 archive 可配置排除）、主链 `reference/**/*.md`、`core/**/*.{xml,md}`、`SKILL.md`，以及 `functionality-deep-dive/phases/**/*.md`、`functionality-deep-dive/agents/**/*.md`、`functionality-deep-dive/reference/**/*.md` 中 **`<load target="...">` 与 `target='...'`** 路径 |
| **规则** | 路径以 `mobile-qa-workflow/` 为前缀时**转为** 仓库内相对 `repo_root` 的路径；`test -f` **不存在则 exit 1**；含 **对 `core-rules-subagent.xml`、新 `reasoning-*.md`** 的**可达性** |
| **集成** | `.github/workflows/qa-workflow-schema-check.yml` 新增 **Check 18**（名由你们定），**error 起步**（与 review「至少 warning」相比，v1.1 采用 **error** 以免漂移漏网） |
| **第二层（可选）** | 原「essential 首步比例 / subagent 不加载全量」的启发式，可为 **warning** |

既存 `check-subagent-params`、`check-phase-abort-structure` 保持。  

---

## 6. 文件级总览（开 PR 前已用 grep 在 main / PR-6 合入后基线刷成"精确触达表"，详见 §A）

> **基线**：`feat/qa-workflow-v4.2-pr7-structural-convergence` 切出点 = `7ae366b feat(qa-workflow): v4.2 PR-6 D14 #2 inline 退役 + system-prompt 自动构建`（PR-1 ~ PR-6 累积）。
> **数据采集时间**：2026-04-22。
> 下表是"按操作分组"的总览，逐项触达行号见 **§A 精确触达表**。

| 操作 | 路径 | 触达点数 | 注 |
|------|------|---------|-----|
| 新增 | `core/core-rules-essential.xml`（70 行内）+ `core/core-rules-dsl-reference.xml`（215 行内） | 2 文件 | §3.3.1 D-AGG-1 唯二可编辑源 |
| 新增 + 改写脚本 | `scripts/sync-core-rules-aggregate.py` + 单测 | 1 + 1 | §3.3.1 D-AGG-1 唯一写入口 |
| 改写（脚本生成） | `core/core-rules.xml` | 1 | §3.3.1 G1 单根 XML 聚合 |
| 新增 | `core/core-rules-subagent.xml`（~30 行） | 1 | §3.5 / §2.2 Full 平台 SubAgent 专用 |
| 新增 | `reference/reasoning-chain-core.md` + 4 个 `reasoning-guide-{functional,ui,network,compat}.md` | 5 文件 | §3.4 |
| 改写 | `reference/reasoning-chain.md` 顶部加聚合 + deprecate 注释（保留拼贴 = §3.4.1 C1） | 1 | §3.4.1 C1 兼容入口 |
| 新增 | `agents/shared-input-guard.md`（~10 行） | 1 | §3.6 / §2.1 |
| 新增 | `agents/coder-workflow.md`（约 100 行）+ `reference/contract-checklist-spec.md`（约 80 行） | 2 | §2.1 E1 拆三件下游文件 |
| 改写 | `agents/coder-agent.md`：保留入口必备块 + 新增两条固定顺序 `<load>` 子文件 | 1 | §2.1 E1 入口必备 |
| 改写 | `agents/shared-arbiter-base.md`：删除入参校验段，改 `<load shared-input-guard.md>` | 1 | §3.6 |
| 改写 | `agents/shared-challenger-base.md`：同上 | 1 | §3.6 |
| 改写 | `phases/p3-root-cause.md`：phase 首步（line 20）改 essential；6 处 invoke-subagent 内 `<load core-rules.xml>` (lines 78/87/116/122/128/138)：投诉/反诉路径**保留 essential**，需要 `<available-agents>` 表的 invoke（即调主 challenger/arbiter 包装层）按需**前插** dsl-reference | **7** 个 core-rules.xml load 触达点 | §3.3.1 phase 首步 + §3.5 |
| 改写 | `phases/p4-fix-design.md`：phase 首步（line 21）改 essential；7 处 invoke-subagent 内 `<load core-rules.xml>` (lines 44/57/62/84/89/94/104) 同上规则 | **8** 个 core-rules.xml load 触达点 | §3.3.1 + §3.5 |
| 改写 | `phases/p5-fix-impl.md`：phase 首步（line 20）改 essential；invoke 内 `<load core-rules.xml>` (line 85) → essential。**注**：line 87 / line 99 的 `<load coder-agent.md>` 已是 §2.1 E1 唯一入口形态，本 PR 无需新增/删除任何 load，仅靠入口文件内部添加固定顺序两条 `<load>` 即生效。 | 2 个 core-rules.xml load 触达点 + 0 个 coder-agent load 增量 | §3.3.1 + §2.1 |
| 改写 | `phases/p1-intake.md`：phase 首步（line 19）改 essential | 1 处 | §3.3.1 |
| 改写 | `phases/p2-spec-definition.md`：phase 首步（line 19）改 essential；invoke 内（line 128）按需保留 essential | 2 处 | §3.3.1 |
| 改写 | `phases/p6-verification.md`：phase 首步（line 22）改 essential | 1 处 | §3.3.1 |
| 改写 | `functionality-deep-dive/core/workflow.xml`：line 18 phase 首步改 essential | 1 处 | §3.3.1 |
| 改写 | `functionality-deep-dive/phases/f1-context-reconstruction.md`：phase 首步 (line 19) + invoke 内 (line 27) | 2 处 | §3.3.1 + §3.5 |
| 改写 | `functionality-deep-dive/phases/f2-state-topology.md`：phase 首步 (line 19) + invoke 内 (line 27) | 2 处 | §3.3.1 + §3.5 |
| 改写 | `functionality-deep-dive/phases/f3-temporal-correlation.md`：phase 首步 (line 18) + invoke 内 (line 26) | 2 处 | §3.3.1 + §3.5 |
| 改写 | `functionality-deep-dive/phases/f4-isolation-debate.md`：phase 首步 (line 21) + 2 处 invoke (lines 29/44) | 3 处 | §3.3.1 + §3.5 |
| 改写 | `functionality-deep-dive/phases/f5-defensive-fix-design.md`：1 处 invoke (line 35)；该文件无 phase 首步 essential load | 1 处 | §3.5 |
| 改写 | **O16-A**：`functionality-deep-dive/core/default-config.yaml`：3 个 `emit_*` → `deep_dive_optional_artifacts.*` | 1 文件 / 3 行 | §3.2.1 选 A |
| 改写 | **O16-A**：`functionality-deep-dive/phases/{f1,f2,f3}.md`：6 处 `<check if="emit_..."` → 主端键 | 3 文件 / 6 行 | §3.2.1 选 A |
| 改写 | **O16-A**：`core/config-schema.yaml`：清空 `known_legacy_aliases` 中 deep-dive 相关 3 行 | 1 文件 / 3 行 | §3.2.1 选 A |
| 改写 | `phases/p3-root-cause.md` step 5 三档升级早退面（O15）：保留逐字 `<phase-abort>`（已是 PR-3' 已落 / O21 宏体），仅整理路径常量化 | 3 处 phase-abort | §3.1 A 档 |
| 新增 | `scripts/check-load-targets.sh` | 1 | §5.1 必做 / Check 18 / error 起步 |
| 改写 | `.github/workflows/qa-workflow-schema-check.yml`：注册 Check 18 | 1 | §5.1 |
| 改写 | `scripts/build-system-prompt.py` + `scripts/tests/test_build_system_prompt.py` | 1 + 1 | §4 GEN-PR7 |

**触达面自检结论**（实施前已确认）：

- ✅ **§2.1 P5 路径已天然合规**：`phases/p5-fix-impl.md` line 87（invoke）+ line 99（降级）均仅 `<load coder-agent.md>`，**无**额外的 `coder-workflow.md` / `contract-checklist-spec.md` 单独 load——只需在拆三件后让 `coder-agent.md` 入口再补两条固定顺序 `<load>` 即可，不破坏 P5 既有调用。
- ✅ **P6 例外路径不存在**：当前 `phases/p6-verification.md` 仅 1 处 `<load core-rules.xml>`（首步），**未**单独 load `coder-agent.md` 或 `contract-checklist-spec.md`；§2.1 P6 例外是**预留接口**，本 PR 不为其新增触达点。
- ✅ **§3.2.1 选 A 的 4 项前提全部满足**：
  - (a) 子端 `emit_*` 仅在仓库内 4 个文件引用（`functionality-deep-dive/core/default-config.yaml` + f1/f2/f3 各 2 处 = 7 处 grep 命中），无跨仓库 / 跨团队的存量持久化配置；
  - (b) v3-legacy 老会话归档（PR-1 O3）已物理迁移至 `functionality-deep-dive/agents/archive/v3-legacy/`，不引用 emit_*；
  - (c) `core/config-schema.yaml` 的 `known_legacy_aliases` 块**仅**为 deep-dive 漂移而存在，整体可清空（不影响其他键）；
  - (d) 主端 `core/default-config.yaml` 的 `deep_dive_optional_artifacts` 三个二级键（`environment_factor_report` / `deep_dive_topology` / `concurrency_analysis_report`）作为唯一权威命名继承使用。**统一定版**：子端键名按主端定版替换（详见 §3.2.1）。
- ✅ **`<phase-abort>` / `<phase-complete>` 已是仓库主语**：phases 主链 6 文件 + `core/core-rules.xml` 内已用 `<tag>` 完整定义两宏（PR-3' / O21），O15 改写直接用现有宏。

---

---

## 7. PR-level DoD（v1.1 可执行）

- [ ] **§2.1** P5 仅经 `coder-agent.md`；P6 仅 checklist 时仅 `contract-checklist-spec.md`。  
- [ ] **§2.2** Full SubAgent 使用 `core-rules-subagent.xml`；Limited 不生称矛盾收益。  
- [ ] **§2.3** PR 文内**表格** + 基线 SHA + 固定 P3 complex case + **tokenizer 名** + **≥25%**（**非**行数主证）。  
- [ ] **§3.2.1** 选 A **或** B 并满足其表。  
- [ ] **§3.3.1** 三文件关系唯一；CI 对聚合有校验。  
- [ ] **§3.4.1** 已路由 case 在 PR 中**举例** 2+1（命中 guide / fallback / 边界）。  
- [ ] **§5.1** Check 18 绿。  
- [ ] **O15–O19+–O23–O25** 与 **GEN-PR7** 完成。  
- [ ] 跨平台：**Cursor + Trae + 1 Limited**（与主控 §5）.  
- [ ] eval 全量 + `seed-10` 不回归。  
- [ ] **删除 v1.0 不再使用的矛盾句**；本 v1.1 为**唯一**施工依据。  

---

## 8. 回滚

分块 revert；**O16** 若动 alias，revert 时恢配置；**D-AGG-1** 若上脚本，revert 即恢复单文件 `core-rules.xml` 手改基线。  

---

## 9. 时间盒与砍 scope

与 v1.0 同：不足则 **O23+O25+O24** + 最小 O11+（**仍守 §2.1 入口**）；O15/O16 可 **PR-7.1**；**不**删 §2.3/§5.1/§2.1/§2.2/§3.2.1 的**定版**条款于「缩 scope」之外。  

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-04-22 | 首版；方向正确、口径未闭合 |
| v1.1 | 2026-04-22 | 吸收 [REVIEW-2026-04-22](./pr-7-structural-convergence-token-and-modularization-REVIEW-2026-04-22.md)；唯一规范 + CI/Token/O16/聚合/O24 真值 + O25/ Limited |

---

## 附录 §A · 精确触达表（2026-04-22 / HEAD = `7ae366b` PR-1~PR-6 累积基线）

> 已在仓库 HEAD 上跑 grep；下表逐行可重放。
> **统计范围**：仅主链 `mobile-qa-workflow/{core,phases,agents,reference,functionality-deep-dive}/**` + `scripts/`；construction-plans 历史文档 / archive 内引用**不计入**改写触达，仅作上下文参考。

### §A.1 `<load target="…/core/core-rules.xml">` 触达点（O23 改 essential / O25 改 subagent.xml 的入口）

| 文件 | 行号 | 调用语境 | 改写策略 |
|------|------|----------|---------|
| `phases/p1-intake.md` | L19 | phase 首步 | → `core-rules-essential.xml` |
| `phases/p2-spec-definition.md` | L19 | phase 首步 | → `core-rules-essential.xml` |
| `phases/p2-spec-definition.md` | L128 | invoke `curator` 内 | → `core-rules-essential.xml`（subagent 不需要 `<available-agents>`） |
| `phases/p3-root-cause.md` | L20 | phase 首步 | → `core-rules-essential.xml` |
| `phases/p3-root-cause.md` | L78 | invoke `investigator` 内 | **O25 命中**：Full → `core-rules-subagent.xml`；Limited 不变 |
| `phases/p3-root-cause.md` | L87 | invoke `challenger` 内 | **O25 命中**：Full → `core-rules-subagent.xml` |
| `phases/p3-root-cause.md` | L116 | invoke `investigator`（fan-out 第 2 个）| **O25 命中** |
| `phases/p3-root-cause.md` | L122 | invoke `investigator`（fan-out 第 3 个）| **O25 命中** |
| `phases/p3-root-cause.md` | L128 | invoke `challenger`（fan-out 后）| **O25 命中** |
| `phases/p3-root-cause.md` | L138 | invoke `arbiter` | **O25 命中** |
| `phases/p4-fix-design.md` | L21 | phase 首步 | → `core-rules-essential.xml` |
| `phases/p4-fix-design.md` | L44/L57/L84/L89 | invoke `fix-proposer` × 4 | **O25 命中** |
| `phases/p4-fix-design.md` | L62/L94 | invoke `challenger` × 2 | **O25 命中** |
| `phases/p4-fix-design.md` | L104 | invoke `arbiter` | **O25 命中** |
| `phases/p5-fix-impl.md` | L20 | phase 首步 | → `core-rules-essential.xml` |
| `phases/p5-fix-impl.md` | L85 | invoke `coder-agent` 内 | **O25 命中**：Full → `core-rules-subagent.xml` |
| `phases/p6-verification.md` | L22 | phase 首步 | → `core-rules-essential.xml` |
| `functionality-deep-dive/core/workflow.xml` | L18 | phase 首步 | → `core-rules-essential.xml` |
| `functionality-deep-dive/phases/f1-context-reconstruction.md` | L19, L27 | 首步 + invoke `deep-dive-context-analyst` | 首步 essential / invoke **O25 命中** |
| `functionality-deep-dive/phases/f2-state-topology.md` | L19, L27 | 首步 + invoke `deep-dive-structure-analyst` | 同上 |
| `functionality-deep-dive/phases/f3-temporal-correlation.md` | L18, L26 | 首步 + invoke `deep-dive-race-and-isolation-analyst` | 同上 |
| `functionality-deep-dive/phases/f4-isolation-debate.md` | L21, L29, L44 | 首步 + 2 个 invoke | 同上 |
| `functionality-deep-dive/phases/f5-defensive-fix-design.md` | L35 | 仅 1 个 invoke `defensive-fix-architect` | invoke **O25 命中** |

**汇总**：主链 6 phase + deep-dive workflow + 5 deep-dive phase = 共 **34 处** `<load core-rules.xml>`：
- **8 处** phase 首步 → 全量改 `core-rules-essential.xml`
- **26 处** invoke-subagent 内 → Full 平台改 `core-rules-subagent.xml`（**O25 关键收益面**）；Limited 平台仍是 essential（不动；§2.2）

### §A.2 `<load target="…/agents/coder-agent.md">` 触达点（O11+ §2.1 E1 入口规范）

| 文件 | 行号 | 语境 | 改写策略 |
|------|------|------|---------|
| `phases/p5-fix-impl.md` | L87 | step 5 invoke `coder-agent` 内 | **不动**（已是 §2.1 唯一入口） |
| `phases/p5-fix-impl.md` | L99 | step 5 降级模式 | **不动** |

> **关键发现**：仓库内**不存在**任何对 `coder-workflow.md` / `contract-checklist-spec.md` 的独立 load（验证：`grep -rn "coder-workflow.md\|contract-checklist-spec.md" mobile-qa-workflow/{phases,agents,functionality-deep-dive,core,reference}` 零命中）。E1 入口规范在 v1.1 建立后，**仅**通过修改 `agents/coder-agent.md` 内部即可生效，不破坏任何现有 phase 调用面。**P6 例外路径** (§2.1) 在本 PR 不引入。

### §A.3 `<load target="…/reference/reasoning-chain.md">` 触达点（O24 拆分入口）

| 文件 | 行号 | 语境 | 改写策略 |
|------|------|------|---------|
| `phases/p3-root-cause.md` | L56 | step 5 phase 主体 | 按 §3.4.1 R24-1 真值表替换为：先 load `reasoning-chain-core.md` + 按 `issue_card.主分类` load 对应 `reasoning-guide-{cat}.md`（未命中 → fallback-full） |
| `phases/p3-root-cause.md` | L80 | invoke `investigator` 内 | 同上规则；invoke 内的 R24-1 由调用方在 prompt 拼接时按主分类预解析 |
| `phases/p3-root-cause.md` | L118 | invoke `investigator` (fan-out 2) | 同上 |
| `phases/p3-root-cause.md` | L124 | invoke `investigator` (fan-out 3) | 同上 |
| `scripts/build-system-prompt.py` | L376-L379 (`build_l3_reasoning_toolbox`) | 生成器 | GEN-PR7 改造：与 P3 同构的分类逻辑；`--mode=full` 走 §3.4.1 C1 静态拼贴 |

**汇总**：4 处 phase 内 + 1 处生成器 = **5 处**改写触达。

### §A.4 子端 `emit_*` → 主端 `deep_dive_optional_artifacts.*` 触达（O16-A）

| 文件 | 行号 | 旧 | 新 |
|------|------|-----|-----|
| `functionality-deep-dive/core/default-config.yaml` | L18 | `emit_environment_factor_report: true` | `deep_dive_optional_artifacts.environment_factor_report: true` |
| `functionality-deep-dive/core/default-config.yaml` | L19 | `emit_topology_report: true` | `deep_dive_optional_artifacts.deep_dive_topology: true` |
| `functionality-deep-dive/core/default-config.yaml` | L20 | `emit_concurrency_report: true` | `deep_dive_optional_artifacts.concurrency_analysis_report: true` |
| `functionality-deep-dive/phases/f1-context-reconstruction.md` | L38, L43 | `emit_environment_factor_report` | `deep_dive_optional_artifacts.environment_factor_report` |
| `functionality-deep-dive/phases/f2-state-topology.md` | L38, L43 | `emit_topology_report` | `deep_dive_optional_artifacts.deep_dive_topology` |
| `functionality-deep-dive/phases/f3-temporal-correlation.md` | L38, L43 | `emit_concurrency_report` | `deep_dive_optional_artifacts.concurrency_analysis_report` |
| `core/config-schema.yaml` | L80–L83 | `known_legacy_aliases:` 块（仅 deep-dive 3 行） | 整段清空（保留键 + 空 dict / 或注释 deprecated） |

> **配套**：`core/default-config.yaml` L38–L43 的 v4.2 遗留 #1 注释段在 PR-7 实施时**删除或更新为「已收敛 / 历史」**（O16-A 显式收口）。

### §A.5 `<phase-abort>` / `<phase-complete>` 既有触达（O15 改写时**保留逐字**）

| 文件 | 行号 | 宏 / state | 备注 |
|------|------|------|------|
| `phases/p3-root-cause.md` | L65 | `<phase-abort state="Non-Bug" .../>` | step 1 早退 |
| `phases/p3-root-cause.md` | L103 | `<phase-abort state="Non-Bug" .../>` | step 4 早退 |
| `phases/p3-root-cause.md` | L153 | `<phase-abort state="..." .../>` | step 5 升级到 deep-dive 触发面（O15 主战场） |
| `phases/p3-root-cause.md` | L214 | `<phase-complete .../>` | step 7 收尾 |
| `phases/p3-root-cause.md` | L222 | `<phase-abort .../>` | step 7 失败兜底 |
| `phases/p2-spec-definition.md` | L55 | `<phase-abort state="Spec-Uncertain" .../>` | PR-3' 已落 / O14 联动 |
| `phases/p4-fix-design.md` | (后续 grep 补) | … | step n 早退 |
| `phases/p5-fix-impl.md` | (后续 grep 补) | … | … |
| `phases/p6-verification.md` | (后续 grep 补) | … | … |

> **O15 改写约束**：本 PR 仅整理 P3 step 5 三档升级的**路径 / 常量化 / 注释**面，**禁止**改 `state=` 取值或宏体属性 schema（PR-3' / O21 已锁）。
> **CI 守门**：`scripts/check-phase-abort-structure.sh` 在 v4.2 PR-6 起 severity=error；本 PR 应保持零 warning / 零 error。

### §A.6 `<invoke-subagent>` 触达点文件清单（O11+ / O25 共同关注面）

主链：`phases/p2-spec-definition.md`、`p3-root-cause.md`、`p4-fix-design.md`、`p5-fix-impl.md`
deep-dive：`functionality-deep-dive/phases/{f1,f2,f3,f4,f5}.md`
其他：`PLATFORM-GUIDE.md`（仅文档示例，不计入改写）

**总数**：主链 = 13+ 处（P3 = 6, P4 = 7, P5 = 1, P2 = 1）；deep-dive = 6 处。所有 invoke 内的 `<load core-rules.xml>` 已在 §A.1 列齐。

### §A.7 工作量复核

| 子任务 | 触达文件 | 触达行 | 估时 |
|------|---------|---------|------|
| O16-A 键名收口 | 5 文件 | 12 行 | 0.5h |
| O15 P3 升级面整理 | 1 文件 | 3 处宏邻近 | 0.5h |
| O23 拆 essential + dsl + 聚合脚本 + CI | 5 文件（2 新源 + 1 聚合产物 + 1 脚本 + 1 workflow） | — | 4h |
| O24 reasoning 拆 5 文件 + R24-1 真值表落地 | 5 新文件 + P3 5 处替换 + 生成器改造 | — | 4h |
| O25 subagent.xml + invoke load 替换（仅 Full） | 1 新文件 + 26 处 load 改写（条件 if `env_subagent==true`） | 26 行 | 3h |
| O19+ shared-input-guard + wrapper 整合 | 1 新文件 + 2 wrapper 改写 | — | 1h |
| O11+ E1 入口（仅修 coder-agent.md 内部 + 拆 2 件下游） | 1 改写 + 2 新文件 | — | 2h |
| GEN-PR7 build-system-prompt 联动 + 单测 | 2 文件 | — | 2.5h |
| CI Check 18 + workflow 注册 | 2 文件 | — | 1h |
| Token SOP（§2.3）测量 + 表格 | 1 PR 描述段 | — | 1.5h |
| 跨平台回归 3 case | — | — | 1.5h |

**合计**：~21h ≈ **2.5d**（与 §1 工作量一致；可部分并行）。

---
