"""
Multi-wave research pipeline.

Wave structure (adapted from vault research pipeline):
    Pre-flight  — dedup check against existing knowledge
    Wave 1      — parallel research agents
    Wave 1.5    — adversarial skeptic challenges Wave 1 output
    Wave 2      — synthesis + dedup of all agent outputs

After waves: Quality Gate → Curator → Knowledge Store.
"""
