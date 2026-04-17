# Expected Contributing Factors

## Contributing Factor 1: products 字段未初始化
`ProductListAdapter` 中的 `products` 字段声明时未初始化为空列表（`new ArrayList<>()`），默认值为 null。

## Contributing Factor 2: setProducts 方法未做 null 检查
`setProducts()` 不校验参数是否为 null，直接赋值后触发 `notifyDataSetChanged()`。
