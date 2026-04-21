# PR-2 施工方案质检报告

> 评审对象：`mobile-qa-workflow/construction-plans/v4.2/pr-2-sync-debt-and-system-prompt-generator.md`
> 评审日期：2026-04-21
> 评审结论：**暂不建议按当前版本直接开工**
> 评审方式：基于当前仓库现状做静态一致性核查，并实际执行现有守门脚本，重点验证字段瘦身、迁移兼容、CI 升级、生成器交付是否与真实工程闭环一致。

---

## 1. 总体结论

本方案的目标方向基本合理：

- 删除明显冗余的状态字段，降低 `workflow-status` 认知负担
- 把 `system-prompt` 的同步问题从“口头要求”升级为“脚本守门”
- 提前交付生成器，为 PR-6 的首次自动构建铺路

但当前版本仍存在 **2 个阻断级问题** 和 **4 个高优先级问题**，主要集中在：

- O7 删除 `rca_fanout_mode_snapshot` 的论据依赖一个当前仓库中**并不存在的已落地读端保障**
- O5 直接把 `check-system-prompt-sync.sh` 从 warning 升到 error，在当前脚本实现下会把主干已知噪音直接升级成红 CI
- O22 / CI-U1 / CI-U2 的“脚本本身不动”与正文中“要改脚本默认值/补豁免逻辑”互相矛盾
- `check-io-contract.sh` 当前校验模型仍然过宽，升级 error 后也难以形成有效守门
- 生成器部分对“Stage 1 骨架”与“必须完整可用于 PR-6”的定义摇摆，DoD 口径不收敛
- H1 前置守门脚本的提取策略延续了当前 sync 脚本的脆弱正则风格，误报风险偏高

建议先修订施工单，再进入实施。

---

## 2. 质检评级

| 维度 | 评级 | 说明 |
|---|---|---|
| 目标清晰度 | B | 范围边界大体清楚，但局部约束互相打架 |
| 与仓库现状一致性 | C- | 关键兼容性前提和 CI 现状描述不完全成立 |
| 可实施性 | C | 可以修订后实施，当前版本直接施工风险偏高 |
| CI 方案可靠性 | D+ | 至少 2 个守门脚本当前不适合直接升级为 error |
| 兼容性与迁移设计 | C- | 有意识，但 O7 的主论据与现状不符 |

**综合结论**：`不通过（需修订后复审）`

---

## 3. Blocking Findings

### 3.1 阻断问题 1：O7 删除 `rca_fanout_mode_snapshot` 的核心前提，与当前仓库实现不一致

**结论**：方案把 `phase_history` 反查描述为“已是主路径、读端已具备”，据此认定 `rca_fanout_mode_snapshot` 可以直接删除；但当前仓库里并没有找到这个“已落地的读端闭环”，现有迁移脚本反而明确声明**不实施**该反查还原逻辑。

**事实依据**：

- 施工单多处写明：
  - 方案 A（`phase_history` 反查）已是主路径
  - 存量会话读端“改为只读 `phase_history`”
  - “P3 重入还原逻辑由 PR-1 已合入的迁移脚本反查路径支撑”
- 但当前 `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py` 文件头明确写着：
  - `不实施 fanout_mode 反查还原逻辑`
- 当前真实实现里：
  - `core/workflow-status-template.yaml` 仍保留 `rca_fanout_mode_snapshot`
  - `phases/p3-root-cause.md` step 10 仍同时写 `rca_fanout_mode_snapshot` 和 `phase_history`
- 本次核查未在仓库中找到一个现成的、已生效的“仅依赖 `phase_history` 完成 P3 重入还原”的读端实现。

**风险**：

- 该变更不再是文档中声称的“主路径零运行时分支变更”，而是实际触达 P3 重入兼容链路。
- 如果直接删 snapshot 写入和 schema 字段，但没有先补齐真实读端，存量会话或边缘重入路径会丢掉还原依据。
- reviewer 会被“已有保障”这一表述误导，低估回放验证的重要性。

