# Functionality Deep-Dive V2 可实施变更清单

> **目的**：将 `FUNCTIONALITY_DEEP_DIVE_IMPLEMENTATION_PLAN_V2.md` 进一步拆解为“逐文件、逐修改点、逐内容”的工程实施清单，供开发直接按文件落地。  
> **范围**：仅覆盖 V2 认定的 P0/P1 必要改动，并明确哪些文件 **不要改**，避免回到 V1 的错误实现路径。  
> **适用对象**：工作流编排维护者、Agent 协议维护者、模板维护者。

---

## 0. 总体实施原则

1. Deep-Dive 是 **P2/P3/P4 内部增强分支**，不是新 phase。
2. 不引入 `Deep-Dive-InProgress`、不依赖 `workflow.xml` 新状态路由。
3. 所有 Deep-Dive 产物必须能被主产物消费，不能只是旁路文件。
4. 多根因场景落地为：`Primary Root Cause + Contributing Factors`，而不是彻底改写现有 RCA/Fix 主链路。

---

## 1. 必改文件清单

### 1.1 `mobile-qa-workflow/phases/p3-root-cause.md`

**优先级**：P0  
**改动目标**：修正 Deep-Dive 的真正触发点与执行位置，覆盖“直接 deep”和“fast 升级 deep”两类路径。

#### 需要修改的位置

1. `Step 4: 边界驱动路由与复杂度评估`
2. `Step 5: 执行 OVHSC 结构化推理链`

#### 具体修改内容

##### A. 在 `Step 4` 末尾新增 Deep-Dive 候选判定

在现有 `analysis_path` 判定逻辑之后、`Step 4` 结束前，新增一个布尔标记的说明性 action：

```xml
<action>计算 deep_dive_candidate：
    当满足以下全部条件时，标记为 true：
    1. 主分类 == "功能"
    2. complexity_level == "complex"
    3. 问题表现包含以下任一特征：
       - 偶发性（非100%复现）
       - 涉及状态机跳转异常
       - 涉及并发/竞态
       - 涉及缓存一致性
       - Crash 栈指向系统底层但怀疑是上层问题
</action>
<action>更新 {workflow_status}：deep_dive_candidate = [true/false]</action>
```

**注意**：
- 这里 **不要**加入“快速路径反事实校验失败”作为条件。
- 这里 **不要**新增 `Step 4.5`。

##### B. 在 `Step 5` 的 `analysis_path == deep` 分支前半段加入 Stage 2/3 执行块

在现有：

```xml
<check if="analysis_path == deep">
    <load target="mobile-qa-workflow/reference/analysis-strategies.md" ... />
```

之前或刚进入 deep 分支后，插入：

```xml
<check if="deep_dive_candidate == true">
    <action>更新 {workflow_status}：deep_dive_mode = true</action>

    <check if="{workspace_folder}/deep-dive-topology.md 已存在">
        <action>读取并复用 deep-dive-topology.md，不重复生成</action>
    </check>
    <check if="{workspace_folder}/deep-dive-topology.md 不存在">
        <action>执行 Deep-Dive Stage 2：
            - 逆向状态机绘制
            - 数据流污点追踪
            - 不可变性审查
            输出 {workspace_folder}/deep-dive-topology.md
        </action>
    </check>
    <action>更新 {workflow_status}：deep_dive_stage = 2</action>

    <check if="{workspace_folder}/concurrency-analysis-report.md 已存在">
        <action>读取并复用 concurrency-analysis-report.md，不重复生成</action>
    </check>
    <check if="{workspace_folder}/concurrency-analysis-report.md 不存在">
        <action>执行 Deep-Dive Stage 3：
            - 多维时间轴对齐
            - 并发漏洞扫描
            - 符号执行推理
            输出 {workspace_folder}/concurrency-analysis-report.md
        </action>
    </check>
    <action>更新 {workflow_status}：deep_dive_stage = 3</action>

    <action>将上述两个产物的关键发现摘要追加到 {context_bundle}</action>
    <action>更新 {workflow_status}：deep_dive_artifacts += [deep-dive-topology.md, concurrency-analysis-report.md]</action>
</check>

<check if="deep_dive_candidate != true">
    <action>更新 {workflow_status}：deep_dive_mode = false</action>
</check>
```

