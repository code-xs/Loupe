# 用户资料页缓存脏读导致显示他人信息

## 问题概述
用户 A 登出后，用户 B 登录同一设备。用户 B 进入"我的"页面后，短暂看到用户 A 的头像和昵称（约 0.5-1 秒），随后刷新为用户 B 的正确信息。此问题涉及用户隐私，属于 P0 级别安全隐患。

## 复现环境
- **设备**: iPhone 14 Pro (iOS 17.4)
- **APP 版本**: v15.2.0 (Build 1520034)
- **网络**: WiFi

## 复现步骤
1. 用户 A 登录 APP，进入"我的"页面，确保资料已加载
2. 用户 A 执行登出操作
3. 在登录页面，用户 B 输入凭证登录
4. 登录成功后立即点击底部 Tab "我的"
5. 观察：短暂显示用户 A 的头像和昵称

## 复现率
约 5%（操作速度需较快，在登录完成后 1 秒内点击"我的" Tab）

## 日志信息

### 系统日志（登出-登录流程）
```
[15:20:01.100] [Auth] User A logout initiated
[15:20:01.150] [Cache] Clearing auth token cache
[15:20:01.200] [Auth] User A logout completed
[15:20:01.201] [Cache] Profile cache clear scheduled (async)  ← 异步清理
[15:20:05.300] [Auth] User B login initiated
[15:20:05.800] [Auth] User B login completed, token refreshed
[15:20:05.801] [Profile] Loading profile for current user
[15:20:05.802] [Cache] Cache HIT for profile key "user_profile_current"  ← 命中了用户 A 的缓存！
[15:20:05.803] [Profile] Displaying cached profile (stale)
[15:20:06.100] [Network] Profile API response received for User B
[15:20:06.101] [Cache] Profile cache updated for User B
[15:20:06.102] [Profile] Displaying fresh profile (User B)
```

### 缺失日志
- 异步缓存清理的完成回调日志缺失（可能被日志轮转截断）
- 缓存 key 生成逻辑的 debug 日志未开启

## 相关代码片段

### ProfileCacheManager.swift
```swift
class ProfileCacheManager {
    private let cache = NSCache<NSString, ProfileData>()
    private let diskCache = DiskLRUCache(directory: "profile_cache")
    
    func clearOnLogout() {
        cache.removeAllObjects()
        // 磁盘缓存异步清理
        DispatchQueue.global().async { [weak self] in
            self?.diskCache.removeAll()  // 耗时约 200-500ms
        }
    }
    
    func getProfile() -> ProfileData? {
        // 先查内存缓存
        if let cached = cache.object(forKey: "user_profile_current") {
            return cached
        }
        // 再查磁盘缓存
        if let diskData = diskCache.get("user_profile_current") {
            cache.setObject(diskData, forKey: "user_profile_current")
            return diskData
        }
        return nil
    }
}
```

## 用户反馈
- "登录后看到了别人的头像，吓了一跳"
- "这是不是有安全问题？别人能看到我的信息吗？"
