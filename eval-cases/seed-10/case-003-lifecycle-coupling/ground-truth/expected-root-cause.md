# Expected Root Cause

## Primary Root Cause
**Activity 重建时 Fragment 恢复逻辑缺陷 + ViewModel LiveData 引用复用 Bug**

问题由两个缺陷叠加导致：
1. **Fragment 恢复逻辑错误**：`FormActivity.onCreate()` 在配置变更重建时，通过 `findFragmentByTag` 查找当前步骤的 Fragment，但由于使用 `replace` 而非 `add` 添加 Fragment，之前步骤的 Fragment 不在 back stack 中，`findFragmentByTag` 返回 null，触发回退到第 1 步。
2. **LiveData 引用复用导致数据不触发更新**：`saveStepData()` 修改的是同一个 HashMap 引用，`setValue()` 时 LiveData 可能认为值未变化（引用相同），导致观察者不收到更新通知。

## Confidence Level
**High (0.95)** — 100% 复现，日志完整，代码路径清晰。