##### C. 在 `analysis_path == fast` 升级为 deep 的地方补一段“立即执行 Stage 2/3”

定位现有逻辑：

```xml
<check if="反事实校验失败或策展回溯后仍失败">
    <action>升级到深度路径，analysis_path = deep</action>
</check>
```

改为：

```xml
<check if="反事实校验失败或策展回溯后仍失败">
    <action>升级到深度路径，analysis_path = deep</action>
    <check if="deep_dive_candidate == true">
        <action>立即执行 Deep-Dive Stage 2 + Stage 3（若产物已存在则复用）</action>
        <action>更新 {workflow_status}：deep_dive_mode = true, deep_dive_stage = 3</action>
    </check>
</check>
```

##### D. 在 Challenger 调用描述里显式增加 Stage 4 条件扩展

把原来的：

```xml
对所有 Investigator 结论执行五维质疑协议：
因果充分性 / 因果必要性 / 证据可靠性 / 遗漏假设 / 平台盲区
```

改成：

```xml
对所有 Investigator 结论执行五维质疑协议；
当 deep_dive_mode == true 时，追加执行 Deep-Dive 条件扩展维度：
生命周期盲区 / 内存泄露 / 缓存一致性
```

##### E. 在 `Step 8` 输出 RCA 前补充主根因/贡献因子描述要求

在输出 `rca-report.md` 前，新增一段 action：

```xml
<action>若存在多根因，必须收敛为：
    - Primary Root Cause（唯一主根因）
    - Contributing Factors（0-N 个贡献因子，标注关系：叠加/上游/互斥）
</action>
```

#### 不要修改的内容

- 不要在本文件中引入新的顶层 step 编号如 `4.5`。
- 不要把 Deep-Dive 抽成独立 workflow 文件并在这里跳转。
- 不要引入 `current_state = Deep-Dive-InProgress`。

---

### 1.2 `mobile-qa-workflow/phases/p2-spec-definition.md`

**优先级**：P0  
**改动目标**：加入 Stage 1 环境因子增强，但只做“机会性增强”，不提前切换 deep_dive_mode。

#### 需要修改的位置

在 `Step 7（上下文策展）` 之后、`Step 8（二位证据分级）` 之前插入新步骤 `Step 7.5`。

#### 具体修改内容

新增：

```xml
<step n="7.5" goal="Deep-Dive 环境因子增强（机会性触发）">
    <check if="主分类 == '功能' 且问题表现包含以下任一特征：
               偶发性 / 并发竞态 / 缓存一致性 / 生命周期耦合">
        <action>执行增量环境因子采集（仅补已缺失项）：
            1. 内存水位 / LMK
            2. Thermal State / 降频
            3. 网络抖动与丢包
            4. 异常前 10 秒生命周期/系统干预
            5. CPU / 磁盘 / GPU 压力
        </action>
        <action>允许标注环境因子与代码位置的关联关系，但禁止提出修复方案</action>
        <action>输出 {workspace_folder}/environment-factor-report.md</action>
        <action>将环境因子结论写入 {output_context_bundle} 的证据清单与 Deep-Dive Attachments 段落</action>
    </check>
</step>
```

#### 同步修改点

在 `Step 9 输出产物` 的描述中，补一条：

```xml
<action>若 environment-factor-report.md 存在，则在 context-bundle.md 中增加附件引用</action>
```

#### 不要修改的内容

- 不要在 P2 决定 `deep_dive_mode = true`。
- 不要把 Stage 1 的输出单独作为主编排输入路由条件。

---

### 1.3 `mobile-qa-workflow/core/workflow-status-template.yaml`

**优先级**：P0  
**改动目标**：为 Deep-Dive 提供最小可审计元字段，但不参与主编排路由。

#### 需要修改的位置

在 `# [END_PRESERVE_FORMAT]` 之前追加字段。

#### 具体修改内容

在现有：

```yaml
non_bug_reflow_count: 0
lint_retry_count: 0
```

之后追加：

```yaml
deep_dive_mode: false
deep_dive_candidate: false
deep_dive_stage: null
deep_dive_artifacts: []
```

#### 字段语义

- `deep_dive_mode`: 当前 P3/P4 是否启用 Deep-Dive 增强
- `deep_dive_candidate`: 是否命中 Deep-Dive 候选
- `deep_dive_stage`: 最近执行到哪个 Stage（1-5）
- `deep_dive_artifacts`: 已生成并可复用的 Deep-Dive 产物