**修订建议**：

- 先把“谁在什么时机读取 `phase_history` 并恢复 `fanout_mode`”写成真实可定位的实现链路，再决定 O7 是否独立落在 PR-2。
- 如果该读端尚未存在，建议把 O7 改成两步：
  - 第一步：先补齐读端，并用回放用例证明 snapshot 已完全冗余
  - 第二步：再删 schema 字段和写入点
- 若坚持 PR-2 直接删除，则必须把 PR 定位改成“兼容链路有运行时触达”，并新增强制回放验收。

---

### 3.2 阻断问题 2：O5 把 `check-system-prompt-sync.sh` 升级为 error 的前提不成立，当前主干脚本会直接产出噪音告警

**结论**：施工单声称 PR-2 里只要把 workflow yml 中的 severity 从 warning 切到 error 即可，但当前脚本在干净工作树上就会报出与真实语义无关的 warning；直接升 error 会把现有噪音变成硬阻塞。

**事实依据**：

- 我在当前仓库直接执行 `bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh`，脚本退出 0，但输出了 2 条 warning：
  - `ENUM-DECLARATION-BLOCK 与 core/workflow-status-template.yaml 头部 enum 集不一致`
  - `Spec-Uncertain allowed_values 字面不一致`
- 这两条 warning 不是单纯由 PR-2 计划中的 O7/O8 引起，而是脚本自身提取策略过于脆弱：
  - 校验 1 的 `ENUM_CORE` 从 `workflow-status-template.yaml` 头部注释中抓 PascalCase token，会把 `PRESERVE_FORMAT`、`SKILL`、`PLATFORM-GUIDE` 等非 state 文本一起抓进去
  - 校验 2a 直接取两个文件里**第一个** `allowed_values=`，当前命中的并不是 `Spec-Uncertain` 的目标段，而是更靠前的通用协议文本
- 施工单首页“涉及文件”又写了：
  - `check-system-prompt-sync.sh` 仅 workflow yml 侧切换 severity，脚本本身不动
- 但正文 CI-U1 又明确要求：
  - 脚本默认值 `warning -> error`
  - 还要给 2a 增加 `Confirm vs 1|2|S` 的豁免逻辑

**风险**：

- 按“脚本不动，仅切 severity”执行，会直接把当前主干的噪音 warning 升成红 CI。
- reviewer 无法判断应该按“文件列表”还是按“CI-U1 小节”实施，容易造成范围失控。
- 后续一旦有人修了脚本提取器，但没同步修施工单，DoD 与实现会再次漂移。

**修订建议**：

- 明确把 O5 拆成两个子项：
  - 先修 `check-system-prompt-sync.sh` 的提取逻辑
  - 再升级 severity 为 error
- 施工单中的“涉及文件”和 CI-U1 小节必须统一，不要同时出现“脚本本身不动”和“脚本默认值/逻辑需要改”两种口径。
- 在脚本修好之前，不建议承诺“PR-2 直接升级 error”。

---

## 4. Major Findings

### 4.1 高优先级问题 1：`check-io-contract.sh` 当前仍是“宽松兜底”模型，升级为 error 的守门价值不足

**结论**：施工单将 CI-U2 描述为“warning -> error”的自然升级，但当前 `check-io-contract.sh` 仍以“存在任意变量化路径就放行”为核心兜底逻辑，升级后也很难形成有效的产物契约守门。

**事实依据**：

- 我在当前仓库执行 `bash mobile-qa-workflow/scripts/check-io-contract.sh`，结果为：
  - `DECLARED=13 / ACTUAL=6`
  - 大量产物（如 `spec.md`、`issue-card.md`、`fix-design.md`、`verification-report.md`）都只是以 `::notice::存在变量化路径兜底` 方式放过
