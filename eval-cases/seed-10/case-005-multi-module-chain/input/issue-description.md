# 推送-路由-WebView-Native 四模块联动导致页面白屏

## 问题概述
用户点击推送通知后，APP 通过 DeepLink 路由到一个 Hybrid 页面（WebView）。该页面加载后调用 Native Bridge 获取用户鉴权信息，但在 APP 冷启动场景下，Native Bridge 返回空数据，导致 WebView 页面白屏（H5 因鉴权失败显示空白）。

## 复现环境
- **设备**: 各种 Android 设备
- **APP 版本**: v25.0.0
- **前置条件**: APP 处于完全退出状态（冷启动）

## 复现步骤
1. 完全退出 APP（从最近任务列表滑掉）
2. 收到推送通知
3. 点击推送通知
4. 观察：APP 启动 → 页面白屏

## 日志信息
```
[09:00:00.000] [Push] Notification clicked, deepLink=myapp://hybrid/promo?id=123
[09:00:00.001] [App] Application.onCreate() — cold start
[09:00:00.100] [Router] Parsing deepLink: myapp://hybrid/promo?id=123
[09:00:00.101] [Router] Route matched: HybridActivity, params={page=promo, id=123}
[09:00:00.150] [Lifecycle] HybridActivity.onCreate()
[09:00:00.200] [WebView] Loading URL: https://h5.example.com/promo?id=123
[09:00:00.500] [WebView] Page loaded, executing JS bridge call: NativeBridge.getAuthInfo()
[09:00:00.501] [Bridge] getAuthInfo called, checking AuthManager...
[09:00:00.502] [Auth] AuthManager.getToken() = null  ← 用户 Token 尚未初始化！
[09:00:00.503] [Bridge] Returning empty auth to WebView
[09:00:00.504] [WebView] JS: Auth info empty, API call failed with 401
[09:00:00.505] [WebView] JS: Showing blank page (no error UI configured)
...
[09:00:01.200] [Auth] AuthManager initialization completed, token loaded from Keystore  ← 太晚了
```

## 相关代码（关键模块交互链）

### Application.onCreate()
```java
public void onCreate() {
    super.onCreate();
    initRouter();           // 同步，立即完成
    initPushHandler();      // 同步，注册 Intent 处理
    initAuthManager();      // 异步！Token 从 Keystore 加载需 ~1s
    initNativeBridge();     // 同步，但依赖 AuthManager
}
```

### AuthManager.java
```java
public class AuthManager {
    private volatile String token = null;
    private volatile boolean initialized = false;
    
    public void init() {
        Executors.newSingleThreadExecutor().execute(() -> {
            token = loadTokenFromKeystore();  // ~800ms-1200ms
            initialized = true;
        });
    }
    
    public String getToken() {
        return token;  // 可能返回 null（初始化未完成）
    }
}
```

## 问题链路图
```
Push Click → Router → HybridActivity.onCreate → WebView.loadUrl → JS Bridge.getAuthInfo
    ↑ 冷启动                                                           ↓
Application.onCreate → AuthManager.init (async, ~1s) ← 还没完成       → token=null → 白屏
```
