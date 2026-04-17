# Expected Fix Direction

## Primary Fix
**将回调移到锁外执行**：
```java
public void batchWrite(List<Item> items, BatchWriteCallback callback) {
    rwLock.writeLock().lock();
    try {
        doWrite(items);
    } finally {
        rwLock.writeLock().unlock();
    }
    callback.onBatchComplete();  // 锁已释放后再回调
}
```

## Defensive Fixes
1. 移除 `updateBadge()` 的 `synchronized`，改用主线程单线程模型保证安全
2. `getCollectionCount()` 改为异步调用，不在 UI 回调中同步查库
3. 数据库写入改用 WAL 模式，减少读写锁冲突
4. 添加死锁检测机制（StrictMode 或自定义 watchdog）
