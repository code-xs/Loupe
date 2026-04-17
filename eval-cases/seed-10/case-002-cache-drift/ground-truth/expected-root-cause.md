# Expected Root Cause

## Primary Root Cause
**双层缓存（内存 + 磁盘）清理时序不一致导致脏读**

登出时 `clearOnLogout()` 同步清理了内存缓存（`NSCache.removeAllObjects()`），但磁盘缓存的清理被 dispatch 到全局队列异步执行。当新用户快速登录并请求 Profile 时：
1. 内存缓存已清空 → cache miss
2. 磁盘缓存清理尚未完成 → disk cache HIT（返回旧用户数据）
3. 旧数据被回填到内存缓存（`cache.setObject`），加剧了问题

## Confidence Level
**High (0.88)** — 日志显示明确的 cache HIT 行为，代码路径可追溯。但磁盘缓存清理的完成时间日志缺失，无法精确量化竞态窗口。
