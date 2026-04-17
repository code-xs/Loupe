# Expected Root Cause

## Primary Root Cause
**经典 ABBA 死锁：数据库写锁回调中触发 UI 更新，UI 更新又需要数据库读锁**

死锁形成路径：
1. `db-writer-1` 线程持有数据库写锁，执行批量写入完成后，在写锁持有期间调用 `callback.onBatchComplete()`
2. 回调通过 EventBus 在主线程触发 `CollectionBadgeView.onCollectionChanged()`
3. `updateBadge()` 被 `synchronized` 修饰（持有 View 对象锁），并调用 `getCollectionCount()` 需要数据库读锁
4. 同时，主线程的 `updateBadge()` 已持有 View 锁，但需要的读锁被写锁阻塞
5. `db-writer-1` 的回调需要在主线程执行 UI 操作（隐式等待主线程），但主线程在等待读锁
6. 形成循环等待 → 死锁

## Confidence Level
**Medium-High (0.82)** — ANR 堆栈明确显示死锁，但日志在 ANR 后截断，无法确认所有触发路径。
