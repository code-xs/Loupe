# Expected Fix Direction

## Primary Fix
**在 `acquirePlayer()` 中引入异步等待机制**：当所有播放器处于 `RELEASING` 状态时，不立即返回 null，而是注册一个 release completion callback，在任一播放器释放完成后自动重试获取。

```java
public void acquirePlayer(int position, PlayerCallback callback) {
    VideoPlayer player = getIdlePlayer();
    if (player != null) {
        player.prepare(position);
        callback.onPlayerReady(player);
        return;
    }
    // 注册等待回调，而非直接返回 null
    pendingRequests.add(new PendingRequest(position, callback));
}
```

## Defensive Fixes
1. **状态机增加 RELEASING_PENDING 子状态**：允许在 RELEASING 状态下排队新的 prepare 请求
2. **添加 onPageSelected 节流**：限制回调处理频率（最小间隔 100ms）
3. **播放器池超时兜底**：RELEASING 状态超过 2s 未完成时强制重置为 IDLE
4. **Surface 生命周期解耦**：SurfaceTexture detach 改为延迟执行，不阻塞状态机转换
