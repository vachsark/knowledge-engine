# knowledge-engine — Claude Code Conventions

## Quick orientation

- **Entry point**: `src/knowledge_engine/cli.py` — all `ke` commands defined here
- **Pipeline flow**: `research/pipeline.py` orchestrates everything; read it first
- **Key abstractions**: `evaluation/gate.py` (backpressure), `knowledge/store.py` (persistence), `scheduler/heartbeat.py` (scheduling)
- **Settings**: `config/settings.py` — all config lives here, env prefix `KE_`

## Development setup

```bash
uv sync --all-extras
uv run pytest
uv run ruff check src/
uv run mypy src/
```

## Module ownership

| Module        | Inspiration                       | Responsibility             |
| ------------- | --------------------------------- | -------------------------- |
| `search/`     | vault-search hybrid retrieval     | BM25 + embed + RRF         |
| `research/`   | vault research pipeline (waves)   | Multi-wave orchestration   |
| `evaluation/` | autocontext curator + gate        | Quality gating, curation   |
| `knowledge/`  | autocontext versioned persistence | Store, lessons, rules      |
| `scheduler/`  | vault heartbeat system            | Scheduled task execution   |
| `models/`     | vault model routing table         | Frontier vs local dispatch |
| `distill/`    | original                          | Training data export       |

## Patterns to follow

**Settings access**: Always inject `Settings` via parameter — never import from module level in tests.

**Model calls**: Always route through `models/router.py`, never call Ollama/Anthropic directly from business logic.

**Knowledge writes**: Always go through `knowledge/store.py` — never write files directly. The mutation log must stay consistent.

**Gate bypass**: Never skip the quality gate in production paths. The `force=True` parameter exists only for tests.

**Ollama num_ctx**: Always pass `num_ctx` to Ollama API calls. Without it, the Vulkan runner hangs when prompts exceed the default 4096 tokens.

## Adding a new research wave

1. Create the wave function in `research/pipeline.py`
2. Add its agent prompt to `agents/`
3. Wire it into `ResearchPipeline.run()` with a named stage
4. Add a test stub in `tests/test_research.py`

## Adding a new evaluation dimension

1. Add the dimension to `templates/evaluation-rubric.yaml`
2. Update `evaluation/rubric.py` to parse it
3. Update `evaluation/gate.py` scoring logic if weights change

## Pre-commit checklist

- [ ] `uv run ruff check src/` passes
- [ ] `uv run mypy src/` passes
- [ ] `uv run pytest` passes
- [ ] Any new public function has a docstring and type hints
- [ ] No hardcoded model names — use `settings.default_model`
- [ ] No direct file writes outside `knowledge/store.py`

## What's a scaffold

Most `raise NotImplementedError` in the current source are intentional scaffolding.
The interfaces are designed — implementations come later.
Don't remove the `NotImplementedError` stubs; replace them with real code when implementing.
