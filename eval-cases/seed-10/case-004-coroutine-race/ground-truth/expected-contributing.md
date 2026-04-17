# Expected Contributing Factors

## Contributing Factor 1: 服务端缺少幂等性保护
订单提交 API 没有幂等性 key（如 `Idempotency-Key` header），相同内容的两次请求被视为两个独立订单。

## Contributing Factor 2: RetryInterceptor 未感知业务语义
重试拦截器是通用的网络层组件，不区分幂等请求（GET）和非幂等请求（POST /order/submit）。

## Contributing Factor 3: 未使用 OkHttp Call.cancel()
协程取消时没有同步调用 `Call.cancel()` 来中断底层网络请求。
