# Expected Fix Direction

## Primary Fix
**使用本地购物车状态作为单一真相源 + 乐观更新**：
```kotlin
class CartManager {
    private val _cartCount = MutableStateFlow(0)
    
    fun addToCart(itemId: String) {
        _cartCount.value++  // 乐观更新
        viewModelScope.launch(Dispatchers.IO) {
            try {
                val response = cartApi.addItem(itemId)
                _cartCount.value = response.cartCount  // 服务端确认更新
            } catch (e: Exception) {
                _cartCount.value--  // 失败回滚
            }
        }
    }
}
```

## Defensive Fixes
1. 如果仍使用 EventBus，添加事件版本号（单调递增），badge 只接受版本号 > 当前版本的事件
2. 添加按钮点击节流（最小间隔 300ms）
3. 合并短时间内的多次加购请求为单次批量请求
4. 将 GlobalScope 替换为 viewModelScope
