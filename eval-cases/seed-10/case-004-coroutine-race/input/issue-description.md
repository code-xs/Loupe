# Kotlin 协程取消与网络回调竞态导致订单重复提交

## 问题概述
用户在订单确认页面点击"提交订单"后，由于网络延迟较高（>3s），用户误以为未成功而快速按返回键退出页面。结果发现订单被提交了两次，账户被扣了两次款。

## 复现环境
- **设备**: Android / iOS 均受影响
- **APP 版本**: v20.1.0
- **网络**: 弱网环境（RTT > 3000ms）

## 复现步骤
1. 使用网络代理工具将延迟设置为 3-5 秒
2. 进入订单确认页面，点击"提交订单"
3. 等待 1-2 秒（按钮已灰化，请求已发出但未响应）
4. 按系统返回键退出订单页面
5. 返回首页后约 2-3 秒收到两次"订单提交成功"通知

## 日志信息
```
[11:00:00.000] [Order] Submit button clicked, starting order submission
[11:00:00.001] [Order] Coroutine launched in viewModelScope
[11:00:00.002] [Network] POST /api/v1/order/submit — request sent
[11:00:01.500] [Lifecycle] OrderActivity.onDestroy() — user pressed back
[11:00:01.501] [ViewModel] OrderViewModel cleared, viewModelScope cancelled
[11:00:01.502] [Coroutine] Job cancelled: StandaloneCoroutine{Cancelling}
[11:00:03.200] [Network] POST /api/v1/order/submit — response 200 OK (orderId=ORD-12345)
[11:00:03.201] [Order] ⚠️ Order response received AFTER coroutine cancellation
[11:00:03.202] [Network] OkHttp callback delivered on background thread (not coroutine)
[11:00:03.203] [Order] Order callback handler: retrying submission (treated as no-response)
[11:00:03.204] [Network] POST /api/v1/order/submit — DUPLICATE request sent
[11:00:06.400] [Network] POST /api/v1/order/submit — response 200 OK (orderId=ORD-12346) ← 重复订单！
```

## 相关代码片段

### OrderViewModel.kt
```kotlin
class OrderViewModel : ViewModel() {
    fun submitOrder(orderData: OrderData) {
        viewModelScope.launch {
            try {
                val result = orderRepository.submit(orderData)
                _orderResult.value = Result.success(result)
            } catch (e: CancellationException) {
                // 协程被取消，不处理
                throw e
            } catch (e: Exception) {
                _orderResult.value = Result.failure(e)
            }
        }
    }
}
```

### OrderRepository.kt
```kotlin
class OrderRepository(private val api: OrderApi, private val okHttpClient: OkHttpClient) {
    suspend fun submit(order: OrderData): OrderResult {
        return withContext(Dispatchers.IO) {
            api.submitOrder(order)  // Retrofit suspend function
        }
    }
    
    // 问题: OkHttp 还注册了一个全局 Interceptor 做失败重试
    init {
        okHttpClient.interceptors().add(RetryInterceptor(maxRetries = 1))
    }
}
```

### RetryInterceptor.kt
```kotlin
class RetryInterceptor(private val maxRetries: Int) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var response: Response? = null
        var exception: IOException? = null
        
        for (i in 0..maxRetries) {
            try {
                response = chain.proceed(chain.request())
                if (response.isSuccessful) return response
            } catch (e: IOException) {
                exception = e
                // 重试 — 但不检查调用方的取消状态
            }
        }
        throw exception ?: IOException("Unknown error")
    }
}
```
