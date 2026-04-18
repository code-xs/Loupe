## 通用规则：跨层契约与资源引用溯源约束

> 本节规则不区分平台，属于全局防幻觉策略，优先级高于分平台检查项。

1. **严禁臆测机制映射**：绝不能基于上层业务代码的变量名/常量名，直接推测底层或跨层配置文件中的键名或枚举值。

2. **强制定义溯源**：任何跨越语言或框架边界的引用，必须使用检索工具查阅该标识在源文件中的精确定义（Declaration），并确保拼写与大小写严格 1:1 匹配。

3. **溯源记录留痕**：每次溯源操作的结果必须记录在 Contract-Checklist 或 Impl Report 中，供 Phase 6 验证引用。

---

# Android/iOS 平台专项检查清单

AI 在推理过程中必须参照的平台专项知识，以结构化 Checklist 形式内嵌到推理链中。

---

## Android 平台检查清单

### 生命周期
- [ ] 当前 Activity/Fragment 状态是否与操作预期一致？
- [ ] 是否在 onDestroy 后仍持有引用？
- [ ] 配置变更（屏幕旋转/语言切换）后状态是否正确恢复？
- [ ] onSaveInstanceState/onRestoreInstanceState 是否正确处理？

### 线程模型
- [ ] 异常操作是否发生在主线程？
- [ ] 是否存在跨线程访问 UI 的情况？
- [ ] Handler/Looper 状态是否正常？
- [ ] 协程/RxJava 的线程调度是否正确？
- [ ] 异步任务的取消和生命周期绑定是否正确？

### 内存
- [ ] 是否存在 Context 泄漏链？（Activity → 匿名内部类/Handler/静态引用）
- [ ] Bitmap 是否及时回收？是否使用了合适的采样率？
- [ ] 是否触发 GC 导致卡顿？
- [ ] 大对象是否使用了对象池？

### 进程
- [ ] 多进程场景下 SharedPreferences 是否存在竞争？
- [ ] ContentProvider 的跨进程访问是否线程安全？
- [ ] 进程优先级是否导致被系统杀死？
- [ ] 跨进程通信（Binder/AIDL）是否正确处理异常？

### 混淆
- [ ] 堆栈是否需要 mapping.txt 还原？
- [ ] 泛型擦除是否导致类型转换异常？
- [ ] ProGuard/R8 规则是否覆盖了反射使用的类？
- [ ] JSON 序列化/反序列化的字段是否被混淆？

### 存储
- [ ] 文件访问是否符合 Scoped Storage 规范（Android 10+）？
- [ ] 数据库操作是否在事务中执行？
- [ ] SharedPreferences 的 apply/commit 选择是否合理？

### 权限
- [ ] 运行时权限是否正确申请和处理拒绝场景？
- [ ] targetSdkVersion 升级后权限行为是否有变化？

---

## iOS 平台检查清单

### 内存管理
- [ ] ARC 下是否存在循环引用？（delegate/block/timer/NotificationCenter）
- [ ] 是否在 dealloc 后访问了 self？
- [ ] Closure 中是否正确使用 [weak self] 或 [unowned self]？
- [ ] NSTimer/CADisplayLink 是否在 dealloc 时 invalidate？

### 线程
- [ ] 是否在非主线程操作 UI？
- [ ] GCD 队列是否存在死锁？（同步调用到当前队列）
- [ ] @synchronized 范围是否合理？
- [ ] DispatchQueue 的 QoS 是否合适？
- [ ] 是否正确使用了 actor（Swift Concurrency）？

### RunLoop
- [ ] 是否因 RunLoop Mode 切换导致 Timer 行为异常？（.default vs .common）
- [ ] ScrollView 滚动时 Timer 是否暂停？
- [ ] RunLoop Observer 的注册和移除是否正确？

### 系统 API
- [ ] 是否使用了被 deprecated 的 API？
- [ ] iOS 版本间行为差异是否被处理？（@available 检查）
- [ ] 隐私相关 API 是否正确声明用途说明（Info.plist）？
- [ ] App Transport Security 配置是否正确？

### 符号化
- [ ] dSYM 是否与 build 版本匹配？
- [ ] 系统库堆栈是否需要进一步符号化？
- [ ] Bitcode 是否影响了符号化结果？

### 存储
- [ ] UserDefaults 存储的数据量是否过大？
- [ ] Core Data 操作是否在正确的 NSManagedObjectContext 线程？
- [ ] Keychain 的 accessibility 级别是否合理？

### 界面
- [ ] Safe Area 是否正确处理？
- [ ] Status Bar 样式是否与页面内容匹配？
- [ ] 横竖屏切换是否正确处理约束变化？
- [ ] Dynamic Type 字号变化是否正确响应？

---

## API 版本合规检查

### Android

```
检查流程:
1. 读取 build.gradle 中的 minSdkVersion 和 targetSdkVersion
2. 扫描修改代码中使用的 Android API
3. 对比每个 API 的引入版本与 minSdkVersion
4. 高于 minSdkVersion 的 API 必须:
   - 使用 @RequiresApi 注解
   - 或 Build.VERSION.SDK_INT 版本检查
   - 或使用 AndroidX Compat 替代

常见风险 API:
- Android 10 (29): Scoped Storage, Background Activity 限制
- Android 11 (30): Package Visibility, 强制 Scoped Storage
- Android 12 (31): 精确闹钟权限, PendingIntent mutability
- Android 13 (33): 通知权限, Photo Picker
- Android 14 (34): 前台服务类型, 精确闹钟限制
```

### iOS

```
检查流程:
1. 读取 Deployment Target（Xcode 项目设置）
2. 扫描修改代码中使用的系统 API
3. 对比每个 API 的引入版本与 Deployment Target
4. 高于 Deployment Target 的 API 必须:
   - 使用 @available / #available 版本检查
   - 或提供低版本替代实现

常见风险 API:
- iOS 14: WidgetKit, App Clips, PHPicker
- iOS 15: async/await 原生支持, AttributedString
- iOS 16: NavigationStack, SwiftUI Charts, Transferable
- iOS 17: Observation framework, TipKit, StoreKit 2 必须
- iOS 18: Control Center Widget, FinanceKit
```
