# Mobile QA Workflow Batch A/B/C PR Description

> 日期：2026-04-18
> 分支：`feature/coder_subagent`
> 范围：共享基座、主链路动态路由、Functionality Deep-Dive 收敛、UI Deep-Dive、Eval 闭环

---

## 1. PR 标题建议

`feat: land Batch A/B/C workflow upgrade with shared bases, dynamic routing, deep-dive convergence, and eval ROI`

---

## 2. 背景

本次改造基于 `B2C_WORKFLOW_SUBAGENT_BATCH_ABC_EXEC_TASKS_2026-04-18.md` 的施工目标，完成了 `Batch A/B/C` 的核心落地，重点解决以下问题：

- 主流程 `challenger / arbiter` 存在重复 prompt 逻辑，缺少共享协议基座
- `P2 / P3 / P4 / P6` 的复杂度判断、动态 fan-out、失败回流有底座但未真正形成闭环
- `Functionality Deep-Dive` 仍保留较多细粒度旧角色，`F4` 还借用主流程 `investigator`
- 缺少可运行的 `UI Deep-Dive`
- `eval-framework` 尚不能量化动态 fan-out、Deep-Dive 进入率和平均 agent 成本收益

本次改造将上述能力按 5 个提交主题完成，并已推送到远程分支。

---

## 3. 变更概览

### 3.1 共享 `challenger / arbiter` 基座

对应提交：

- `9863f29` `feat(workflow): add shared challenger and arbiter bases`

核心改动：

- 新增共享基座文件：
  - `mobile-qa-workflow/agents/shared-challenger-base.md`
  - `mobile-qa-workflow/agents/shared-arbiter-base.md`
- 将主流程 `challenger / arbiter` 改为包装层：
  - `mobile-qa-workflow/agents/challenger.md`
  - `mobile-qa-workflow/agents/arbiter.md`

达成效果：

- `challenger` 统一输入契约、维度集、输出结构、置信度影响格式
- `arbiter` 统一候选汇总、质疑吸收、最终裁定、`final_confidence` 计算口径
- 后续 `RCA / FIX / DEEP_DIVE` 场景都通过“共享基座 + 包装层 + 显式参数注入”工作

---

### 3.2 Functionality Deep-Dive 收敛为复合角色工作流

对应提交：

- `58edc94` `feat(deep-dive): add composite functionality deep-dive workflow`

核心改动：

- 新增 4 个复合角色：
  - `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-context-analyst.md`
  - `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-structure-analyst.md`
  - `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`
  - `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-arbiter.md`
- 重写专项编排与状态：
  - `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
  - `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
  - `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- 阶段切换到复合角色：
  - `f1-context-reconstruction.md`
  - `f2-state-topology.md`
  - `f3-temporal-correlation.md`
  - `f4-isolation-debate.md`
  - `f5-defensive-fix-design.md`
- 更新专项产物模板与说明文档：
  - `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
  - `agents/README.md`

达成效果：

- `F4` 不再借用主流程 `investigator`
- 专项角色收敛为 4 个复合角色 + 1 个按需防御性修复角色
- 中间产物默认降级为按需附录，主流程优先依赖 `deep-dive-summary.md` 和必要 RCA

---

### 3.3 新增最小可运行 `UI Deep-Dive`

对应提交：

- `fa17ef7` `feat(ui-deep-dive): add minimal runnable UI deep-dive workflow`

核心改动：

- 新增完整 `ui-deep-dive` 目录
- 新增 UI 专项角色：
  - `ui-context-analyst`
  - `ui-structure-analyst`
  - `ui-render-and-interaction-analyst`
  - `ui-deep-dive-arbiter`
- 新增 `U1-U4` 阶段和 RCA / Summary 模板

达成效果：

- UI 疑难问题具备独立专项入口
- 支持视觉基线、布局拓扑、渲染时序、交互冲突四段式分析

---

### 3.4 主工作流动态路由正式生效，并同步入口说明

对应提交：

- `49401ce` `feat(main-workflow): enable dynamic routing and sync platform entrypoints`

核心改动：

- 主编排状态与 I/O 契约更新：
  - `mobile-qa-workflow/core/workflow.xml`
  - `mobile-qa-workflow/core/workflow-status-template.yaml`
  - `mobile-qa-workflow/core/default-config.yaml`
  - `mobile-qa-workflow/core/core-rules.xml`
- P2 输出复杂度与 fan-out 建议：
  - `mobile-qa-workflow/phases/p2-spec-definition.md`
  - `mobile-qa-workflow/templates/spec.md`
- P3 正式启用三档动态 fan-out：
  - `mobile-qa-workflow/phases/p3-root-cause.md`
  - `mobile-qa-workflow/reference/analysis-strategies.md`
- P4 正式启用三档 proposer 模式：
  - `mobile-qa-workflow/phases/p4-fix-design.md`
  - `mobile-qa-workflow/templates/fix-design.md`
  - `mobile-qa-workflow/reference/fix-strategies.md`
- P6 失败分类与回流逻辑统一：
  - `mobile-qa-workflow/phases/p6-verification.md`
