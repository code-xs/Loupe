# 数据库读写锁与 UI 线程同步回调导致死锁

## 问题概述
APP 偶发出现 ANR（Application Not Responding），ANR 日志显示主线程阻塞在数据库锁等待上。问题在数据密集型操作（如批量收藏、批量删除）后更容易出现。

## 复现环境
- **设备**: 各种 Android 设备
- **APP 版本**: v22.0.0
- **复现率**: <1%，但 APM 上每天约 50 例

## ANR 堆栈
```
"main" prio=5 tid=1 Blocked
  | group="main" sCount=1 dsCount=0
  | held mutexes=
  at com.app.data.AppDatabase.query(AppDatabase.java:78)
  - waiting to lock <0x0f6a8b30> (a java.util.concurrent.locks.ReentrantReadWriteLock$WriteLock)
  - locked by thread "db-writer-1"
  at com.app.feature.collection.CollectionRepository.getCollectionCount(CollectionRepository.java:45)
  at com.app.feature.collection.CollectionBadgeView.updateBadge(CollectionBadgeView.java:30)
  at com.app.feature.collection.CollectionBadgeView.onCollectionChanged(CollectionBadgeView.java:25)
  // ... 由 EventBus 在主线程回调

"db-writer-1" prio=5 tid=15 Blocked
  | group="main" sCount=1 dsCount=0
  at com.app.feature.collection.CollectionBadgeView.updateBadge(CollectionBadgeView.java:30)
  - waiting to lock <0x0f7c2e40> (a android.view.View) [UI 操作需要主线程]
  at com.app.data.AppDatabase$BatchWriteCallback.onBatchComplete(AppDatabase.java:156)
  - locked <0x0f6a8b30> (a java.util.concurrent.locks.ReentrantReadWriteLock$WriteLock)
```

## 日志信息（有限）
```
[14:30:00.000] [DB] Batch write started: 50 items
[14:30:00.500] [DB] Write lock acquired by db-writer-1
[14:30:01.000] [DB] Batch write progress: 25/50
[14:30:01.500] [DB] Batch write complete, invoking callback...
[14:30:01.501] [EventBus] Posting CollectionChangedEvent on main thread
--- ANR occurs here, no more logs ---
```

## 相关代码

### AppDatabase.java
```java
public class AppDatabase {
    private final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
    
    public List<Item> query(String sql) {
        rwLock.readLock().lock();  // 主线程可能在这里阻塞
        try { return doQuery(sql); }
        finally { rwLock.readLock().unlock(); }
    }
    
    public void batchWrite(List<Item> items, BatchWriteCallback callback) {
        rwLock.writeLock().lock();  // 写锁
        try {
            doWrite(items);
            callback.onBatchComplete();  // 回调在持有写锁时执行！
        } finally {
            rwLock.writeLock().unlock();
        }
    }
}
```

### CollectionBadgeView.java
```java
public class CollectionBadgeView extends View {
    @Subscribe(threadMode = ThreadMode.MAIN)
    public void onCollectionChanged(CollectionChangedEvent event) {
        updateBadge();
    }
    
    private synchronized void updateBadge() {
        int count = collectionRepository.getCollectionCount();  // 需要读锁
        setText(String.valueOf(count));
    }
}
```

## 死锁分析
```
Thread Main:  持有 View 锁 → 等待读锁 (被 db-writer-1 的写锁阻塞)
Thread db-writer-1:  持有写锁 → callback → EventBus post to Main → 等待 View 锁
= 经典 ABBA 死锁
```