- 当前脚本 Step 3 的实际规则是：
  - 只要 `ACTUAL` 中存在任意 `{output_*}` 变量化路径，就允许未直接命中的 basename 通过
- 这意味着脚本更接近“结构存在性检查”，而不是“产物映射正确性检查”。
- 施工单“涉及文件”同样写了 `check-io-contract.sh` 脚本本身不动，但 CI-U2 小节又要求改脚本默认 severity，存在与 CI-U1 相同的口径矛盾。

**风险**：

- 升 error 后看起来更严格，实际上只是把一个本就宽松的脚本变成强制通过项，守门增益有限。
- 一旦未来真实产物名漂移，但变量化占位仍在，脚本可能继续假绿。

**修订建议**：

- 先决定 PR-2 对 `io-contract` 的目标到底是：
  - “只消除 warning 噪音”
  - 还是“真正建立强契约”
- 如果要升 error，建议先补一版更窄但更可信的匹配模型，再升级。

---

### 4.2 高优先级问题 2：施工单对 CI 变更范围的描述前后冲突，实施边界不稳定

**结论**：文档首页的“涉及文件”表与后文 CI-U1 / CI-U2 细节不一致，导致 reviewer 无法仅凭方案判断哪些脚本应该被修改。

**事实依据**：

- 首页写法：
  - `check-system-prompt-sync.sh`：仅 workflow yml 侧切 severity，脚本本身不动
  - `check-io-contract.sh`：仅 workflow yml 侧切 severity，脚本本身不动
- 但后文又分别提出：
  - 修改 `SEVERITY="${...:-warning}"` 为 `error`
  - 给 `check-system-prompt-sync.sh` 增加已知漂移豁免逻辑

**风险**：

- 实施者可能只改 workflow yml，不改脚本；也可能把脚本逻辑一起改了，但与文件清单不一致。
- reviewer 难以依据“预计 diff”做核对，DoD 的边界感被削弱。

**修订建议**：

- 把首页“涉及文件”更新为真实修改范围。
- 把 CI-U1 / CI-U2 拆成“workflow 集成改动”和“脚本逻辑改动”两个编号，避免混在一起。

---

### 4.3 高优先级问题 3：生成器部分对“Stage 1 骨架”与“完整实现”的定义不收敛

**结论**：方案前半段把 `build-system-prompt.py` 定位成“Stage 1 交付脚本 + 单测，不首次构建”；但后文又要求它具备完整的 `full/layered/verify` 模式、L0-L4 builder、产物写出能力，以及较重的单元测试覆盖，实际上已经接近“可正式投产的完整实现”。

**事实依据**：

- GEN-N1 标题写的是“生成器骨架”
- 代码草案却要求：
  - `--mode=full`
  - `--mode=layered`
  - `--mode=verify`
  - 5 个 builder
  - 禁止输出到 `system-prompt.md` 的运行时守门
- Reviewer 议题 #3 又明确建议：
  - “本 PR 交付完整实现，否则 PR-6 首次构建无法触发”
- DoD 也要求：
  - `python build-system-prompt.py --mode=verify` 退出 0
  - unittest discover 全绿

**风险**：

- 开发者难以判断这是不是一个“允许 stub 的准备 PR”。
- 如果按“骨架”实现，DoD 很可能达不到；如果按“完整实现”实现，工作量与风险会高于文档首页的预估。

**修订建议**：

- 在方案中二选一并写死：
  - 要么定义为“可运行的最小完整实现”
  - 要么定义为“骨架 + 明确未实现清单”，并同步下调 DoD
- 当前更合理的口径是：`PR-2 交付 PR-6 可直接调用的最小完整实现，但不执行首次替换`

---

### 4.4 高优先级问题 4：H1 前置守门脚本的提取思路偏脆弱，存在重复踩中当前 sync 脚本问题的风险

**结论**：新提议的 `check-build-system-prompt-precondition.sh` 主要依赖 `grep -oE` 从 markdown/XML 混合文本中抽 `allowed_values`；这和当前 `check-system-prompt-sync.sh` 的脆弱点属于同一类问题，可靠性需要在方案中提前约束。

