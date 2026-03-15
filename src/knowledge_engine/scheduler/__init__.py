"""
Heartbeat scheduler — autonomous task scheduling with state/config separation.

Adapted from vault heartbeat architecture (schedule.md + state.md separation,
OnCalendar wall-clock timer, comma-separated day support).

Key design decisions (from vault heartbeat memory):
    - Config and state are SEPARATE files (schedule.yaml vs state.yaml)
    - Use wall-clock OnCalendar scheduling, not OnUnitActiveSec (avoids drift)
    - Comma-separated days: 'weekly monday,wednesday,friday HH:MM'
    - Tool-dependent tasks skip local model fallback
    - Always pass num_ctx to Ollama calls
"""