#### 不要修改的内容

- 不要调整现有 YAML 结构。
- 不要新增会影响编排器判断下一阶段的字段语义。

---

### 1.4 `mobile-qa-workflow/FUNCTIONALITY_DEEP_DIVE_WORKFLOW.md`

**优先级**：P0  
**改动目标**：修复设计文档中的 4 个硬伤，并补齐“嵌入主工作流”的正式定义。

#### 需要修改的位置与内容

##### A. Stage 1 约束修改

原文：

```markdown
*   **Agent 约束**：严禁在此阶段给出任何代码修复建议，只允许输出《极端环境因子关联报告》。
```

改为：

```markdown
*   **Agent 约束**：严禁在此阶段给出修复方案，但允许标注环境因子与代码位置的关联关系，只允许输出《极端环境因子关联报告》。
```

##### B. Stage 2 约束修改

原文：

```markdown
*   **Agent 约束**：必须精确到具体的类名、方法名和代码行号，输出《全局状态与数据流向图》。
```

改为：

```markdown
*   **Agent 约束**：必须精确到具体的类名和方法名；若能定位到代码行号则必须标注，若无法定位则标注 [Line-Uncertain] 并说明推断依据。输出《全局状态与数据流向图》。
```

##### C. Stage 3 约束修改

原文：

```markdown
*   **Agent 约束**：如果推断出竞态，必须给出能够 100% 复现该竞态的"极端时序序列脚本"。
```

改为：

```markdown
*   **Agent 约束**：如果推断出竞态，必须给出高概率复现的时序序列描述（包含关键事件顺序与必要时间窗口），并标注复现概率估计（High/Medium/Low）。如需构造确定性复现路径，建议通过 Thread.sleep / CountDownLatch / 延迟注入等方式强制时序，而非依赖自然时序。
```

##### D. Stage 4 约束修改

原文：

```markdown
*   **Agent 约束**：多 Agent 对抗必须收敛于一个具有唯一逻辑自洽性的根因，否则要求补充特定的内存或时序日志。
```

改为：

```markdown
*   **Agent 约束**：多 Agent 对抗必须收敛于一个具有逻辑自洽性的根因集合（允许 1-N 个根因），各根因之间必须明确逻辑关系：独立叠加 / 因果链 / 互斥分支。最终交付时必须指定一个 Primary Root Cause，并将其余列为 Contributing Factors；若无法收敛，则要求补充特定的内存或时序日志。
```

##### E. 重写 I/O 契约章节

把当前“独立输入/独立输出”描述，改成“嵌入主工作流的增强模式”，必须包含：

1. Stage 1 -> P2 Step 7.5  
2. Stage 2/3 -> P3 Step 5 deep 分支内部  
3. Stage 4 -> Challenger 条件扩展维度  
4. Stage 5 -> P4 防御性修复附录  

并补充四个产物与主产物的对应关系：

- `environment-factor-report.md` -> `context-bundle.md` 附件
- `deep-dive-topology.md` -> `context-bundle.md` 附件
- `concurrency-analysis-report.md` -> `rca-report.md` Deep-Dive Findings
- `defensive-fix-design.md` -> `fix-design.md` Defensive Addendum

---

### 1.5 `mobile-qa-workflow/templates/context-bundle.md`

**优先级**：P1  
**改动目标**：把 Stage 1/2 产物正式挂到主产物上。

#### 需要修改的位置

在 `### 证据清单` 与 `### 信息缺口` 之间，新增一段。

#### 具体修改内容

新增：

```markdown
### Deep-Dive Attachments（可选）
- **environment-factor-report.md**: [存在/不存在] | [路径]
- **deep-dive-topology.md**: [存在/不存在] | [路径]
- **关键增强结论摘要**:
  - [环境因子结论摘要]
  - [状态机/数据流结论摘要]
```

#### 同步补充

在 `### 证据清单` 的说明后补一句：

```markdown
- 若证据来自 Deep-Dive 附件，请在“来源”列标注 `[Environment-Factor-Enhanced]` 或 `[Deep-Dive-Enhanced]`
```

---

### 1.6 `mobile-qa-workflow/templates/rca-report.md`

