# Reasoning Guide · 网络类问题

> v4.2 PR-7 / O24 / R24-1：本文件由 P3 step 5 按 issue_card 主分类「网络」命中加载，
> 与 [`reasoning-chain-core.md`](./reasoning-chain-core.md) 配套使用。
>
> **聚合契约（D-AGG-2）**：`<!-- AGG-INJECT-START -->` ~ `<!-- AGG-INJECT-END -->` 之间
> 的内容会被 `scripts/sync-reasoning-chain-aggregate.py` 注入到聚合产物
> `reference/reasoning-chain.md` 的「## 分类专项推理引导」章节内（注入顺序：
> functional → ui → network → compat）。区块外的内容仅供本文件作为独立加载入口阅读。

## 加载入口

主路径：`phases/p3-root-cause.md` step 5 起点 / invoke-subagent 内部
触发条件：`issue_card.主分类` 一级主题包含「网络」

<!-- AGG-INJECT-START -->
### 网络类问题

**OBSERVE 阶段重点**:
- 完整记录: 请求URL/Method/Headers/Body → 响应Code/Headers/Body/耗时
- 区分: 请求未发出/请求发出但无响应/响应已收到但解析失败/解析成功但业务处理失败
- 对比: 同一请求在正常/异常环境下的差异
- 时间线: 多个相关请求的发出和响应时序

**HYPOTHESIZE 阶段重点**:
- 按错误处理链逐层检查: 网络层 → 协议层 → 解析层 → 业务层 → 展示层
- 客户端 vs 服务端归属判定:
  - 服务端返回错误码 → 优先怀疑服务端/请求参数
  - 客户端超时但服务端日志正常 → 怀疑网络环境/客户端超时配置
  - 数据不一致 → 同时检查客户端缓存策略和服务端数据
- 必须检查: 请求参数拼装是否正确（尤其动态参数/签名/token过期）
- 必须检查: 是否有请求拦截器/中间件修改了请求或响应

**VERIFY 阶段重点**:
- 关键验证手段: 用相同参数直接调 API (curl/Postman) 对比结果
- 抓包: 对比客户端实际发出的请求 vs 代码中构造的请求
- 反事实: 如果是服务端问题，其他客户端(Web/其他版本)是否也有同样问题？
<!-- AGG-INJECT-END -->
