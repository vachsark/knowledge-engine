"""
Evaluation module: quality gating, curation, rubric scoring, weakness detection.

Key patterns adapted from autocontext:
    - Backpressure gate: rejects runs with insufficient knowledge delta
    - Curator: decides what specific knowledge to persist, what to update
    - Rubric: configurable RACE-like evaluation dimensions
    - Weakness detector: pattern-based flagging of common failure modes
"""
