# Context Curation Report

## 1. Candidate Contexts (`candidate_contexts`)
*List the original set of code candidates collected before curation.*
- [File/Method 1]: (Brief description of why it was initially collected)
- [File/Method 2]: ...

## 2. Pruned Contexts (`pruned_contexts`)
*List contexts that have been definitively ruled out and will NOT enter RCA.*
- [File/Method 1]:
  - `prune_reasons`: (e.g., `dead-code`, `flag-off`, `no-runtime-link`)
  - *Note: Retained here for auditing and potential curation backtracking.*

## 3. Retained Contexts & Reasons (`keep_reasons`)
*List contexts that are confirmed as live, relevant, and mapped to runtime evidence.*
- [File/Method 1]:
  - `keep_reasons`: (e.g., explicitly hit in crash stack, flag confirmed ON)
  - `runtime_links`: (Mapping to stack traces, logs, or network traces)

## 4. Unresolved Noise (`unresolved_noise`)
*List contexts that cannot be definitively confirmed nor ruled out. These are retained but downgraded to `Suspect` status.*
- [File/Method 1]:
  - Reason for uncertainty: (e.g., Config snapshot unavailable, implicit reflective call)
  - `Liveness Status`: `Suspect`

## 5. Curation Summary
* **Context Noise Risk**: [High / Medium / Low] (Assessment of the overall pollution level before curation)
* **Curation Confidence**: [0.0 - 1.0] 
  *(>=0.7: Ready for RCA; 0.4-0.7: Partial, requires extra Challenger scrutiny [Curation-Partial]; <0.4: Curation failed, requires fallback/human-review)*
