"""
Model routing and integration layer.

Routes calls to the appropriate backend based on model tier:
    'sonnet' / 'opus' / 'haiku' → Anthropic API (anthropic.py)
    'local'                      → Ollama HTTP API (ollama.py)

From vault model selection table (CLAUDE.md):
    Haiku  — read-only scans, simple edits, data gathering
    Sonnet — all coding/implementation, default
    Opus   — multi-agent coordination, long-context (50+ files), quality gates
    Local  — heartbeat tasks, retrieval, reranking (free, GPU-accelerated)

Critical from vault memory: Always pass num_ctx to Ollama — Vulkan runner hangs
without it when prompts exceed the default 4096 token context.
"""
