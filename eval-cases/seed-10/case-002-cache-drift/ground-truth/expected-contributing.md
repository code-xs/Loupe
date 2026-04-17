# Expected Contributing Factors

## Contributing Factor 1: 缓存 Key 未绑定用户 ID
缓存 key 使用固定字符串 `"user_profile_current"` 而非 `"user_profile_{user_id}"`，导致不同用户的缓存数据相互覆盖而非隔离。

## Contributing Factor 2: 登出流程未等待缓存清理完成
`clearOnLogout()` 不返回 completion handler，登出流程无法确认缓存完全清理后再允许新用户登录。

## Contributing Factor 3: Profile 请求未携带用户身份校验
`getProfile()` 方法不接受 user_id 参数，无法在返回缓存数据时校验数据所属用户是否为当前登录用户。

## Contributing Factor 4: 无缓存版本标记机制
缓存数据没有附带 session_id 或 user_id 标记，无法在读取时判断数据是否属于当前会话。
