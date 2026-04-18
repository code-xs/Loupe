# Error Dump 模板

```markdown
## Error Dump — {Issue-ID}

### 元信息
- **关联 Issue**: {issue_id}
- **纠错轮次**: 3（已达上限）
- **触发时间**: {timestamp}
- **Execution-Status**: Human-Review

### 最终错误现场
- **错误类型**: [编译错误/链接错误/Lint Error/类型不匹配/...]
- **错误文件**: {file_path}
- **错误行号**: {line_number}
- **完整错误消息**:
  ```
  {error_message}
  ```

### 三轮纠错尝试记录

| 轮次 | 错误摘要 | 溯源操作 | 修正动作 | 结果 |
|------|---------|---------|---------|------|
| 1 | {error_1} | {trace_1} | {fix_1} | ❌ 未解决 / ✅ 已解决但引发新错误 |
| 2 | {error_2} | {trace_2} | {fix_2} | ❌ |
| 3 | {error_3} | {trace_3} | {fix_3} | ❌ |

### 当前代码快照
- **修改文件列表**:
  - {file_1}: +{N}/-{M} 行
  - {file_2}: +{N}/-{M} 行
- **已应用变更**: [变更描述]
- **未回滚状态**: [是否有部分修改未回滚]

### 建议人工处理方向
1. {suggestion_1}
2. {suggestion_2}
3. {suggestion_3}
```
