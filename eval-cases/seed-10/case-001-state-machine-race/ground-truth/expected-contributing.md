# Expected Contributing Factors

## Contributing Factor 1: SurfaceTexture 复用机制引入的额外延迟
PR #4498 引入的 SurfaceTexture 复用机制，在播放器释放时增加了 Surface detach 的额外操作，使得 `RELEASING → RELEASED` 的转换时间从原来的 ~20ms 增加到 ~50-100ms，扩大了竞态窗口。

## Contributing Factor 2: 低端设备内存压力导致 GC 暂停
在 3GB RAM 设备上，APP 内存占用 2.1GB 时频繁触发 GC，GC 暂停会进一步延迟异步释放回调的执行，使竞态窗口从 ~50ms 扩大到 ~200ms，解释了低端设备上复现率更高的现象。

## Contributing Factor 3: ViewPager2 快速滑动回调频率
ViewPager2 在快速滑动时，`onPageSelected` 回调的触发频率可能超过播放器状态机的处理能力（>3次/秒），但没有任何节流（throttle）或去抖（debounce）机制。

## Contributing Factor 4: 缺少播放器获取失败的重试/降级策略
`acquirePlayer()` 返回 null 后没有任何重试或降级逻辑，直接放弃了该位置的视频播放，也没有注册回调在播放器可用时重新尝试。
