# PR-8 · CI + install 整合（v2.2）实施期偏差 Review (2026-04-20)

## Scope

- 审查对象：施工单 `construction-plans/v2.2/pr8-ci-install-integration.md` (commit `a7d8ae5`)
  与实际三个实施 commit (`81d93eb` / `8f2ce87` / `1ccde10`)
- 审查基线：`mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` §3 PR-8、§5.1、§7.8、附录 C D11-D19 / M16
- 审查性质：**实施期就地修正留档**（非外部审查发现的待修问题）。
  施工单 v1 草案在 dry-run 阶段被发现 5 处描述/算法不够精确，
  已在 commit `8f2ce87` 内一次性修正并在 commit message 诚实记录；
  本文档把 5 项偏差正式归档，便于后人参考施工单 v1 时不再踩坑。
- 结论：**5 项偏差全部不阻塞 PR-8 合并**；其中 **3 项（#1 / #2 / #5）建议在 v2.2
  收口阶段回填到施工单 v1 或在本文档基础上发布 `施工单 v2`**

## Intent (Inferred)

施工单 v1 把 8 项 CI 守门当作"伪代码草案"提出，预期实施期会做工程化打磨。
实施期发现以下 3 类偏差：

1. **设计意图细化**（偏差 #1 / #2）：施工单描述过严或算法单向，实际应与 D14/D19 的 v4.2 过渡豁免对齐
2. **实现 bug 修复**（偏差 #3 / #5）：施工单草案的 awk 锚点与 pipefail 处理有真实 bug，照抄会导致守门失效或诊断信息丢失
3. **可移植性增强**（偏差 #4）：兼容 macOS 默认 bash 3.x，本地可裸跑 dry-run

## Deviation Flow

```mermaid
flowchart TD
    A[施工单 v1 §3.B/§3.C 草案] --> B{实施期 dry-run}
    B -->|偏差 #1: D16 范围未排除 allowlist| C[就地细化: 跳过 allowlist legacy]
    B -->|偏差 #2: D14 单向匹配| D[就地升级: 双向匹配 + 反向漂移检测]
    B -->|偏差 #3: D15 awk 锚点过宽| E[就地修复: 锚点收紧为 ^# ⚠️]
    B -->|偏差 #4: 用 mapfile 不兼容 bash 3.x| F[就地替换: while read 数组累加]
    B -->|偏差 #5: pipefail + grep 经典坑| G[就地修复: pipe 末尾 || true]
    C --> H[8 项 CI 全绿 + commit message 诚实记录]
    D --> H
    E --> H
    F --> H
    G --> H
    H --> I[本 REVIEW 留档]
    style C fill:#fff3e0,color:#e65100
    style D fill:#c8e6c9,color:#1a5e20
    style E fill:#fde2e4,color:#8a1c1c
    style F fill:#bbdefb,color:#0d47a1
    style G fill:#fde2e4,color:#8a1c1c
    style H fill:#c8e6c9,color:#1a5e20
```

## Findings (Ordered by Risk Level)

| No. | Issue Title | Risk | Status | Suggestion |
|---:|---|---|---|---|
| 1 | **Bug Fix · D15 awk 锚点过宽** — 施工单 v1 用 `/顶层镜像字段白名单/` 触发 in_block，会被 `workflow-status-template.yaml` line 58 的注释 mention 提前触发，误抽 4 个字段 (`user_inputs / non_bug_context / parse_error_count / non_bug_user_choice`) 作为白名单。当前现状下 6 个 result_field 与误抽 3 个名字未撞名，所以"恰好"无误报；但一旦后续新增 result_field 命名上撞到 `parse_error_count` 等常用名，D15 守门会**静默失效** | 🟡 中（命名撞名风险） | ✅ 已就地修正：锚点收紧为 `^#[[:space:]]*⚠️[[:space:]]*顶层镜像字段白名单` | 强烈建议回填施工单 v1 §3.B 第 3 项 awk skeleton |
| 2 | **Bug Fix · pipefail + grep 无匹配的经典坑** — 施工单 v1 §3.C `check-config-schema.sh` 草案 `keys=$(echo \| sed \| grep -oE \| sed \| sort)` 在第一次遇到无 `=` 写入语法的行（如 `更新 ... config_source：增加 X、Y、Z 路径`）时，grep 退 1 → pipefail 让命令替换失败 → set -e 让脚本退 1 但**不打任何 `[M16-FAIL]`**，CI 会显示"failed step"但**没有诊断信息** | 🔴 高（隐性 bug，浪费排查时间） | ✅ 已就地修复：pipe 末尾加 `\|\| true` | 强烈建议回填施工单 v1 §3.C 草案，加注释说明 set -o pipefail + grep 无匹配的兼容写法 |
| 3 | **Algorithm Upgrade · D14 单向匹配 → 双向匹配** — 施工单 v1 §3.B 第 2 项是单向（phases 命中 → 看是否在 allowlist），漏掉了"phases 内 step-pause 已删除但 allowlist 没同步删"的反向漂移场景。D19 文件头协议明确这是 fail 行为 | 🟢 低（守门能力**强于** v1） | ✅ 已就地升级：双向匹配 + ±5 行漂移 + 反向 `[D19-DRIFT]` 检测 | 建议回填施工单 v1 §3.B 第 2 项的 grep 骨架 |
| 4 | **Scope Refinement · D16 范围细化** — 施工单 v1 §3.B 第 1 项写"所有 `<step-pause>` 三属性完整"，与 D14/D19 设计的"phase legacy 享受 v4.2 整改过渡豁免"冲突。若按字面执行，CI 在 PR-8 之前的 base 上即 fail（phases/p2:53 / phases/p4:136 这 2 处 legacy 确实缺 `result_field` / `allowed_values`） | 🟢 低（设计本就这样，v1 描述过严） | ✅ 已就地细化：剔除 allowlist 内 legacy；非 allowlist 命中仍强守门；legacy 由检查 2 兜底 | 建议回填施工单 v1 §3.B 第 1 项描述 |
| 5 | **Portability · bash 3.x 兼容** — 施工单 v1 用 `mapfile -t LEGACY < <(...)` (bash 4+)，CI ubuntu-latest 自带 bash 5.x 能跑，但 macOS 默认 `/bin/bash` 是 3.2.57 → 本地无法 dry-run | 🟢 无（CI 与本地行为一致；本地可跑是收益） | ✅ 已就地替换：`while IFS= read -r line; do LEGACY+=("$line"); done < <(...)` | 可不回填；或在 §3.A 元信息加一句"实现需兼容 bash 3.x" |

