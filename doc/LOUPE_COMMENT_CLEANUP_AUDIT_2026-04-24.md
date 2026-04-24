# Loupe 工程注释清理审计报告

> 日期：2026-04-24
> 范围：`doc/`、`.github/workflows/`、`eval-cases/`、`eval-framework/`、`mobile-qa-workflow/` 全目录
> 目标：识别“无用注释、历史注释、重复说明、占位说明、生成产物中的冗余说明”，形成可执行清理清单
> 关联文档：`doc/LOUPE_PROJECT_SLIMMING_PLAN_2026-04-24.md`

---

## 一、执行摘要

本轮审计确认：工程在“文件瘦身”之后，仍存在较明显的“注释膨胀”问题，但问题并非均匀分布，而是高度集中在以下四类文件中：

1. `mobile-qa-workflow/phases/` 中带有 PR/Oxx/ADR/Finding 背景的历史修订注释
2. `mobile-qa-workflow/core/`、`SKILL.md`、`PLATFORM-GUIDE.md` 之间重复解释同一协议
3. `mobile-qa-workflow/scripts/` 与 `scripts/tests/fixtures/` 中为了说明修复来历而保留的历史背景注释
4. `eval-framework/` 中未随实现同步更新的版本说明和运行期占位文案

与此同时，也有一批注释虽然冗长，但**不能简单删除**，因为它们属于：

- 生成脚本或校验脚本依赖的协议声明
- 状态模板中的权威枚举说明
- 生成产物的“禁止手改”保护头
- 子工作流 / 子 Agent 的最小契约注释

结论如下：

- P0：当前无必须“立即删除”的注释块，主要是 P1/P2 的结构化压缩
- P1：优先清理 `phases/`、`core/`、`SKILL.md`、`PLATFORM-GUIDE.md`、`eval-framework/__init__.py`
- P2：继续压缩 `scripts/tests/`、`functionality-deep-dive/agents/README.md`、`eval-framework` 其余历史/占位注释
- 长期：建立“运行时文件只保留现态语义，不保留 PR 施工史”的注释治理规则

---

## 二、审计口径

### 2.1 识别为“应清理”的注释

- 历史补丁叙事：如 `v4.2 PR-6 / O13 / reviewer finding` 这类施工史
- 重复协议说明：同一字段或同一流程在多个文件中完整重复
- 占位提示语：会进入运行结果或对外产物的 `[占位]`、`[待分析]`
- 已完成迁移的兼容说明：仍以大段注释保留在运行时文件中
- 测试/夹具中的过度背景：测试目标已经清楚，但注释仍保留完整施工来历

### 2.2 识别为“不能直接删”的注释

- 状态模板的枚举块和保序说明
- 生成产物头部的 autogen / sync / do-not-edit 说明
- `core-rules-*` 中作为 DSL 契约的一次性权威规则说明
- `reference/` 中聚合脚本依赖的结构说明
- 明确约束 LLM 行为的协议型注释

### 2.3 建议动作定义

- 删除：整段注释可以安全移除
- 压缩：保留现态规则，去掉历史来历
- 去重：确立唯一权威源，其他文件改为引用
- 迁移：将历史背景迁移到 ADR、changelog 或治理文档
- 保留：不建议动

---

## 三、全仓结论

| 模块 | 结论 | 优先级 | 备注 |
|------|------|--------|------|
| `doc/` | 当前仅剩瘦身方案文档，注释问题很轻 | 低 | 新增治理报告即可 |
| `.github/workflows/` | 基本无注释治理价值点 | 低 | 保持现状 |
| `eval-cases/` | 基本干净，正文说明属于数据集内容 | 低 | 不建议“为了瘦身而瘦身” |
| `eval-framework/` | 存在版本说明过期、占位文案暴露、TODO 泛化 | 中 | 建议单独做一轮文案收敛 |
| `mobile-qa-workflow/core/` | 协议说明价值高，但历史修订注释偏多，且存在多文件重复 | 高 | 最值得收益的清理区 |
| `mobile-qa-workflow/phases/` | 历史修订注释最密集 | 高 | 建议第一批处理 |
| `mobile-qa-workflow/agents/` | 总体较干净，个别入口文件顶部历史说明可压缩 | 中 | `coder-workflow.md` 已较前期收敛 |
| `mobile-qa-workflow/reference/` | 以权威知识和聚合源为主 | 低 | 原则上保留 |
| `mobile-qa-workflow/templates/` | 基本无冗余注释 | 低 | 保持现状 |
| `mobile-qa-workflow/scripts/` | 有一批“施工史型”脚本头注释 | 中 | 压缩为当前用途即可 |
| `mobile-qa-workflow/scripts/tests/` | 测试意图明确，但背景说明偏长 | 中 | 适合做第二批压缩 |
| `mobile-qa-workflow/functionality-deep-dive/` | 活跃文件总体合理，legacy 说明稍重 | 中 | 重点在 README 和默认配置注释 |

