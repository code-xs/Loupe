# Expected Root Cause

## Primary Root Cause
**VideoPlayerPool 异步回收与同步获取之间的状态机竞态条件**

在 v28.5.0 的性能优化中（PR #4521），`VideoPlayerPool.recycleDistantPlayers()` 被改为异步执行播放器释放操作。然而 `acquirePlayer()` 方法在触发异步释放后，立即同步尝试获取空闲播放器。由于释放操作尚未完成（状态仍为 `RELEASING`），所有播放器都处于不可用状态，导致 `getIdlePlayer()` 返回 null，最终表现为视频黑屏。

## Root Cause 详细分析

### 竞态窗口
```
Timeline:
T0: onPageSelected(7) → acquirePlayer(7)
T1: recycleDistantPlayers(7) → 异步 release(player_for_pos_4) [状态: PLAYING→RELEASING]
T2: getIdlePlayer() → null [所有 player 都在 RELEASING 状态]  ← 竞态窗口
T3: acquirePlayer returns null → 黑屏
T4: (100-500ms later) release callback → player_for_pos_4 状态: RELEASING→RELEASED→IDLE
    ← 此时已经晚了，没有重试机制
```

### 根因链
1. **直接原因**: `acquirePlayer()` 在所有播放器处于 `RELEASING` 状态时返回 null
2. **触发条件**: 异步回收 + 同步获取的时序不一致
3. **设计缺陷**: 状态机缺少 `RELEASING` 状态下的等待/重试机制
4. **架构缺陷**: `recycleDistantPlayers()` 的异步化未同步更新 `acquirePlayer()` 的获取逻辑

## Confidence Level
**High (0.92)** — 日志明确显示状态冲突，代码路径可追溯，时间窗口与复现条件吻合。
