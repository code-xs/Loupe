# EventBus 事件乱序导致购物车数量显示与实际不一致

## 问题概述
用户在商品详情页快速连续点击"加入购物车"按钮后，购物车图标上的数量 badge 显示的数字与购物车内实际商品数量不一致。例如：实际加入了 3 件商品，但 badge 显示为 1 或 2。

## 复现环境
- **设备**: Android / iOS
- **APP 版本**: v19.0.0
- **复现条件**: 快速连续点击（>3次/秒）

## 复现步骤
1. 进入任意商品详情页
2. 快速连续点击"加入购物车"按钮 5 次
3. 观察购物车 badge：显示的数字不是 5（可能是 2、3 或 4）
4. 进入购物车页面：实际有 5 件商品

## 日志信息
```
[12:00:00.000] [Cart] Add item clicked (1st)
[12:00:00.050] [Cart] Add item clicked (2nd)
[12:00:00.100] [Cart] Add item clicked (3rd)
[12:00:00.150] [Cart] Add item clicked (4th)
[12:00:00.200] [Cart] Add item clicked (5th)
[12:00:00.300] [Network] POST /cart/add — item_id=123, response: {cart_count: 1}
[12:00:00.350] [EventBus] CartUpdatedEvent(count=1) posted
[12:00:00.400] [Network] POST /cart/add — item_id=123, response: {cart_count: 2}
[12:00:00.420] [Network] POST /cart/add — item_id=123, response: {cart_count: 4}  ← 跳过了3！
[12:00:00.421] [EventBus] CartUpdatedEvent(count=4) posted
[12:00:00.422] [EventBus] CartUpdatedEvent(count=2) posted  ← 乱序！count=2 晚于 count=4
[12:00:00.450] [Network] POST /cart/add — item_id=123, response: {cart_count: 3}
[12:00:00.451] [EventBus] CartUpdatedEvent(count=3) posted  ← 乱序！
[12:00:00.500] [Network] POST /cart/add — item_id=123, response: {cart_count: 5}
[12:00:00.501] [EventBus] CartUpdatedEvent(count=5) posted
[12:00:00.502] [Badge] Latest received count=5, but badge shows 3  ← 因为 count=3 是最后处理的
```

## 相关代码

### CartManager.kt
```kotlin
class CartManager {
    fun addToCart(itemId: String) {
        // 每次点击都发起独立的网络请求
        GlobalScope.launch(Dispatchers.IO) {
            val response = cartApi.addItem(itemId)
            // 网络响应顺序不确定 → 事件发送顺序不确定
            EventBus.getDefault().post(CartUpdatedEvent(response.cartCount))
        }
    }
}
```

### CartBadgeView.kt
```kotlin
class CartBadgeView : View {
    @Subscribe(threadMode = ThreadMode.MAIN)
    fun onCartUpdated(event: CartUpdatedEvent) {
        // 直接使用事件中的 count，无乱序保护
        setBadgeCount(event.count)
    }
}
```
