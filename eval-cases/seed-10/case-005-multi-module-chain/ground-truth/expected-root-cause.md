# Expected Root Cause

## Primary Root Cause
**APP 冷启动时模块初始化顺序与 DeepLink 路由执行的时序错配**

在冷启动场景下，推送点击触发的 DeepLink 路由会在 `Application.onCreate()` 之后立即执行。路由将用户导航到 HybridActivity，WebView 加载并通过 Native Bridge 请求鉴权信息。但此时 `AuthManager` 的异步初始化尚未完成（Token 从 Keystore 加载需约 1 秒），导致 `getToken()` 返回 null，H5 页面因 401 错误显示白屏。

核心问题是四个模块（Push Handler → Router → WebView → Native Bridge → AuthManager）之间缺少就绪状态同步机制。

## Confidence Level
**High (0.93)**
