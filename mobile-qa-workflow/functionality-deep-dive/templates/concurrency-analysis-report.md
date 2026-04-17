# Concurrency Analysis Report — {Issue-ID}

## Thread Model
| Thread / Queue | Role | Related Code | Interaction |
|----------------|------|--------------|-------------|
| Main | UI | [Class.method] | [交互点] |

## Shared Resources
| Resource | Read/Write | Protection | Risk |
|----------|------------|------------|------|
| [Resource] | [Main/IO] | [Lock/None] | [High/Medium/Low] |

## Timeline
| Time | Event Type | Description | Thread | Race Marker |
|------|------------|-------------|--------|-------------|
| T+0ms | Touch | [描述] | Main | |

## Race Windows
- RW1: [描述] | Probability: [High/Medium/Low]

## Reproduction Guidance
- **High Probability Path**: [描述]
- **Forced Timing Suggestion**: [注入点 / 手段]

## Cache Consistency
- [一致 / 不一致 / 漂移类型]
