# Coder SubAgent 修复对比报告

生成时间：2026-04-18

## 1. 修复目标

本轮修复聚焦上一次 review 中确认的 4 个问题：

1. P5 失败分支缺少真正的显式终止语义
2. P5 在成功验收后可能再次覆写 `impl-report.md`
3. P6 使用了与 DSL 规范不一致的 `switch on` 写法
4. `mobile-qa-workflow/` 权威源与 `.cursor/.trae` 镜像、`system-prompt.md` 入口存在漂移

## 2. 逐文件变更点

| 文件 | 修复前问题 | 本次修复点 |
|------|------------|------------|
| `mobile-qa-workflow/core/workflow.xml` | 阶段返回后无论成功失败都会把当前阶段写入 `stepsCompleted` | 新增 `current_phase_result` 初始化；在阶段收口处识别 `ABORT`，失败阶段不再写入 `stepsCompleted` |
| `mobile-qa-workflow/phases/p5-fix-impl.md` | 失败路径只写“阶段终止”文字，但没有显式控制流；Step 7 会继续执行；成功路径会再次模板写入 `impl-report.md` | 失败分支统一 `goto step="8"` 收口，并更新 `current_state = Human-Review`；Step 7 改为仅在 `non-code-fix` 且报告不存在时模板输出，`code-fix` 明确保留 Coder Agent 产物 |
| `mobile-qa-workflow/phases/p6-verification.md` | 使用 `switch on="Repair-Route"` / `case value="..."`，与 DSL 规范不一致 | 改为 `switch condition="Repair-Route"` / `case if="..."`，与 `core-rules.xml` 和主编排一致 |
| `mobile-qa-workflow/system-prompt.md` | Limited 平台仍保留旧版 Phase 5/6 内联逻辑，缺少契约溯源门禁、Error Dump、契约交叉验证 | 补齐 Phase 5 路由判定、契约溯源、微验证纠错和 Error Dump；补齐 Phase 6 契约溯源交叉验证；同步模板摘要 |
| `.cursor/skills/mobile-qa-workflow/core/workflow.xml` | 镜像目录保留旧版阶段收口语义 | 与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/phases/p5-fix-impl.md` | 镜像目录仍为旧版 P5，无显式失败收口和防覆写逻辑 | 与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/phases/p6-verification.md` | 镜像目录仍为旧版 P6 DSL | 与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/system-prompt.md` | 镜像目录仍为旧版 Limited 入口 | 与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/agents/coder-agent.md` | 缺失 `coder-agent.md`，Full 平台无法加载该角色 | 新增并与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/templates/contract-checklist.md` | 缺失契约清单模板 | 新增并与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/templates/error-dump.md` | 缺失纠错失败转储模板 | 新增并与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/templates/impl-report.md` | 模板字段落后于 V3.1 设计 | 与权威源同步 |
| `.cursor/skills/mobile-qa-workflow/templates/verification-report.md` | 模板字段落后于 V3.1 设计 | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/core/workflow.xml` | 镜像目录保留旧版阶段收口语义 | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/phases/p5-fix-impl.md` | 镜像目录仍为旧版 P5，无显式失败收口和防覆写逻辑 | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/phases/p6-verification.md` | 镜像目录仍为旧版 P6 DSL | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/system-prompt.md` | 镜像目录仍为旧版 Limited 入口 | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/agents/coder-agent.md` | 缺失 `coder-agent.md`，Full 平台无法加载该角色 | 新增并与权威源同步 |
| `.trae/skills/mobile-qa-workflow/templates/contract-checklist.md` | 缺失契约清单模板 | 新增并与权威源同步 |
| `.trae/skills/mobile-qa-workflow/templates/error-dump.md` | 缺失纠错失败转储模板 | 新增并与权威源同步 |
| `.trae/skills/mobile-qa-workflow/templates/impl-report.md` | 模板字段落后于 V3.1 设计 | 与权威源同步 |
| `.trae/skills/mobile-qa-workflow/templates/verification-report.md` | 模板字段落后于 V3.1 设计 | 与权威源同步 |

## 3. 修复后的验证逻辑

### 3.1 P5 修复实施阶段

#### code-fix 路径

1. Phase 5 先调用 `coder-agent`
2. `coder-agent` 负责写出：
   - `impl-report.md`
   - `contract-checklist.md`（代码修复路径）
   - `error-dump.md`（仅 3 轮纠错失败）
3. P5 Step 6 读取文件哨兵：
   - 若存在 `error-dump.md`：判定 `Human-Review`，设置 `current_phase_result = ABORT`，跳转失败收口
   - 若存在 `impl-report.md` 且存在 `contract-checklist.md`：判定成功，进入 Step 7
   - 若存在 `impl-report.md` 但缺失 `contract-checklist.md`：判定 `Incomplete`，设置 `current_state = Human-Review`，跳转失败收口
   - 若两个产物都不存在：判定 `Incomplete`，设置 `current_state = Human-Review`，跳转失败收口
4. 成功路径下，Step 7 不再覆写 `impl-report.md`，而是直接保留 `coder-agent` 的实施报告

#### non-code-fix 路径

1. Phase 5 在路由判定后直接进入输出阶段
2. 若 `impl-report.md` 尚不存在，则允许模板生成基础报告
3. 进入 `Verifying`

### 3.2 阶段收口逻辑

1. 主编排在执行阶段前初始化 `current_phase_result = CONTINUE`
2. 若阶段内显式设置为 `ABORT`：
   - 当前阶段不会写入 `stepsCompleted`
   - `lastStep` 仍记录当前阶段，便于人工恢复
   - 后续路由基于 `current_state` 执行，不会把失败阶段误记为已完成

### 3.3 P6 验证阶段

1. 先从 `impl-report.md` 提取 `Repair-Route` 和 `Execution-Status`
2. 按 `Repair-Route` 分支：
   - `code-fix`：必须执行 `contract-checklist.md` 交叉验证
   - `non-code-fix`：标记 `SKIPPED`
3. 契约溯源结果参与 L1 结论：
   - `PASS` / `SKIPPED`：不阻断
   - `WARNING`：允许保留人工确认语义
   - `FAIL`：L1 失败，回退到 Phase 4

### 3.4 多入口一致性

本次修复后，以下入口语义保持一致：

- `mobile-qa-workflow/` 权威源
- `.cursor/skills/mobile-qa-workflow/`
- `.trae/skills/mobile-qa-workflow/`
- `system-prompt.md` 的 Limited 平台内联逻辑

## 4. 本次已执行检查

### 4.1 诊断检查

- `mobile-qa-workflow/core/workflow.xml`：无诊断错误
- `mobile-qa-workflow/phases/p5-fix-impl.md`：无诊断错误
- `mobile-qa-workflow/phases/p6-verification.md`：无诊断错误
- `mobile-qa-workflow/system-prompt.md`：无诊断错误

### 4.2 规则检查

- 全仓 `mobile-qa-workflow` 范围内已无 `switch on=` 旧写法残留
- `current_phase_result = ABORT` 已被主编排识别和消费

### 4.3 镜像一致性检查

已确认以下权威文件与 `.cursor/.trae` 镜像内容完全一致：

- `core/workflow.xml`
- `phases/p5-fix-impl.md`
- `phases/p6-verification.md`
- `system-prompt.md`
- `agents/coder-agent.md`

## 5. 结论

本轮修复完成后：

1. P5 失败路径具备了真实的显式中断语义
2. `impl-report.md` 不会再在 code-fix 成功后被模板覆写
3. P6 的 DSL 写法回归到现有解释器约定
4. Full / Limited / 镜像入口的行为和产物契约已重新对齐
