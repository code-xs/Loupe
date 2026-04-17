# 视频播放器状态机竞态导致黑屏卡死

## 问题概述
用户在短视频 Feed 流中快速上下滑动时，偶发出现视频画面黑屏、播放器卡死的现象。此时 UI 线程仍然响应（可以继续滑动），但当前视频位永远无法恢复播放，需要滑走再滑回才能恢复。问题在高端和低端设备上均可复现，但低端设备（内存 < 4GB）上复现率显著更高（约 15% vs 3%）。

## 复现环境
- **设备**: Samsung Galaxy A14 (Android 13, 3GB RAM) / Pixel 7 (Android 14, 8GB RAM)
- **APP 版本**: v28.5.0 (Build 28050123)
- **OS 版本**: Android 13 / 14
- **网络**: WiFi + 4G 均可复现

## 复现步骤
1. 打开 APP，进入短视频 Feed 流
2. 快速连续上滑 5-8 个视频（滑动速度 > 3 个视频/秒）
3. 在第 6-8 个视频处停下
4. 观察：当前视频黑屏，进度条显示 00:00，无声音输出
5. 等待 10 秒无自动恢复
6. 上滑离开再下滑回来，视频恢复正常

## 复现率
- 低端设备（RAM < 4GB）：约 15%（20 次中 3 次）
- 高端设备（RAM >= 6GB）：约 3%（30 次中 1 次）

## 日志信息

### Logcat 关键日志（复现时刻 ±2s）
```
2026-04-15 14:32:05.123 E/VideoPlayer: [StateMachine] Illegal transition: PREPARING -> PAUSED (current=RELEASING)
2026-04-15 14:32:05.124 W/VideoPlayer: [StateMachine] Transition rejected, state locked at RELEASING
2026-04-15 14:32:05.125 E/VideoPlayer: [PlayerPool] Cannot acquire player for position=7, all players in RELEASING state
2026-04-15 14:32:05.130 W/VideoPlayer: [Surface] SurfaceTexture detached but player state is PREPARING
2026-04-15 14:32:05.131 E/VideoPlayer: [Renderer] No valid surface for rendering, frame dropped
2026-04-15 14:32:05.235 D/VideoPlayer: [StateMachine] State=RELEASING, pending_ops=[prepare(pos=7), release(pos=4)]
2026-04-15 14:32:05.340 W/VideoPlayer: [PlayerPool] Deadlock detected: player_3 waiting for release callback, player_1 waiting for prepare callback
2026-04-15 14:32:06.125 E/VideoPlayer: [StateMachine] Timeout waiting for RELEASED state (1000ms elapsed)
2026-04-15 14:32:06.126 W/VideoPlayer: [Recovery] Force reset attempted but surface already detached
```

### APM 数据
- 事件链：`onPageSelected(pos=7)` → `preparePlayer(7)` → `releasePlayer(4)` → **状态冲突**
- 时间戳分析：`preparePlayer(7)` 和 `releasePlayer(4)` 在 2ms 内先后被调用
- 线程分析：`preparePlayer` 在 Main Thread，`releasePlayer` 在 PlayerThread
- 内存快照：触发时 APP 内存占用 2.1GB（低端设备总内存 3GB）

### 堆栈信息
```
java.lang.IllegalStateException: Cannot prepare player in RELEASING state
    at com.app.video.player.VideoStateMachine.transition(VideoStateMachine.java:156)
    at com.app.video.player.VideoPlayerPool.acquirePlayer(VideoPlayerPool.java:89)
    at com.app.video.feed.FeedVideoManager.onPageSelected(FeedVideoManager.java:234)
    at androidx.viewpager2.widget.ViewPager2$4.onPageSelected(ViewPager2.java:256)
```

## 相关代码片段

### VideoStateMachine.java (核心状态机)
```java
public class VideoStateMachine {
    private volatile PlayerState currentState = PlayerState.IDLE;
    private final Object stateLock = new Object();
    
    public boolean transition(PlayerState target) {
        synchronized (stateLock) {
            if (!isValidTransition(currentState, target)) {
                Log.e(TAG, "Illegal transition: " + currentState + " -> " + target);
                return false;
            }
            currentState = target;
            return true;
        }
    }
    
    // 状态转换表：IDLE -> PREPARING -> PREPARED -> PLAYING -> PAUSED -> RELEASING -> RELEASED -> IDLE
    // 问题：RELEASING 状态下不允许任何其他转换，但 release 是异步回调
}
```

### VideoPlayerPool.java (播放器池)
```java
public class VideoPlayerPool {
    private final Map<Integer, VideoPlayer> activePlayers = new ConcurrentHashMap<>();
    
    public VideoPlayer acquirePlayer(int position) {
        // 先尝试回收最远的播放器
        recycleDistantPlayers(position);  // 这会触发 release
        
        // 再获取新播放器 — 问题：recycleDistantPlayers 中的 release 是异步的
        VideoPlayer player = getIdlePlayer();
        if (player == null) {
            Log.e(TAG, "Cannot acquire player, all in RELEASING state");
            return null;  // 导致黑屏
        }
        player.prepare(position);
        return player;
    }
}
```

### FeedVideoManager.java (Feed 管理器)
```java
public void onPageSelected(int position) {
    // 快速滑动时，此回调可能在短时间内被连续调用多次
    videoPlayerPool.acquirePlayer(position);  // 同步调用，但内部有异步操作
}
```

## 用户反馈
- "快速划视频的时候经常黑屏，要划走再划回来才行"
- "之前的版本没这个问题，最近更新后开始的"（v28.4.0 → v28.5.0）

## 历史变更
- v28.5.0 中将 PlayerPool 从同步回收改为异步回收（性能优化 PR #4521）
- 同版本引入了 SurfaceTexture 复用机制（PR #4498）
