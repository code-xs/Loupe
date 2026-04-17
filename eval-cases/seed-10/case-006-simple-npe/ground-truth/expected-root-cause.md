# Expected Root Cause

## Primary Root Cause
`ProductListFragment.onRefreshComplete()` 在刷新时先调用 `adapter.setProducts(null)` 清空列表，这会将 adapter 内部的 `products` 字段设为 null。紧接着调用 `notifyDataSetChanged()`（在 `setProducts` 内部），此时 `getItemCount()` 访问 `products.size()` 触发 NPE。

## Confidence Level
**Very High (0.98)** — 必现，堆栈完整，代码路径明确。
