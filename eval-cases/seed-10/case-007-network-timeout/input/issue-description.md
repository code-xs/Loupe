# 首页 Feed 流加载超时导致白屏 10 秒以上

## 问题概述
用户在弱网环境或首次冷启动时，首页 Feed 流出现长时间白屏（>10s），无 loading 指示器，无缓存兜底。

## 复现环境
- **设备**: Android + iOS
- **网络**: 弱网（3G / 高延迟 WiFi）或首次安装冷启动

## 复现步骤
1. 清除 APP 缓存（或首次安装）
2. 将网络设置为 3G 模式（或使用代理模拟 3000ms 延迟）
3. 打开 APP
4. 观察：首页白屏超过 10 秒

## 日志信息
```
[08:00:00.000] [App] Cold start, no local cache
[08:00:00.100] [Feed] Requesting feed data...
[08:00:00.101] [Network] GET /api/v2/feed — timeout=30000ms
[08:00:10.101] [Network] GET /api/v2/feed — still waiting (10s elapsed)
[08:00:15.200] [Network] GET /api/v2/feed — response received (15.1s)
[08:00:15.201] [Feed] Feed data loaded, rendering 20 items
```

## 相关代码
```kotlin
class FeedRepository {
    suspend fun getFeed(): FeedResponse {
        // 无缓存策略，直接请求网络
        return apiService.getFeed()  // 默认超时 30s
    }
}

class FeedViewModel : ViewModel() {
    fun loadFeed() {
        viewModelScope.launch {
            // 无 loading 状态管理
            val feed = feedRepository.getFeed()
            _feedData.value = feed
        }
    }
}
```