---

## 四、逐模块审计

### 4.1 `doc/`

当前 `doc/` 仅保留 `LOUPE_PROJECT_SLIMMING_PLAN_2026-04-24.md`，没有运行时噪音问题。

建议：

- 保留当前瘦身方案，作为“文件/目录瘦身”权威依据
- 将本次报告作为“注释治理”专项文档并列保存
- 后续若持续做治理，建议新增 `doc/governance/` 归拢专题材料

结论：**本模块不需要注释清理，只需要治理文档收口。**

---

### 4.2 `.github/workflows/`

仅含活跃 CI 工作流：

- `eval.yml`
- `qa-workflow-schema-check.yml`

未发现值得单独治理的冗余注释。

结论：**保持现状。**

---

### 4.3 `eval-cases/`

本轮抽查 10 个 case 的 `metadata.yaml`、`issue-description.md`、`ground-truth/*` 后，结论是：

- 标题、章节、Ground Truth 说明都属于数据集正文，不是“注释垃圾”
- `issue-description.md` 内的“历史变更”属于故障上下文的一部分，默认保留
- 少数文件里的“占位内容”是业务语义，不是仓库占位 README 那类噪音

建议：

- 不对 `eval-cases/` 做专项注释清理
- 后续只在发现“与评测无关的作者备注”时个案处理

结论：**整体干净，不建议继续裁剪。**

---

### 4.4 `eval-framework/`

#### 模块级结论

`eval-framework/` 代码量不大，但存在三类典型问题：

- 顶部文档字符串仍保留旧版本口径
- fallback 逻辑输出“占位”字样，容易被误认为未完成实现
- 个别 TODO / 版本迁移注释过于历史化

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `eval-framework/__init__.py` | 顶部模块说明仍写 6 维度，已与当前 9 维度实现不一致 | 压缩并更新为现态说明 | P1 |
| `eval-framework/judge.py` | `_placeholder_response()` 返回大量 `[占位]` 字样，会进入评估结果 | 改文案，不改逻辑 | P1 |
| `eval-framework/baseline_runner.py` | `_generate_placeholder()` 的 `[待分析]` / `[占位]` 重复过多 | 合并为一次性 fallback 声明 | P1 |
| `eval-framework/weakness_detector.py` | `V3.1 新增...` 注释密度偏高 | 保留一处总说明，删除内联重复版本注释 | P2 |
| `eval-framework/artifact_checker.py` | TODO 过泛，易长期悬挂 | 改为更可追踪的 TODO 或关联任务号 | P2 |
| `eval-framework/tests/test_judge_parse.py` | 测试头注释与版本标签偏历史化 | 压缩为测试目的说明 | P2 |

#### 不建议动的文件

- `coordinator.py`
- `iteration_loop.py`
- `scoring_engine.py`
- `metrics.py`
- `quality_gate.py`
- `report_generator.py`
- `comparator.py`
- `session_manager.py`

这些文件未发现“注释冗余是主要问题”的信号，后续优先级可低。

---

### 4.5 `mobile-qa-workflow/` 根目录文件

#### 模块级结论

根目录的注释问题不是“太少”，而是**同一协议在多个入口文件重复解释**。

重点文件：

- `SKILL.md`
- `PLATFORM-GUIDE.md`
- `system-prompt.md`

