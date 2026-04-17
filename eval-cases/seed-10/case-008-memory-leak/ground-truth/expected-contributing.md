# Expected Contributing Factors

## Contributing Factor 1: 多个 closure 同时形成循环引用
不仅 `onGiftReceived`，`onDanmakuTap` 也形成了独立的循环引用，两条引用环叠加。

## Contributing Factor 2: 缺少 deinit 监控
生产环境中没有 deinit 监控或内存泄漏检测机制，导致问题长时间未被发现。

## Contributing Factor 3: 直播间资源较重
每个 LiveRoomViewController 实例持有视频解码器、弹幕渲染器等重资源，单次泄漏约 40MB。