**优先级**：P1  
**改动目标**：让 RCA 主报告能消费并表达竞态/时序增强结论，并兼容“主根因 + 贡献因子”。

#### 需要修改的位置

1. `### 根因结论`
2. `### 推理过程` 后

#### 具体修改内容

##### A. 扩展根因结论段

把：

```markdown
- **根因描述**: ...
- **代码位置**: ...
```

扩展为：

```markdown
- **Primary Root Cause**: [唯一主根因]
- **代码位置**: [file:line — function_name]
- **Contributing Factors**:
  - [CF1] [描述] | 关系: [叠加/上游/互斥]
  - [CF2] [描述] | 关系: [...]
```

##### B. 新增 Deep-Dive Findings 段落

在 `### 分析过程摘要（深度路径时填写）` 之后新增：

```markdown
### Deep-Dive Findings（可选）
- **关联并发报告**: [concurrency-analysis-report.md 路径]
- **竞态窗口**: [RW1 / RW2 / None]
- **复现概率**: [High/Medium/Low]
- **强制复现建议**: [注入点 + 方式]
- **缓存一致性结论**: [一致 / 不一致 / 漂移类型]
- **时序精度等级**: [Microsecond / Millisecond / Order-Only]
```

---

### 1.7 `mobile-qa-workflow/templates/fix-design.md`

**优先级**：P1  
**改动目标**：让防御性修复成为正式附录入口，而不是脱离主方案。

#### 需要修改的位置

在 `### 竞争方案记录（如有多方案评估）` 之后，`### 回归测试设计` 之前，新增一段。

#### 具体修改内容

新增：

```markdown
### Defensive Addendum（可选）
- **是否启用 Deep-Dive 防御性修复附录**: [是/否]
- **附录文件**: [defensive-fix-design.md 路径]
- **启用原因**: [涉及状态机/并发/缓存一致性/生命周期耦合]
- **附录作用**: [状态加固 / 生命周期感知 / 熔断器 / 架构鲁棒性提升]
```

#### 同步补充

在评估矩阵说明附近新增一句：

```markdown
- 当启用 Defensive Addendum 时，可使用 Deep-Dive 增强评估矩阵替代标准矩阵。
```

---

### 1.8 `mobile-qa-workflow/agents/investigator.md`

**优先级**：P1  
**改动目标**：在不新增 Agent 的前提下，把 Stage 2/3 能力并入 Investigator。

#### 需要修改的位置

1. `# Capabilities`
2. `# Constraints`
3. `# Output Format`

#### 具体修改内容

##### A. 在 `# Capabilities` 末尾追加

```markdown
- **Deep-Dive 增强能力**（仅当 deep_dive_mode == true 时启用）
  - 逆向状态机绘制
  - 数据流污点追踪
  - 不可变性审查
  - 多维时间轴对齐
  - 并发漏洞扫描
  - 符号执行推理
```

##### B. 在 `# Constraints` 末尾追加

```markdown
- 当 deep_dive_mode == true 时：
  - 状态机分析必须输出 Mermaid 状态图
  - 时序分析必须给出复现概率估计
  - 类名/方法名必须精确；行号无法确定时标 [Line-Uncertain]
  - 所有 Deep-Dive 结论必须显式引用 Context Bundle 中的证据
```

##### C. 在 `# Output Format` 末尾追加补丁段

新增一个可选节：

```markdown
### DEEP-DIVE ENHANCEMENT（仅 deep_dive_mode == true 时输出）
- 状态机拓扑摘要: ...
- 数据流/脏写点摘要: ...
- 时序与竞态摘要: ...
- 复现路径摘要: ...
```

---

### 1.9 `mobile-qa-workflow/agents/challenger.md`

**优先级**：P1  
**改动目标**：把 Stage 4 作为现有质疑协议的条件扩展，而不是新协议。

#### 需要修改的位置

1. `# Capabilities` 中“归因场景”部分
2. `# Output Format`

#### 具体修改内容

##### A. 在条件两维后追加 Deep-Dive 扩展维度

新增：

```markdown
**Deep-Dive 条件扩展维度**（当 deep_dive_mode == true 时追加）：
8. 生命周期盲区攻击
9. 内存泄露攻击
10. 缓存一致性攻击
```

并分别给出 Android / iOS 示例问题句式。

##### B. 修改输出表格

在原有 `C7` 之后追加：

