# Expected Fix Direction

## Primary Fix
**在 Router 中实现冷启动初始化等待机制**：
```java
class Router {
    void route(DeepLink link) {
        if (AppInitializer.isColdStart() && !AppInitializer.isCriticalModulesReady()) {
            AppInitializer.onReady(() -> routeInternal(link));  // 延迟路由
        } else {
            routeInternal(link);
        }
    }
}
```

## Defensive Fixes
1. AuthManager 改为 `CompletableFuture` 模式，支持阻塞等待
2. NativeBridge.getAuthInfo 支持异步回调模式
3. H5 页面增加鉴权失败重试（最多 3 次，间隔 500ms）
4. 冷启动增加全局 SplashScreen 等待关键模块就绪
5. 推送 SDK 的 DeepLink 处理延迟到 `onActivityStarted` 之后
