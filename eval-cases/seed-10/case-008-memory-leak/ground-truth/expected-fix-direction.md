# Expected Fix Direction

## Primary Fix
在所有 closure 中使用 `[weak self]`：
```swift
viewModel.onGiftReceived = { [weak self] gift in
    guard let self = self else { return }
    self.showGiftAnimation(gift)
    self.danmakuManager.addGiftDanmaku(gift)
}
```

## Secondary Fixes
1. 在 `viewWillDisappear` 中将 closure 置为 nil 作为额外保护
2. 添加 Debug 模式下的 deinit 断言检查
3. 集成 MLeaksFinder 或类似工具做 CI 泄漏检测