```markdown
| C8 | 生命周期盲区 (仅 Deep-Dive) | ... | ... | ... |
| C9 | 内存泄露 (仅 Deep-Dive) | ... | ... | ... |
| C10 | 缓存一致性 (仅 Deep-Dive) | ... | ... | ... |
```

##### C. 修改存活率说明

把：

```markdown
- 实际执行质疑维度数: M (5~7)
```

改为：

```markdown
- 实际执行质疑维度数: M (5~10，Deep-Dive 模式下为 8~10)
```

---

### 1.10 `mobile-qa-workflow/phases/p4-fix-design.md`

**优先级**：P1  
**改动目标**：让 Deep-Dive 防御性修复能够正式进入 P4，但只在条件满足时启用。

#### 需要修改的位置

在 `Step 3: 方案确认与评估矩阵` 中，标准矩阵之后新增条件分支。

#### 具体修改内容

新增：

```xml
<check if="deep_dive_mode == true 且存在 defensive-fix-design.md 或修复方案被判定为防御性修复">
    <action>使用 Deep-Dive 增强评估矩阵：
        | 维度 | 标准权重 | Deep-Dive 权重 |
        | 根因覆盖度 | 30% | 25% |
        | 副作用风险 | 25% | 20% |
        | 变更最小性 | 15% | 10% |
        | 跨平台一致性 | 10% | 10% |
        | 可回滚性 | 10% | 10% |
        | 长期可维护性 | 10% | 15% |
        | 架构鲁棒性提升 | - | 10% |
    </action>
    <action>允许在 Minimality 论证中写明“为防御性目的适度扩大变更范围”的例外说明</action>
</check>
```

#### 同步增加一个输出要求

在 `Step 6` 输出前加：

```xml
<check if="deep_dive_mode == true">
    <action>若需要防御性修复附录，则输出 {workspace_folder}/defensive-fix-design.md，并在 fix-design.md 中引用</action>
</check>
```

---

### 1.11 `mobile-qa-workflow/templates/deep-dive-topology.md`

**优先级**：P1  
**类型**：新增文件  
**改动目标**：承载 Stage 2 的状态机与数据流结果。

#### 文件内容必须包含

1. 元信息
2. 状态定义表
3. Mermaid 状态转移图
4. 孤岛状态
5. 非法跳转
6. 数据流污点追踪
7. 脏写点清单

#### 文件内容不要包含

- 不要放“时序对齐轴”
- 不要放“竞态窗口”
- 不要放“复现路径”

这些统一放到 `concurrency-analysis-report.md`。

---

### 1.12 `mobile-qa-workflow/templates/concurrency-analysis-report.md`

**优先级**：P1  
**类型**：新增文件  
**改动目标**：承载 Stage 3 的时序、竞态、隔离诊断与复现信息。

#### 文件内容必须包含

1. 元信息
2. 线程/队列模型
3. 共享资源清单
4. 竞态漏洞扫描（Android/iOS）
5. 时序对齐轴
6. 竞态窗口
7. 高概率复现路径
8. 强制复现建议
9. 缓存一致性对齐
10. 综合结论（主根因/贡献因子引用）

---

### 1.13 `mobile-qa-workflow/templates/defensive-fix-design.md`

**优先级**：P1  
**类型**：新增文件  
**改动目标**：承载 Stage 5 的防御性修复增强信息。

#### 文件内容必须包含

1. 适度性评估
2. 渐进式落地路径
3. 过度设计审查
4. 修改前状态机图
5. 修改后状态机图
6. 差异标注
7. 熔断器/断言点清单
8. 生命周期感知注入点
9. Deep-Dive 增强评估矩阵
10. Minimality 例外说明

---

### 1.14 `mobile-qa-workflow/reference/environment-factor-thresholds.md`

**优先级**：P1  
**类型**：新增文件  
**改动目标**：作为 Stage 1 环境因子分析的参考知识库。

#### 文件内容必须包含

1. Android 阈值表：
   - LMK
   - Thermal
   - Jitter
   - 丢包率
   - CPU 峰值
   - 省电模式
2. iOS 阈值表：
   - 内存/Jetsam 接近度
   - Thermal State
   - Jitter
   - 丢包率
   - CPU 峰值
   - 低电量模式
3. 时间精度降级策略：
   - Microsecond
   - Millisecond
   - Order-Only

