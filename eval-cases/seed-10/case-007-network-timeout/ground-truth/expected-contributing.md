# Expected Contributing Factors

## Contributing Factor 1: 无 loading 状态管理
ViewModel 没有管理 loading/error/success 状态，用户看不到任何加载提示。

## Contributing Factor 2: 默认超时过长
网络请求默认超时 30 秒，对于首页核心体验场景不合理。

## Contributing Factor 3: 无缓存降级
首次加载无本地缓存可用，后续加载也没有 stale-while-revalidate 策略。