## Evidence Links

- 施工单 v1 落盘：[`pr8-ci-install-integration.md`](./pr8-ci-install-integration.md)（commit `a7d8ae5`）
- 实施 commit：
  - `81d93eb` install.sh `--target=` 合并 + install_trae.sh shim
  - `8f2ce87` CI workflow + check-config-schema (含全部 5 项偏差修正)
  - `1ccde10` 主文档 §4 索引行联动
- D14 协议定义：[`core-rules.xml:L108-L123`](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L108-L123)
- D15 顶层白名单段（被偏差 #1 误抽的 mention）：[`workflow-status-template.yaml:L58`](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L58)
  与真实白名单段 [`workflow-status-template.yaml:L80-L85`](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L80-L85)
- D19 allowlist 文件头协议：[`legacy-phase-step-pause-allowlist.txt`](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt)
- 8 项 CI 实现：[`qa-workflow-schema-check.yml`](file:///Users/bytedance/Code/loupe/.github/workflows/qa-workflow-schema-check.yml)
- M16 独立脚本：[`check-config-schema.sh`](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/scripts/check-config-schema.sh)

## Verification

### 本地 dry-run（commit `8f2ce87` 落盘后即跑）

```
[D16-OK] checked=6 skipped_legacy=2
[D14-OK] all 2 phase-internal hits matched; allowlist 0 drift
[D15-OK] result_fields=6, whitelist=1 (non_bug_user_choice), no leakage
[Migration-Note-OK]  [D13-OK]  [D19-OK] non-comment=2
[M16-OK] all 12 config_source write keys registered
[D18-OK] 4 lifecycle actions present
```

### 反向破坏性测试

phases/p1-intake.md 临时注入 1 个非 allowlist 的 `<step-pause>` →
Check 2 立即输出 `[D14-FAIL] mobile-qa-workflow/phases/p1-intake.md:112 not in allowlist` 退 1
（fail-fast 工作正常），还原后复绿。

### install 等价性自检

| 入口 | 结果 |
|---|---|
| `bash install.sh --help` | ✓ 新 Usage |
| `bash install_trae.sh --help` (shim 转发) | ✓ 输出与 install.sh 一致 |
| `bash install.sh --target=foo` | ✓ Unknown --target value fail-fast |
| `bash install.sh --bogus` | ✓ Unknown argument + 打印 help |
| `bash -n` 两脚本 | ✓ 语法 OK |

## 审查结论

- 施工单 v1 的整体 8 项守门设计**正确且完整**，5 项偏差均为"工程化打磨阶段必然出现"的细节问题
- 实施 commit `8f2ce87` 已就地修正全部 5 项偏差，CI 8 项本地全绿 + 反向破坏性测试通过
- **不阻塞 PR-8 合并 / push**
- 建议状态：`Approved with Notes` — push 前后均可，3 项（#1 / #2 / #5）的施工单回填可作为 v2.2 收口阶段的 follow-up
- v4.2 收敛时（主文档 §1.2.2 v4.2 遗留 #3 / #6）一并处理：
  - 遗留 #3：删除顶层镜像字段后，本 REVIEW 偏差 #1 的 awk 锚点可同步移除
  - 遗留 #6：phases legacy step-pause 整改后，本 REVIEW 偏差 #4 的 D16 跳过逻辑可同步移除