---

## 2. 建议改但可延后文件

### 2.1 `mobile-qa-workflow/reference/analysis-strategies.md`

**优先级**：P2  
**建议改动**：
- 新增 `Strategy-StateTopology`
- 新增 `Strategy-TaintTracking`
- 新增 `Strategy-TemporalAlignment`
- 新增 `Strategy-IsolationProbing`
- 在编排器分配规则中补充：`deep_dive_mode == true` 时，至少 1 个 Deep-Dive 专项策略

**原因**：P0/P1 即使不改也能先落地，只是策略池表达不够完整。

---

### 2.2 `mobile-qa-workflow/reference/platform-checklist.md`

**优先级**：P2  
**建议改动**：
- Android 补充：
  - SharedViewModel 竞态
  - DataStore 原子性
  - WorkManager 幂等性
  - Room WAL 并发
  - Flow/SharedFlow replay 时序
  - AB 实验竞态
- iOS 补充：
  - Actor isolation
  - Sendable
  - CoreData 线程约束
  - Combine @Published 时序
  - UserDefaults KVO 时序
  - 动态库加载顺序

**原因**：属于专业深度补强，不阻塞 P0/P1 主链路打通。

---

### 2.3 `mobile-qa-workflow/reference/reasoning-chain.md`

**优先级**：P2  
**建议改动**：
- 在“功能类问题”后新增 `Deep-Dive 增强引导`
- 规定：
  - 先读 `deep-dive-topology.md`
  - 再读 `concurrency-analysis-report.md`
  - 再将 Deep-Dive 发现映射为 OBSERVE/HYPOTHESIZE 的输入

---

## 3. 明确不要修改的文件

### 3.1 `mobile-qa-workflow/core/workflow.xml`

**结论**：V2 阶段 **不要改**。  

**原因**：
- 主编排器按 `stepsCompleted + workflow-model.yaml` 决定阶段；
- 如果此时去加 `Deep-Dive-InProgress` 等状态，只会回到 V1 的错误方向；
- Deep-Dive 应在 phase 内部完成，不应通过编排器新增状态机路由。

### 3.2 `mobile-qa-workflow/core/workflow-model.yaml`

**结论**：V2 阶段 **不要改**。  

**原因**：
- 不新增 phase；
- Deep-Dive 不是第 7 阶段。

### 3.3 `mobile-qa-workflow/core/default-config.yaml`

**结论**：V2 阶段 **建议不要改**。  

**原因**：
- 现阶段文件输出路径主要由 phase 内 `{workspace_folder}/xxx.md` 控制；
- 现在去加 `output_deep_dive_*` 容易形成“配置声明了但没人消费”的伪配置。

### 3.4 `mobile-qa-workflow/system-prompt.md`

**结论**：V2 阶段 **可暂不改**。  

**原因**：
- 优先保证源工作流文件跑通；
- 等核心实现稳定后，再做 inline prompt 的同步。

---

## 4. 实施顺序建议

### 第一批（P0，先做）

1. `phases/p3-root-cause.md`
2. `phases/p2-spec-definition.md`
3. `core/workflow-status-template.yaml`
4. `FUNCTIONALITY_DEEP_DIVE_WORKFLOW.md`

### 第二批（P1，接着做）

5. `templates/context-bundle.md`
6. `templates/rca-report.md`
7. `templates/fix-design.md`
8. `agents/investigator.md`
9. `agents/challenger.md`
10. `phases/p4-fix-design.md`
11. `templates/deep-dive-topology.md`
12. `templates/concurrency-analysis-report.md`
13. `templates/defensive-fix-design.md`
14. `reference/environment-factor-thresholds.md`

---

## 5. 最终交付标准

实施完成后，至少应满足：

1. 功能类 complex 问题进入 deep 路径时，能生成或复用 `deep-dive-topology.md` 与 `concurrency-analysis-report.md`
2. fast 路径升级到 deep 后，仍能执行 Stage 2/3
3. `context-bundle.md` 能引用 `environment-factor-report.md` 与 `deep-dive-topology.md`
4. `rca-report.md` 能表达 `Primary Root Cause + Contributing Factors`
5. `fix-design.md` 能引用 `defensive-fix-design.md`
6. 全链路无需新增 `Deep-Dive-InProgress` 状态，也能恢复和审计

