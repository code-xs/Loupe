# Expected Root Cause

## Primary Root Cause
**并发网络请求响应乱序 + EventBus 无序事件投递导致最终状态不一致**

每次点击"加入购物车"都启动一个独立的协程发起网络请求。由于网络响应时间不确定，5 个请求的响应可能以任意顺序返回。每个响应都通过 EventBus 发送 `CartUpdatedEvent`，badge 直接使用最后收到的事件中的 `count` 值。如果最后到达的不是 count=5 的事件（例如 count=3 的响应最后到达），badge 就会显示错误的数字。

## 根因本质
事件驱动架构中缺少事件版本控制或时序保证机制，导致后发先至的"旧"事件覆盖了"新"事件的状态。

## Confidence Level
**High (0.92)**
