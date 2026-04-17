# Expected Contributing Factors

## Contributing Factor 1: Fragment 事务使用 replace 而非 add+hide
`showStep()` 使用 `replace` 替换 Fragment，导致前序步骤的 Fragment 被销毁，无法在 Activity 重建后通过 FragmentManager 自动恢复。

## Contributing Factor 2: 未使用 SavedStateHandle
ViewModel 中的表单数据仅存在于内存中的 LiveData，没有使用 `SavedStateHandle` 持久化到 Bundle，虽然 ViewModel 在配置变更中存活，但如果进程被杀则数据丢失。

## Contributing Factor 3: Fragment 未实现 onSaveInstanceState
StepFragment 没有在 `onSaveInstanceState` 中保存当前步骤的表单输入状态。
