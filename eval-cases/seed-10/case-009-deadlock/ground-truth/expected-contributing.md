# Expected Contributing Factors

## Contributing Factor 1: 在持有锁的回调中执行外部操作
`batchWrite` 在持有写锁时调用 callback，违反了"持有锁时不调用外部代码"的并发编程原则。

## Contributing Factor 2: EventBus 线程切换隐藏了跨线程依赖
`@Subscribe(threadMode = ThreadMode.MAIN)` 使线程切换变得隐式，开发者不易察觉回调链跨越了线程边界。

## Contributing Factor 3: View 方法使用 synchronized
`updateBadge()` 使用 `synchronized` 关键字引入了额外的锁，增加了死锁的可能性。

## Contributing Factor 4: 批量操作持有写锁时间过长
50 个 item 的批量写入可能持有写锁 1-2 秒，大幅增加了死锁时间窗口。
