# Expected Fix Direction

## Primary Fix
1. **修复 Activity 重建逻辑**：在 `savedInstanceState != null` 时，直接使用 `viewModel.getCurrentStep()` 创建对应步骤的 Fragment，而非依赖 `findFragmentByTag`
2. **修复 LiveData 值更新**：`saveStepData()` 中创建 HashMap 的新副本再 `setValue()`

## Defensive Fixes
1. 使用 `SavedStateHandle` 持久化表单数据
2. Fragment 实现 `onSaveInstanceState` 保存局部输入状态
3. 考虑使用 Navigation Component + SafeArgs 管理多步骤导航
