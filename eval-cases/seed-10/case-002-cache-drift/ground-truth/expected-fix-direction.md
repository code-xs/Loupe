# Expected Fix Direction

## Primary Fix
**将缓存 Key 绑定到用户 ID**，使不同用户的缓存数据完全隔离：
```swift
func getProfile(for userId: String) -> ProfileData? {
    let key = "user_profile_\(userId)" as NSString
    // ...
}
```

## Defensive Fixes
1. **登出时同步清理所有缓存层**：将磁盘缓存清理改为同步操作，或使用 DispatchGroup 等待完成后再返回
2. **缓存数据附带 session 标记**：每条缓存记录包含 `session_id` 字段，读取时校验
3. **Profile 显示前强制校验用户身份**：在 UI 层渲染前比对缓存数据的 user_id 与当前登录 user_id
4. **登录流程增加缓存清洁断言**：新用户登录成功后，断言旧用户缓存已清空
