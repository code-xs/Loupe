# Expected Root Cause

## Primary Root Cause
**ViewController ↔ ViewModel ↔ DanmakuManager 之间的 Closure 循环引用**

`LiveRoomViewController` 持有 `viewModel` 和 `danmakuManager`。`viewModel.onGiftReceived` closure 捕获了 `self`（ViewController），形成 VC → VM → closure → VC 的强引用环。同样，`danmakuManager.onDanmakuTap` closure 也捕获了 `self`，形成 VC → DM → closure → VC → VM 的引用环。由于循环引用，ViewController 退出后无法被 ARC 释放。

## Confidence Level
**Very High (0.98)** — Instruments 数据明确，代码路径清晰。