其中：

- `system-prompt.md` 是生成产物，不应直接手改
- `SKILL.md` 与 `PLATFORM-GUIDE.md` 对 `workflow_status` 字段、恢复协议、`user_inputs` 单写、`current_phase_result` 非持久化等内容存在明显重复

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/SKILL.md` | 字段说明和协议说明较重，夹带版本修订语句 | 以 `workflow-status-template.yaml` 为权威源，压缩为“入口说明 + 链接” | P1 |
| `mobile-qa-workflow/PLATFORM-GUIDE.md` | 与 `SKILL.md` 对状态恢复和关键字段解释重复 | 删除重复解释，改为引用权威源 | P1 |
| `mobile-qa-workflow/system-prompt.md` | 行数大，但属于生成产物 | 不手改；从 `scripts/build-system-prompt.py` 收敛生成内容 | P1 |
| `mobile-qa-workflow/install.sh` | 未见明显无用注释 | 保留 | 低 |

#### 建议边界

- `SKILL.md` 只回答“如何作为入口运行”
- `PLATFORM-GUIDE.md` 只回答“不同平台如何集成”
- `workflow-status-template.yaml` 负责字段语义和枚举
- `core-rules.xml` 负责协议规则

---

### 4.6 `mobile-qa-workflow/core/`

#### 模块级结论

这是本轮注释治理的关键模块。问题不是“注释多”，而是：

- 有一批注释本身是必要契约
- 另一批注释夹带大量 PR/Oxx/修订史，影响可读性
- 同一协议在 `core-rules.xml`、`core-rules-dsl-reference.xml`、`SKILL.md`、`system-prompt.md` 之间多次重复

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/core/workflow-status-template.yaml` | 字段注释有效，但历史修订信息偏多 | 保留枚举块和字段语义，删除版本施工史，压缩为“现态说明” | P1 |
| `mobile-qa-workflow/core/core-rules-dsl-reference.xml` | DSL 规则注释价值高，但 PR/Oxx/ADR 背景过重 | 保留契约，迁移历史背景到 ADR 或治理文档 | P1 |
| `mobile-qa-workflow/core/core-rules.xml` | 为聚合产物，且与 source 文件重复 | 不手改；通过源文件收敛注释 | P1 |
| `mobile-qa-workflow/core/core-rules-subagent.xml` | 注释已相对克制，仍可轻微压缩头部说明 | 小幅压缩，不改规则主体 | P2 |
| `mobile-qa-workflow/core/workflow.xml` | 兼容与状态路由说明仍有价值，但版本化描述略多 | 删除发布过程描述，仅保留路由规则 | P2 |
| `mobile-qa-workflow/core/config-schema.yaml` | 历史/legacy 注释零散 | 顺手清理即可 | P2 |
| `mobile-qa-workflow/core/default-config.yaml` | 未见突出问题 | 保留 | 低 |
| `mobile-qa-workflow/core/step-pause-registry.yaml` | 属于权威配置，不应为了瘦身压缩可读性 | 保留 | 低 |
| `mobile-qa-workflow/core/workflow-model.yaml` | 未见注释冗余主问题 | 保留 | 低 |

#### 处理原则

- 任何会影响脚本抽取、CI 对账、状态枚举的注释块，不要直接删除
- 历史补丁来源只保留在 ADR / changelog，不在运行时权威文件反复出现

---

### 4.7 `mobile-qa-workflow/phases/`

#### 模块级结论

`phases/` 是当前“无用注释密度最高”的区域。主要问题是：

