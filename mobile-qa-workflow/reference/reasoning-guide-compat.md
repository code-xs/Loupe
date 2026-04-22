# Reasoning Guide · 兼容性类问题

> v4.2 PR-7 / O24 / R24-1：本文件由 P3 step 5 按 issue_card 主分类「兼容 / 兼容性*」命中加载，
> 与 [`reasoning-chain-core.md`](./reasoning-chain-core.md) 配套使用。
>
> **聚合契约（D-AGG-2）**：`<!-- AGG-INJECT-START -->` ~ `<!-- AGG-INJECT-END -->` 之间
> 的内容会被 `scripts/sync-reasoning-chain-aggregate.py` 注入到聚合产物
> `reference/reasoning-chain.md` 的「## 分类专项推理引导」章节内（注入顺序：
> functional → ui → network → compat）。区块外的内容仅供本文件作为独立加载入口阅读。

## 加载入口

主路径：`phases/p3-root-cause.md` step 5 起点 / invoke-subagent 内部
触发条件：`issue_card.主分类` 一级主题包含「兼容」或「兼容性*」

<!-- AGG-INJECT-START -->
### 兼容性类问题

**OBSERVE 阶段重点**:
- 精确的设备差异对比: 问题设备 vs 正常设备的参数逐项比对
- 确认问题的"设备边界": 同品牌不同型号？同OS不同版本？同版本不同品牌？
- 检查是否与厂商定制行为相关（权限管理/后台限制/通知策略）

**HYPOTHESIZE 阶段重点**:
- API 可用性: 使用了高版本 API 但未做版本检查/降级？
- 厂商差异: 厂商ROM修改了标准行为（常见于通知/后台/权限/存储）？
- 硬件差异: GPU渲染差异/摄像头API差异/传感器精度差异？
- SDK 冲突: 不同 SDK 版本间的二进制兼容性/资源冲突/初始化顺序？
- Android 碎片化: targetSdkVersion 升级带来的行为变更？
- iOS 版本: 系统行为变更（如 iOS 隐私策略/后台模式/推送机制迭代）？

**VERIFY 阶段重点**:
- 关键验证手段: 在问题设备上用条件编译/动态配置绕过可疑代码
- 反事实: 如果是 API X 的兼容性问题，是否只有使用了 API X 的功能受影响？
- 对照: 同一设备上的其他 App 是否有类似问题？（区分App问题和系统问题）
<!-- AGG-INJECT-END -->
