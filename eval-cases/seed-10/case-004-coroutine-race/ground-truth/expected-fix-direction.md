# Expected Fix Direction

## Primary Fix
1. **协程取消时同步取消 OkHttp Call**：使用 `suspendCancellableCoroutine` 包装网络调用，在 `invokeOnCancellation` 中调用 `call.cancel()`
2. **服务端添加幂等性保护**：客户端生成唯一 `Idempotency-Key`，服务端在 5 分钟窗口内对相同 key 返回缓存结果

## Defensive Fixes
1. RetryInterceptor 检查请求 method，非幂等请求（POST/PUT/DELETE）不自动重试
2. 订单提交增加本地防重标记（提交中状态持久化到 SharedPreferences）
3. 提交按钮增加不可重入锁，防止快速多次点击
