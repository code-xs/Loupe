# 直播间 Closure 循环引用导致内存泄漏

## 问题概述
用户反复进出直播间后，APP 内存持续上涨不释放。进出 5 次后内存增长约 200MB，最终触发 OOM 被系统杀掉。

## 复现环境
- **设备**: iPhone 13 (iOS 17.2)
- **APP 版本**: v16.0.0

## 复现步骤
1. 打开 APP，进入一个直播间
2. 观看 5 秒后退出
3. 重复步骤 1-2 共 5 次
4. 使用 Instruments 观察：LiveRoomViewController 的实例数为 5（未被释放）

## Instruments 数据
```
Instance Count for LiveRoomViewController: 5 (expected: 0)
Instance Count for LiveRoomViewModel: 5 (expected: 0)
Instance Count for DanmakuManager: 5 (expected: 0)
Memory growth: ~40MB per enter-exit cycle
```

## 相关代码

### LiveRoomViewController.swift
```swift
class LiveRoomViewController: UIViewController {
    private let viewModel = LiveRoomViewModel()
    private let danmakuManager = DanmakuManager()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        viewModel.onGiftReceived = { gift in
            // 问题: 未使用 [weak self]，self 被 closure 强引用
            self.showGiftAnimation(gift)
            self.danmakuManager.addGiftDanmaku(gift)
        }
        
        danmakuManager.onDanmakuTap = { danmaku in
            self.viewModel.reportDanmakuInteraction(danmaku)
        }
    }
    
    deinit {
        print("LiveRoomViewController deinit")  // 永远不会被调用
    }
}
```

### LiveRoomViewModel.swift
```swift
class LiveRoomViewModel {
    var onGiftReceived: ((Gift) -> Void)?
    // ViewModel 持有 closure，closure 捕获 ViewController → 循环引用
}
```