- 为了说明某次修复来历，保留了过长的 PR/Oxx/ADR/Finding 注释
- 很多注释描述的是“为什么当时这样改”，不是“现在这段 DSL 要表达什么”
- 这些注释占据了运行时上下文，且会降低 phase 文件可读性

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/phases/p2-spec-definition.md` | Non-Bug、Spec-Uncertain、Curation-Failed 相关历史说明偏多 | 压缩为现态协议说明，删除 PR/Oxx/整改史 | P1 |
| `mobile-qa-workflow/phases/p3-root-cause.md` | 重入恢复、升级链、低置信回流处历史注释最密集 | 第一批清理对象；保留规则表意，删除施工史 | P1 |
| `mobile-qa-workflow/phases/p4-fix-design.md` | 与 P3/P6 一样夹带较多修订来历 | 统一压缩为现态规则说明 | P1 |
| `mobile-qa-workflow/phases/p5-fix-impl.md` | 宏协议、回流逻辑说明存在历史化表达 | 压缩 | P1 |
| `mobile-qa-workflow/phases/p6-verification.md` | 失败分类与回流说明夹带版本背景 | 压缩 | P1 |
| `mobile-qa-workflow/phases/p1-intake.md` | 相对干净 | 保留 | P2 |

#### 推荐做法

- 每个 phase 文件只保留“当前规则 + 输入输出语义 + 必要边界”
- 所有“来自哪次 PR / 哪个 finding / 哪次评审”迁移到 ADR 或注释治理文档

---

### 4.8 `mobile-qa-workflow/agents/`

#### 模块级结论

主流程 agents 总体比 phases 干净。真正有治理价值的点不多。

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/agents/coder-workflow.md` | 顶部历史说明偏重，但主体已明显收敛；Error Dump 已改为引用 | 继续压缩头部“拆分来历”说明 | P2 |
| `mobile-qa-workflow/agents/coder-agent.md` | 作为入口文件，需要少量背景说明 | 保留 | 低 |
| `mobile-qa-workflow/agents/shared-arbiter-base.md` | 未见明显冗余 | 保留 | 低 |
| `mobile-qa-workflow/agents/shared-challenger-base.md` | 未见明显冗余 | 保留 | 低 |
| `mobile-qa-workflow/agents/shared-input-guard.md` | 未见明显冗余 | 保留 | 低 |
| `mobile-qa-workflow/agents/arbiter.md` | 未见主要问题 | 保留 | 低 |
| `mobile-qa-workflow/agents/challenger.md` | 未见主要问题 | 保留 | 低 |
| `mobile-qa-workflow/agents/curator.md` | 有少量版本词但不构成核心问题 | 观察 | 低 |
| `mobile-qa-workflow/agents/investigator.md` | 未见主要问题 | 保留 | 低 |
| `mobile-qa-workflow/agents/fix-proposer.md` | 未见主要问题 | 保留 | 低 |

---

### 4.9 `mobile-qa-workflow/reference/`

#### 模块级结论

该目录主要是知识源和聚合源。大多数说明不是噪音，而是可被 LLM 使用的结构化知识。

#### 结论

- `reasoning-chain.md`：生成产物头注释和保护说明应保留
- `reasoning-chain-core.md`：聚合契约说明应保留
- `reasoning-guide-*.md`：按类别切分，说明量合理
- `analysis-strategies.md`、`fix-strategies.md`、`contract-checklist-spec.md`、`platform-checklist.md`：均属高信息密度文件，不建议为了瘦身删注释

结论：**整体不作为本轮清理重点。**

---

### 4.10 `mobile-qa-workflow/templates/`

13 个模板基本都以正文结构为主，不存在明显“历史注释堆积”问题。

结论：**保持现状。**

---

### 4.11 `mobile-qa-workflow/scripts/`

#### 模块级结论