**事实依据**：

- 当前 sync 脚本已经因为“取第一个 `allowed_values=`”而命中错误位置，产生无意义 warning。
- 新脚本同样使用基于文本顺序的正则抽取：
  - 从 `system-prompt.md` 提 `Spec-Uncertain ... allowed_values=...`
  - 从 `core/workflow.xml` 提 `allowed_values="1|2|S"` 或近似命中
- 但两个文件都包含多个 `allowed_values=` 片段，且既有 XML，又有说明文本、示例文本、规则文本。

**风险**：

- 守门脚本可能在文案小改、注释顺序调整后误报。
- H1 本应是“高置信硬约束”，如果实现方式过于脆弱，反而会削弱其可信度。

**修订建议**：

- 不要依赖“第一个命中”或“模糊上下文命中”。
- 方案中应明确：
  - 锚点范围
  - 精确目标段
  - 缺失时的失败模式
- 最稳妥的做法是给目标段加稳定注释锚点，再按锚点提取。

---

## 5. 次要问题与优化建议

### 5.1 O7 / O8 的引用计数与真实仓库命中点未完全对齐

- 方案多处写“删 5 处引用”“删 6 处引用”，但当前仓库里相关词还散落在多份历史文档、施工单和主文档中。
- 如果这些数字只指“运行时主链 + 对外文档”范围，建议在方案里明确口径，避免 reviewer 误以为是全仓 grep 计数。

### 5.2 `system-prompt.md` “仅允许 2 行改动”的约束可以更可执行

- 当前方案说“字段表删 1 行 + 描述改 1 行”，方向是对的。
- 但若要真正防止顺手改动，建议把验证方式前置写成：
  - reviewer 必贴出 `git diff -- system-prompt.md`
  - 或新增一个更专门的局部 diff 守门，而不是只靠 H1 间接兜底

---

## 6. 建议的修订动作

建议按以下顺序修订施工单后再开工：

1. **先修 O7 兼容性口径**
   - 明确真实读端是谁。
   - 若尚未落地，先补读端或下调 O7 到后续 PR。

2. **再修 O5 / CI-U1**
   - 先修 `check-system-prompt-sync.sh` 的提取器，再谈 severity 升级。
   - 统一“脚本本身是否修改”的文档口径。

3. **再评估 CI-U2**
   - 明确 `check-io-contract.sh` 是“降噪升级”还是“强契约升级”。
   - 如需 error 级守门，先增强算法。

4. **收敛生成器目标**
   - 把“骨架”还是“最小完整实现”写死。
   - 让 DoD、工时和测试策略与该目标一致。

5. **强化 H1 守门设计**
   - 为 `Spec-Uncertain` 目标段增加稳定锚点。
   - 避免再走“首个正则命中”的脆弱路线。

---

## 7. 可采纳项

以下内容建议保留，作为修订版施工单基础：

- `fix_strategy_mode` 与 `fix_fanout_mode` 的语义重叠判断基本成立
- `system-prompt.md` 不在 PR-2 进行首次自动重建，这个边界设置是合理的
- 通过 `--cleanup-v4-deprecated` 处理存量会话，方向正确
- 用 ADR 追加修订段而不是重写旧 ADR，追溯性设计合理
- 把生成器纳入单测和 CI，而不是只交一个脚本文件，方向正确

---

## 8. 最终裁定

**裁定**：`Reject for now`

**原因**：当前施工单的主要问题不是“方向错误”，而是“兼容性前提、CI 现状、实施范围”三者还没有完全对齐。尤其是 O7 与 O5，已经达到会影响真实落地路径的级别，不适合直接照单施工。

**建议流程**：

- 先把施工单修订到 v1.1
- 修完后优先复审 O7 / O5 / CI-U2 三块
- 复审通过后再进入实施
