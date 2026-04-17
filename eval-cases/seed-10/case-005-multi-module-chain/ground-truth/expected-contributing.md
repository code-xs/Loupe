# Expected Contributing Factors

## Contributing Factor 1: AuthManager 初始化未提供就绪回调
`init()` 方法不返回 Future/Promise/Callback，调用方无法等待初始化完成。

## Contributing Factor 2: NativeBridge 未实现等待机制
`getAuthInfo()` 是同步返回的，不支持"等待 AuthManager 就绪后再返回"的模式。

## Contributing Factor 3: H5 页面无错误重试逻辑
WebView 中的 H5 页面在鉴权失败时直接显示空白，没有重试机制或错误提示页。

## Contributing Factor 4: Router 未区分冷启动和热启动
DeepLink 路由在冷启动和热启动时使用相同逻辑，没有冷启动时的初始化等待策略。

## Contributing Factor 5: 推送 SDK 在 Application.onCreate 中过早触发 Intent
推送 SDK 的 Intent 处理在 `Application.onCreate()` 返回后立即执行，未给应用留出初始化窗口。
