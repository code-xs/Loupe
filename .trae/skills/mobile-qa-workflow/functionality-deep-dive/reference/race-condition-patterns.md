# 竞态条件常见模式参考

> 本文件为功能疑难专项子工作流 F3（时序对齐与竞态剖析）提供移动端常见竞态模式。
> Temporal Analyst 应对照本文件检查目标代码中是否存在以下模式。

## 1. Check-Then-Act (CTA)

**定义**：先检查条件是否满足，再执行操作，但两步之间状态可能被其他线程修改。

**典型场景**：
```
// Thread A
if (cache.contains(key)) {     // Check
    data = cache.get(key)       // Act — 此时 key 可能已被 Thread B 删除
}

// Thread B
cache.remove(key)               // 在 Check 和 Act 之间执行
```

**移动端高发位置**：
- 网络缓存读取前的存在性检查
- 数据库事务外的"先查后改"
- Fragment isAdded() 检查后的 UI 操作

**防御模式**：原子操作 / putIfAbsent / 事务隔离 / synchronized

## 2. Read-Modify-Write (RMW)

**定义**：读取→计算→写回三步操作非原子性，中间被其他线程的写操作打断。

**典型场景**：
```
// Thread A                     // Thread B
count = sharedState.count       // read: 5
                                count = sharedState.count  // read: 5
count = count + 1               // modify: 6
sharedState.count = count       // write: 6
                                count = count + 1          // modify: 6
                                sharedState.count = count  // write: 6 (期望 7)
```

**移动端高发位置**：
- SharedPreferences 的 read-modify-write
- 全局计数器（下载进度、未读数）
- 数据库字段的增量更新

**防御模式**：AtomicInteger / ReentrantLock / 数据库事务 / Compare-And-Swap

## 3. 回调交错 (Callback Interleaving)

**定义**：多个异步回调预期按顺序执行，但实际执行顺序不确定。

**典型场景**：
```
// 期望顺序: requestA.onSuccess -> requestB.onSuccess
// 实际可能: requestB.onSuccess -> requestA.onSuccess
// 或: requestA.onSuccess -> requestA.onSuccess (重复回调)
```

**移动端高发位置**：
- 并发网络请求的回调（无序返回）
- 多个 LiveData/Flow 的 Observer 触发顺序
- 多个 NotificationCenter Observer 的执行顺序
- RxJava/Combine 操作符链中的并发合流

**检测信号**：
- 两个回调修改同一个 UI 组件
- 回调 B 依赖回调 A 设置的状态

**防御模式**：SerialDispatchQueue / 单线程 Dispatcher / 回调编排（zip/combine）

## 4. 生命周期竞态 (Lifecycle Race)

**定义**：异步操作完成时，发起者的生命周期已发生变化（已销毁/已暂停/已 detach）。

**典型场景**：
```
// Activity 发起网络请求
api.fetchData() { result ->
    // 回调时 Activity 已被销毁
    textView.text = result  // NPE 或操作无效视图
}
```

**移动端高发位置**：
- 网络请求回调 + Activity/Fragment 销毁
- Handler.postDelayed + Activity finish
- 协程在 Activity 销毁后恢复
- iOS dealloc 后的 block 回调

**检测信号**：
- 回调中未检查 isDestroyed / isAdded / != nil
- 异步操作持有 Activity/Fragment 强引用
- CoroutineScope 未绑定 Lifecycle

**防御模式**：lifecycleScope / weak self / DisposeBag / Cancellation

## 5. 事件丢失 (Lost Event / Dropped Signal)

**定义**：事件发送时接收者尚未准备好，或事件被覆盖。

**典型场景**：
```
// 发送方
eventBus.post(DataReadyEvent)   // t=0

// 接收方
override fun onStart() {        // t=1, 晚于事件发送
    eventBus.register(this)     // 错过了 DataReadyEvent
}
```

**移动端高发位置**：
- EventBus / NotificationCenter 注册时机晚于事件发送
- LiveData.setValue 在 Observer 注册之前
- Channel.send 时无 Receiver（Rendezvous Channel）
- BroadcastReceiver 动态注册的时序窗口

**检测信号**：
- 功能"有时正常有时不正常"
- 首次启动/冷启动异常，热启动正常

**防御模式**：Sticky Event / StateFlow / replay Channel / 启动时主动拉取

## 6. 死锁与活锁 (Deadlock / Livelock)

**定义**：
- **死锁**：两个线程互相等待对方持有的资源
- **活锁**：线程不断重试但始终无法推进

**典型场景**：
```
// Deadlock
Thread A: lock(X) -> lock(Y)
Thread B: lock(Y) -> lock(X)

// Livelock
Thread A: 检测到冲突 → 回退 → 重试 → 又冲突...
Thread B: 检测到冲突 → 回退 → 重试 → 又冲突...
```

**移动端高发位置**：
- 主线程 synchronize + 子线程 runOnUiThread（Android）
- DispatchQueue.main.sync 在主线程调用（iOS）
- 数据库多连接写锁竞争
- ContentProvider 跨进程调用 + 主线程锁

**检测信号**：
- ANR (Application Not Responding)
- 界面冻结但不崩溃
- CPU 高占用但无输出

**防御模式**：固定加锁顺序 / tryLock + timeout / 异步化

## 7. 内存可见性 (Memory Visibility)

**定义**：一个线程修改的值对另一个线程不可见（CPU 缓存/编译器优化/指令重排）。

**典型场景**：
```
// Thread A
isReady = true   // 写入，但可能只在 Thread A 的 CPU 缓存中

// Thread B
while (!isReady) { /* 可能永远看到 false */ }
```

**移动端高发位置**：
- 非 volatile 的标志位用于线程间通信
- 双重检查锁 (DCL) 单例模式实现不当
- 跨线程共享的配置/状态对象

**检测信号**：
- "偶尔读到旧值" 的表现
- Release 模式下出现但 Debug 模式下不出现

**防御模式**：volatile / Atomic / @Synchronized / Memory Barrier

## 使用指南

Temporal Analyst 应在分析过程中：
1. 逐一对照上述 7 种模式排查可疑代码
2. 对每个发现标注模式编号（如 `[Pattern-4: Lifecycle Race]`）
3. 标注复现概率：High / Medium / Low
4. 区分已证实的竞态 vs 推断的竞态
5. 在结论中说明哪些模式与当前异常直接相关
