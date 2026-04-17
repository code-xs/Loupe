# Expected Root Cause

## Primary Root Cause
**协程取消未能阻止底层 OkHttp 请求的执行和重试**

当用户退出页面时，`viewModelScope` 被取消，但底层 OkHttp 的网络请求已经在独立线程中执行。Kotlin 协程的取消是协作式的，OkHttp 的 `Call` 对象不会因为协程取消而自动中断。更严重的是，`RetryInterceptor` 在捕获到 IOException（由请求取消引起）后，会自动重试请求，导致订单被第二次提交。

## 根因链
1. 协程取消 → Retrofit 的 suspend 函数抛出 CancellationException
2. 但 OkHttp Call 已在 IO 线程独立执行，第一次请求实际已到达服务端
3. 协程取消导致的 socket 关闭可能触发 IOException
4. RetryInterceptor 捕获 IOException → 自动重发请求 → 重复订单

## Confidence Level
**High (0.90)**
