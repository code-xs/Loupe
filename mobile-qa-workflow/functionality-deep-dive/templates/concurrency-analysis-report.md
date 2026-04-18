# Concurrency Analysis Report — {Issue-ID}

> 可按需独立落盘；默认优先沉入 `functionality-deep-dive-rca.md` 附录。

## Timeline
| Time | Event Type | Description | Thread | Race Marker |
|------|------------|-------------|--------|-------------|
| T+0ms | Touch | [描述] | Main | |

## Race Windows
- RW1: [描述] | Probability: [High/Medium/Low]

## Shared Resources
| Resource | Read/Write | Protection | Risk |
|----------|------------|------------|------|
| [Resource] | [Main/IO] | [Lock/None] | [High/Medium/Low] |

## Reproduction Guidance
- **High Probability Path**: [描述]
- **Forced Timing Suggestion**: [注入点 / 手段]
