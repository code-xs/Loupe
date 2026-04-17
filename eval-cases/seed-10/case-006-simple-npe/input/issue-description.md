# 列表页下拉刷新时 NullPointerException 崩溃

## 问题概述
用户在商品列表页执行下拉刷新操作时，APP 必现崩溃。Crash 报告显示为 NullPointerException。

## 复现环境
- **设备**: 所有 Android 设备
- **APP 版本**: v18.3.0 (Build 1830012)

## 复现步骤
1. 打开 APP，进入商品列表页
2. 执行下拉刷新手势
3. APP 立即崩溃

## 崩溃堆栈
```
java.lang.NullPointerException: Attempt to invoke virtual method 'int java.util.List.size()' on a null object reference
    at com.app.feature.product.ProductListAdapter.getItemCount(ProductListAdapter.java:45)
    at androidx.recyclerview.widget.RecyclerView$Adapter.notifyDataSetChanged(RecyclerView.java:7200)
    at com.app.feature.product.ProductListFragment.onRefreshComplete(ProductListFragment.java:89)
    at com.app.feature.product.ProductListViewModel$refresh$1.invokeSuspend(ProductListViewModel.kt:56)
```

## 相关代码

### ProductListAdapter.java
```java
public class ProductListAdapter extends RecyclerView.Adapter<ProductViewHolder> {
    private List<Product> products;  // 未初始化，默认 null
    
    public void setProducts(List<Product> products) {
        this.products = products;
        notifyDataSetChanged();
    }
    
    @Override
    public int getItemCount() {
        return products.size();  // NPE: products 可能为 null
    }
}
```

### ProductListFragment.java
```java
public void onRefreshComplete(List<Product> newProducts) {
    adapter.setProducts(null);  // BUG: 清空时传了 null
    adapter.setProducts(newProducts);
}
```
