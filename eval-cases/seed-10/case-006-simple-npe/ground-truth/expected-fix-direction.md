# Expected Fix Direction

## Primary Fix
1. 将 `products` 字段初始化为空列表：`private List<Product> products = new ArrayList<>()`
2. 在 `setProducts()` 中增加 null 检查：`this.products = products != null ? products : new ArrayList<>()`
3. 移除 `onRefreshComplete` 中不必要的 `setProducts(null)` 调用
