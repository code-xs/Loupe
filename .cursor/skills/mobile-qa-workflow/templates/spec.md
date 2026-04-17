# Spec Document 模板

```markdown
## Spec Document — {Issue-ID}

### 基础三要素（所有分类必填）

#### Expected Behavior（预期行为）
[在什么条件下，系统应该如何表现]

#### Actual Behavior（实际行为）
[系统实际表现了什么，与预期的差异点]

#### Invariant（不变量约束）
[无论如何，系统必须满足的约束条件]

### Spec 元信息
- **Spec 来源**: [PRD / 设计稿 / 竞品参照 / 用户口述]
- **Spec 来源优先级**: 1-PRD > 2-设计稿 > 3-竞品 > 4-用户口述
- **Spec 状态**: 确认 / Spec-Uncertain
- **Spec 依赖说明**: [若为 Spec-Uncertain，列出多种可能的 Expected Behavior]

---

### 分类扩展模块（根据 Issue Card 主分类 + 次分类加载对应模块）
```

## 功能类 Spec 扩展

```markdown
### Functional Spec Extension

#### 业务规则（Business Rules）
- [BR1] 当[前置条件]时，操作[X]应产生结果[Y]
- [BR2] ...
（从 PRD/产品文档提取，若不存在则与用户/PM确认）

#### 状态转换图（State Transitions）
[当前功能涉及的状态机]
状态A --事件1--> 状态B --事件2--> 状态C
标注: 问题发生在哪个状态转换上

#### 输入输出映射（I/O Mapping）
| 输入场景 | 预期输出 | 实际输出 | 是否异常 |
|---------|---------|---------|---------|
| 正常输入 | ... | ... | |
| 边界输入 | ... | ... | |
| 异常输入 | ... | ... | |

#### 数据流关键节点（Data Checkpoints）
数据从[来源] -> [处理层1] -> [处理层2] -> [展示层]
标注: 在哪个节点数据开始偏离预期
```

## UI/UX 类 Spec 扩展

> **UI/UX 证据优先级原则**：必须以结构化数据（Layout Inspector 导出 / ConstraintLayout XML / AutoLayout 代码约束）为主要证据，截图仅作 C 级辅助参考。VLM 对移动端像素级差异（≤2dp 偏差、细微颜色差异）存在显著幻觉，不可用于精确差异判断。

```markdown
### UI/UX Spec Extension

#### 视觉参照（Visual Reference）
- 设计稿链接/截图: [Figma/Sketch/截图路径]（辅助参考）
- 实际渲染截图: [用户提供或复现截图]（辅助参考，C 级证据）
- **结构化差异描述**（主要证据，优先填写）:
  - 布局文件引用: [Layout XML / SwiftUI 代码 / XIB/Storyboard 路径]
  - Layout Inspector / View Debugger 导出: [结构化视图树数据]
  - 精确差异标注: [元素名 / 属性 / 期望值 vs 实际值]
    示例: `btnSubmit.marginBottom = 16dp (设计稿) vs 0dp (实际), 偏差 16dp`

#### 布局约束定义（Layout Constraints）
- 容器: [父容器尺寸 + 布局方式]
- 目标元素: [约束关系: 上下左右间距/对齐/比例]
- Android: [ConstraintLayout/LinearLayout 约束 XML]
- iOS: [Auto Layout constraints 代码 / Frame 计算逻辑]

#### 适配场景矩阵（Adaptation Matrix）
| 维度 | 目标值 | 实际表现 |
|------|-------|---------|
| 屏幕尺寸 | [支持范围] | [哪些尺寸异常] |
| 分辨率/密度 | [支持范围] | [哪些密度异常] |
| 暗色模式 | [是否支持] | [是否正常] |
| 动态字号 | [是否支持] | [是否正常] |
| 安全区域 | [刘海/药丸/折叠屏] | [是否适配] |
| RTL 布局 | [是否支持] | [是否正常] |

#### 动画/交互定义（若涉及）
- 动画参数: [时长/曲线/关键帧]
- 手势响应: [触发条件/响应行为]
```

## 网络类 Spec 扩展

```markdown
### Network Spec Extension

#### API 契约（API Contract）
- 接口: [Method] [URL]
- 请求体: [Schema + 必填/可选标注]
- 响应体: [成功Schema + 各错误码Schema]
- 超时策略: [连接超时/读写超时/总超时]
- 重试策略: [重试次数/退避策略/幂等性]

#### 错误处理链（Error Handling Chain）
网络层(OkHttp/URLSession) -> 协议层(HTTP状态码)
  -> 业务层(业务错误码) -> 展示层(用户提示)
标注: 在哪一层的错误处理不符合预期

#### 环境依赖（Environment Dependencies）
- 网络条件: [WiFi/4G/5G/弱网/断网]
- 代理/VPN: [是否影响]
- 证书/DNS: [是否有特殊配置]
- CDN/负载均衡: [是否涉及]

#### 并发与时序（Concurrency & Timing）
- 并发请求: [同一接口是否有并发调用？是否需要去重/排队？]
- 请求依赖链: [A完成后才能B？是否存在时序竞争？]
- 缓存策略: [本地缓存与服务端数据的一致性策略]
```

## 兼容性类 Spec 扩展

```markdown
### Compatibility Spec Extension

#### 问题设备画像（Problem Device Profile）
| 属性 | 问题设备 | 正常设备 | 差异点 |
|------|---------|---------|-------|
| 品牌/型号 | | | |
| OS版本 | | | |
| 芯片/架构 | | | |
| 屏幕参数 | | | |
| 可用内存/存储 | | | |
| 厂商定制ROM | | | |

#### API 可用性对照（API Availability）
| 使用的API | 最低支持版本 | 问题设备版本 | 是否可用 | 替代方案 |
|-----------|------------|-----------|---------|---------|
| ... | ... | ... | | |

#### 第三方 SDK 版本矩阵（若涉及）
| SDK名称 | 当前版本 | 兼容最低OS | 已知问题 |
|---------|---------|-----------|---------|
| ... | ... | ... | |
```

## 非 Bug 判定输出（若判定为非 Bug）

```markdown
### Non-Bug Resolution Report
- **判定类别**: Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate
- **判定依据**: [引用设计文档/产品确认]
- **用户沟通建议**: [如何向用户解释]
- **体验改进评估**:
  - 信号强度: 高 / 中 / 低
  - 改进方向: [Feature Request / UX Improvement / 无]
  - 派发团队: [PM / 设计团队 / 无]
```
