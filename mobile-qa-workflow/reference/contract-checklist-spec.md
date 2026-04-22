# Contract Checklist Spec · 契约溯源检查清单规范

> v4.2 PR-7 / O11+ / §2.1 E1：本文件由 [`agents/coder-agent.md`](../agents/coder-agent.md)
> 入口在「工具权限」段后、「返回判定协议」段前以**固定顺序**第 2 条 `<load>` 引入，
> 紧跟 [`agents/coder-workflow.md`](../agents/coder-workflow.md) 加载；与 workflow
> 拆分后共同构成原 v4.1 单文件 `coder-agent.md` 的全集。
>
> **加载契约**：
>
> - **唯一入口**：`agents/coder-agent.md`（P5 invoke-subagent 与 Limited 降级路径
>   均仅 `<load coder-agent.md>`，**禁止**单独 `<load contract-checklist-spec.md>`）
> - **顺序契约**：本文件**后于** `coder-workflow.md` 加载（与入口固定顺序一致）；
>   workflow 阶段 1 引用本文件的 schema 与反空泛规范，先后顺序不可对调
> - **职责切分**：本文件 = 契约溯源 schema + 反空泛标准 + 平台映射表（数据/规范）；
>   workflow.md = 四阶段执行步骤 + Error Dump 模板（动作）
> - **P6 例外**（§2.1）：当 P6 仅需要 Checklist 而不需要 coder-agent 全集时，**唯一允许**
>   单独 `<load contract-checklist-spec.md>`；当前 v4.2 PR-7 内主链 phases/p6-verification.md
>   不触发该例外，本通路保留为 v4.3 接口

# Contract Checklist 反空泛规范

**最小必填字段（5 项）**：溯源项、源文件、期望值、实际值、匹配状态

**校验规则**：
1. 涉及 N 个跨模块 API 调用/资源引用 → checklist 条目数 ≥ N
2. 源文件字段必须是可验证的 `文件路径:行号` 格式，禁止 "某个文件" 等模糊描述
3. 期望值和实际值必须是具体的字符串、函数签名、枚举值，禁止 "正确的值" 等抽象描述

**空泛检测标准**（满足任一即判定为空泛）：
- 溯源项 不含具体 API/资源/配置键名称
- 源文件 不含文件路径或行号
- 期望值 或 实际值 使用了 "应该"、"正确"、"合理" 等非具体词汇
- 匹配状态 为 ❌ 但未提供修正动作

# 平台溯源映射表

| 平台 | 资源/配置典型溯源路径 | 常见幻觉陷阱 |
|------|---------------------|-------------|
| Android | `res/values/attrs.xml` → 自定义属性声明; `AndroidManifest.xml` → 权限/组件注册; `build.gradle` → 依赖版本/SDK 版本 | 从变量名推测 XML 属性名（实际可能不同）; 混淆后的类名/方法名 |
| iOS | `Info.plist` → 权限声明/URL Scheme; `*.xcconfig` → 构建配置; `Podfile/Package.swift` → 依赖版本 | 从 Swift 属性名推测 ObjC 选择器（实际可能不同）; Framework 版本差异 |
| Flutter | `pubspec.yaml` → 依赖版本; `AndroidManifest.xml` + `Info.plist` → 双平台配置 | 混淆 Dart 层和 Native 层的 API 名 |
| React Native | `package.json` → 依赖版本; Native Module 桥接层 → 方法签名 | JavaScript 侧方法名与 Native 侧映射不一致 |