- 平台入口与说明同步：
  - `mobile-qa-workflow/PLATFORM-GUIDE.md`
  - `mobile-qa-workflow/SKILL.md`
  - `mobile-qa-workflow/system-prompt.md`

达成效果：

- `P2` 将 `analysis_complexity / analysis_complexity_confidence / fanout_mode` 写回状态
- `P3` 支持 `simple-single / medium-challenge / complex-arbitrated`
- `P4` 支持 `single-proposer / challenged-proposer / contested-arbitrated`
- `P6` 可按失败类型回流 `P3` 或 `P4`
- 主流程可接入 Functionality / UI 专项结论

---

### 3.5 Eval 闭环补齐

对应提交：

- `1d356df` `feat(eval): add fanout roi and agent efficiency metrics`

核心改动：

- 评测核心组件更新：
  - `eval-framework/coordinator.py`
  - `eval-framework/judge.py`
  - `eval-framework/comparator.py`
  - `eval-framework/scoring_engine.py`
  - `eval-framework/quality_gate.py`
  - `eval-framework/report_generator.py`
- 配置与 Schema 更新：
  - `eval-framework/artifact-checklist.yaml`
  - `eval-framework/case-schema.yaml`
  - `eval-framework/configs/eval-config.yaml`
  - `eval-framework/configs/monthly-compare.yaml`
  - `eval-framework/configs/nightly-full.yaml`
  - `eval-framework/configs/pr-quick.yaml`
- `seed-10` 元数据补齐 expected route / fan-out / fix mode

达成效果：

- 评测可以采集并比较：
  - `fanout_mode`
  - `fix_strategy_mode`
  - `specialized_workflow_mode`
  - `avg_agent_count`
  - `score_per_agent`
  - `deep_dive_activation_rate`
  - `expected_route_hit_rate`
  - `expected_fanout_hit_rate`
- 质量门禁不再只看分数，也可看成本/收益

---

## 4. 关键设计决策

### 4.1 共享基座替代重复大 prompt

- 避免主流程和专项流程维护两份长期漂移的 `challenger / arbiter`
- 将输入协议、输出协议、置信度公式收敛到单一事实源

### 4.2 Deep-Dive 先做角色复合化，再保留旧文件兼容

- 先收敛调用关系
- 保留历史会话恢复路径，避免旧工作区失效

### 4.3 中间专项产物降级为按需附录

- 降低默认文件风暴
- 保持主流程只依赖 `summary + 必要 RCA`

### 4.4 评测补齐效率指标

- 动态 fan-out 的目标不是单纯增加 Agent 数，而是提升质量/成本比
- Deep-Dive 的目标不是更多产物，而是更高命中收益

---

## 5. 兼容性与风险

### 兼容性

- 主流程状态文件保留旧版兼容逻辑
- Functionality Deep-Dive 旧角色文件保留为兼容包装层
- `system-prompt.md`、`SKILL.md`、`PLATFORM-GUIDE.md` 已同步口径

### 风险点

- `P3 / P4` 动态路由启用后，行为不再是固定重模式
- UI Deep-Dive 当前为最小可运行版本，后续仍可能继续补强
- Eval 指标依赖标准状态字段完整写回

---

## 6. 验证

已完成自检：

- `python3 -m py_compile eval-framework/*.py`
- 关键 YAML 已通过 `yaml.safe_load` 校验
- 回查确认专项 `F4` 已不再借用通用 `investigator`
- 当前改动已分批提交并推送到远程分支

---

## 7. 提交列表

- `9863f29` `feat(workflow): add shared challenger and arbiter bases`
- `58edc94` `feat(deep-dive): add composite functionality deep-dive workflow`
- `fa17ef7` `feat(ui-deep-dive): add minimal runnable UI deep-dive workflow`
- `49401ce` `feat(main-workflow): enable dynamic routing and sync platform entrypoints`
- `1d356df` `feat(eval): add fanout roi and agent efficiency metrics`

---

## 8. 不在本 PR 内

- 本文档创建前，`doc/` 下的若干分析和拆分文档尚未纳入远程，需要单独补充提交
- 旧专项角色文件的物理删除未执行，当前仍保留兼容恢复路径

---

## 9. Reviewer 建议关注点

- `shared-challenger-base / shared-arbiter-base` 的输入输出协议是否足够稳定
- `p3-root-cause / p4-fix-design / p6-verification` 的状态回写字段是否闭环
- Functionality Deep-Dive 复合角色切换后是否仍覆盖原关键分析能力
- UI Deep-Dive 最小拓扑是否满足当前专项接入需求
- Eval 指标是否与 `workflow-status` 的实际语义一致

---

## 10. 可直接粘贴的简版摘要

本 PR 完成 Mobile QA Workflow 的 Batch A/B/C 核心落地：新增共享 `challenger/arbiter` 基座，正式启用 P2/P3/P4/P6 动态路由，收敛 Functionality Deep-Dive 为复合角色工作流，新增最小可运行 UI Deep-Dive，并补齐 `eval-framework` 对 fan-out ROI、Deep-Dive 进入率与平均 agent 成本的量化能力。
