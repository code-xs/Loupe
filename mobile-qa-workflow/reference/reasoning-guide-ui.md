# Reasoning Guide · UI/UX 类问题

> v4.2 PR-7 / O24 / R24-1：本文件由 P3 step 5 按 issue_card 主分类「UI / UI/UX / 交互」命中加载，
> 与 [`reasoning-chain-core.md`](./reasoning-chain-core.md) 配套使用。
>
> **聚合契约（D-AGG-2）**：`<!-- AGG-INJECT-START -->` ~ `<!-- AGG-INJECT-END -->` 之间
> 的内容会被 `scripts/sync-reasoning-chain-aggregate.py` 注入到聚合产物
> `reference/reasoning-chain.md` 的「## 分类专项推理引导」章节内（注入顺序：
> functional → ui → network → compat）。区块外的内容仅供本文件作为独立加载入口阅读。

## 加载入口

主路径：`phases/p3-root-cause.md` step 5 起点 / invoke-subagent 内部
触发条件：`issue_card.主分类` 一级主题包含「UI」「UI/UX」或「交互」

<!-- AGG-INJECT-START -->
### UI/UX 类问题

**OBSERVE 阶段重点**:
- 精确标注视觉差异: 位置偏移(px/dp)、尺寸错误、颜色/字号不匹配、间距异常
- 区分静态渲染问题 vs 动态布局问题（数据加载后才出现）
- 区分全局问题（所有页面）vs 局部问题（特定页面/组件）
- 检查 Layout Inspector/View Debugger 中的实际约束值

**HYPOTHESIZE 阶段重点**:
- 优先考虑: 硬编码数值/约束缺失/约束冲突/资源适配不全(mdpi/hdpi/...)
- 动态问题优先考虑: 异步数据回来后的布局更新时机/measure-layout 循环
- 适配问题优先考虑: 安全区域计算/状态栏/导航栏高度/折叠屏状态
- Android 特有: dp/sp/px 转换 / ConstraintLayout barrier/guideline
- iOS 特有: safeAreaInsets / intrinsicContentSize / Auto Layout 优先级

**VERIFY 阶段重点**:
- 关键验证手段: 在多种屏幕尺寸/密度下复现对比
- 反事实: 如果是约束X导致的问题，修改该约束后布局是否正常？
- 对照: 问题元素在其他页面的同类使用是否也有问题？
<!-- AGG-INJECT-END -->