脚本文件里的注释普遍有价值，但头部经常把“实施阶段、PR 编号、review 议题号”完整写入运行代码。对维护者有帮助，对长期可读性不友好。

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/scripts/build-system-prompt.py` | 文件头和函数注释夹带大量 PR/阶段施工史 | 保留构建职责说明，压缩版本演进史 | P1 |
| `mobile-qa-workflow/scripts/check-io-contract.sh` | 头部和规则注释中有历史施工口径 | 压缩为“当前守门规则” | P2 |
| `mobile-qa-workflow/scripts/check-load-targets.sh` | 逻辑性注释有效，archive 例外说明有必要 | 保留 | 低 |
| `mobile-qa-workflow/scripts/check-system-prompt-sync.sh` | 协议性注释有效 | 保留 | 低 |
| `mobile-qa-workflow/scripts/sync-core-rules-aggregate.py` | 聚合契约说明有价值 | 保留 | 低 |
| `mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py` | 聚合契约说明有价值 | 保留 | 低 |

#### 说明

脚本类文件应当保留：

- 输入输出契约
- 同步边界
- 失败条件

但不应长期保留：

- “某次 PR 第几阶段”
- “review 某 finding 的收口过程”
- “首次交付时如何拆批落地”

---

### 4.12 `mobile-qa-workflow/scripts/tests/`

#### 模块级结论

测试本身质量不错，但测试说明有“把修复历史一起写进测试文件”的倾向。

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `mobile-qa-workflow/scripts/tests/test_p3_reentry_replay.py` | 文档字符串过度绑定 READ-N1 / reviewer 议题 | 压缩为“验证 fanout_mode 反查算法等价性” | P2 |
| `mobile-qa-workflow/scripts/tests/test_build_system_prompt.py` | 可能存在类似阶段性背景说明 | 抽查后按需压缩 | P2 |
| `mobile-qa-workflow/scripts/tests/test_sync_core_rules_aggregate.py` | 若仅保留契约说明则无需动 | 观察 | 低 |
| `mobile-qa-workflow/scripts/tests/test_sync_reasoning_chain_aggregate.py` | 若仅保留契约说明则无需动 | 观察 | 低 |
| `mobile-qa-workflow/scripts/tests/fixtures/*.yaml` | 顶部注释以场景说明为主，但夹带历史 bug/PR/Oxx 过多 | 压缩为“前置状态 + 期望结果” | P2 |

---

### 4.13 `mobile-qa-workflow/functionality-deep-dive/`

#### 模块级结论

活跃专项工作流整体设计合理，注释问题集中在 legacy 兼容说明。

#### 文件级建议

| 文件 | 问题类型 | 建议动作 | 优先级 |
|------|----------|----------|--------|
| `functionality-deep-dive/agents/README.md` | legacy agent 退役条件、版本演进、统计口径说明过重 | 压缩为“当前角色 + legacy 删除前提” | P2 |
| `functionality-deep-dive/core/default-config.yaml` | 配置项下方保留完整历史修复叙事 | 收敛成 1-2 行现态说明 | P2 |
| `functionality-deep-dive/agents/archive/v3-legacy/*.md` | legacy wrapper 顶部说明可进一步简化 | 每个文件压缩为最小兼容说明 | P2 |
| `functionality-deep-dive/core/workflow-status-template.yaml` | 若仍含历史版本注释，可对齐主模板治理方式 | 观察 | P2 |
| `functionality-deep-dive/phases/*` | 当前未发现与主 phases 同等级别的注释膨胀 | 保留 | 低 |
| `functionality-deep-dive/reference/*` | 主要是专项知识内容 | 保留 | 低 |
| `functionality-deep-dive/templates/*` | 主要是模板正文 | 保留 | 低 |

---

## 五、重点文件清单

以下文件是本轮最值得优先处理的“高收益注释清理点”：

1. `mobile-qa-workflow/phases/p3-root-cause.md`
2. `mobile-qa-workflow/phases/p2-spec-definition.md`
3. `mobile-qa-workflow/phases/p4-fix-design.md`
4. `mobile-qa-workflow/phases/p5-fix-impl.md`
5. `mobile-qa-workflow/phases/p6-verification.md`
6. `mobile-qa-workflow/core/workflow-status-template.yaml`
7. `mobile-qa-workflow/core/core-rules-dsl-reference.xml`
8. `mobile-qa-workflow/SKILL.md`
9. `mobile-qa-workflow/PLATFORM-GUIDE.md`
10. `mobile-qa-workflow/scripts/build-system-prompt.py`
11. `eval-framework/__init__.py`
12. `eval-framework/judge.py`
13. `eval-framework/baseline_runner.py`

---

## 六、不建议清理的内容

以下内容虽然看起来“像注释很多”，但经审计后确认不应作为本轮目标：

- `mobile-qa-workflow/reference/reasoning-chain.md` 的生成产物保护头
- `mobile-qa-workflow/reference/reasoning-chain-core.md` 的聚合契约说明
- `mobile-qa-workflow/core/workflow-status-template.yaml` 顶部枚举块本身
- `mobile-qa-workflow/core/step-pause-registry.yaml` 的字段说明
- `mobile-qa-workflow/core/core-rules-subagent.xml` 的主体规则
- `mobile-qa-workflow/templates/*`
- `mobile-qa-workflow/reference/*`
- `eval-cases/seed-10/*`
- `.github/workflows/*`

原则：**不要把“权威协议说明”误判成“历史注释”。**

---

## 七、优先级执行矩阵

| 优先级 | 动作 | 范围 | 预期收益 |
|--------|------|------|----------|
| P1 | 压缩 phase 文件中的 PR/Oxx/ADR/Finding 历史注释 | `mobile-qa-workflow/phases/` | 直接减少运行时噪音，提升可读性 |
| P1 | 收敛状态字段和恢复协议的重复说明 | `SKILL.md`、`PLATFORM-GUIDE.md`、`core/workflow-status-template.yaml` | 降低权威源分散 |
| P1 | 压缩 DSL 规则文件中的施工史注释 | `core/core-rules-dsl-reference.xml`、相关 source 文件 | 提高 core 协议阅读效率 |
| P1 | 优化生成脚本头部历史说明 | `scripts/build-system-prompt.py` | 降低维护噪音 |
| P1 | 修复 eval-framework 的过期/占位文案 | `__init__.py`、`judge.py`、`baseline_runner.py` | 提升对外表达准确性 |
| P2 | 压缩测试与夹具中的历史说明 | `scripts/tests/`、`fixtures/` | 减少测试文件噪音 |
| P2 | 压缩专项工作流 legacy 注释 | `functionality-deep-dive/` | 收敛兼容说明 |
| P2 | 收敛零散 TODO 与版本注释 | `eval-framework/` 其余文件 | 降低历史痕迹 |

---

## 八、建议的清理规则

后续执行时，建议统一遵守以下规则：

1. 运行时文件只保留“现态语义”，不保留“施工过程”
2. PR 编号、review finding、Oxx 任务号默认不写入运行时权威文件
3. 需要追溯来历时，优先写入 ADR、changelog、治理报告
4. 同一协议只保留一个权威说明，其他文件用链接或一句话引用
5. 生成产物不手改，统一修改 source 文件和生成脚本
6. 测试注释只说明“场景 + 断言目标”，不复述完整历史修复故事
7. 占位输出应明确标为 fallback/mock，不使用“待分析/占位”这类未完工语义

---

## 九、推荐执行顺序

### 第一批

1. 清理 `mobile-qa-workflow/phases/` 的历史注释
2. 收敛 `SKILL.md` / `PLATFORM-GUIDE.md` / `workflow-status-template.yaml` 的重复说明
3. 压缩 `core-rules-dsl-reference.xml` 中的历史背景注释

### 第二批

4. 清理 `scripts/build-system-prompt.py`
5. 清理 `eval-framework/__init__.py`、`judge.py`、`baseline_runner.py`
6. 压缩 `scripts/tests/` 和 `fixtures/`

### 第三批

7. 压缩 `functionality-deep-dive/agents/README.md`
8. 压缩 `functionality-deep-dive/core/default-config.yaml`
9. 收尾 `eval-framework/weakness_detector.py`、`test_judge_parse.py` 等低优先项

---

## 十、最终结论

仓库当前已经完成“文件层瘦身”，下一步最有价值的工作不是继续删文件，而是把运行时文件中的历史施工注释、重复协议说明和占位文案进一步收敛。

本轮审计后的总体判断是：

- **最需要清理的是 `mobile-qa-workflow/phases/`**
- **最需要去重的是 `core/` + `SKILL.md` + `PLATFORM-GUIDE.md`**
- **最需要纠正的是 `eval-framework/` 的过期/占位文案**
- **最不该误删的是 `reference/`、`templates/`、状态模板枚举块和生成产物保护头**

建议按本报告的 P1 -> P2 顺序继续实施，预计可以在不改变工作流能力的前提下，进一步显著降低提示词噪音和维护成本。
