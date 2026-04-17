# Expected Contributing Factors

## Contributing Factor 1: 使用 GlobalScope 启动无管理的协程
`GlobalScope.launch` 创建的协程没有生命周期管理，也没有并发控制。

## Contributing Factor 2: 网络响应直接作为事件源
每个网络响应独立发送事件，没有在本地维护单一真相源（Single Source of Truth）。

## Contributing Factor 3: EventBus 不保证事件处理顺序
EventBus 在多线程 post 时不保证 subscriber 的接收顺序与 post 顺序一致。

## Contributing Factor 4: 缺少点击防重/节流
按钮没有节流（throttle）机制，允许极高频率的点击触发。
