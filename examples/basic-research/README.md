# Basic Research Session

Run your first knowledge-engine research session in under 5 minutes.

## Prerequisites

1. **Install uv** — https://docs.astral.sh/uv/
2. **Install Ollama** — https://ollama.com/
3. **Pull models**:

```bash
ollama pull qwen3:8b
ollama pull qwen3-embedding:0.6b
```

## Setup

```bash
# Clone and install
git clone https://github.com/vachsark/knowledge-engine
cd knowledge-engine
uv sync

# Copy the example config
cp examples/basic-research/config.yaml ke.yaml
```

## Run a Research Session

```bash
# Research a topic — output is saved to ./knowledge/notes/
ke research "transformer attention mechanisms"

# The pipeline will:
# 1. Check your knowledge/ dir for existing coverage (pre-flight)
# 2. Run Wave 1: parallel research agents
# 3. Run Wave 1.5: skeptic challenges the output
# 4. Synthesize the wave outputs
# 5. Score against the quality rubric
# 6. If score >= 0.65: curate and persist to knowledge/notes/
```

## View Results

```bash
# Check what was saved
ke status

# Search the knowledge base
ke search "attention mechanisms"

# View the raw note
ls knowledge/notes/
cat knowledge/notes/<note-file>.md
```

## What You'll See

```
Researching: transformer attention mechanisms
Running pipeline...
  [1/5] Pre-flight: checking existing knowledge...  no overlap found
  [2/5] Wave 1: running 2 research agents...        done
  [3/5] Wave 1.5: skeptic review...                 3 challenges
  [4/5] Synthesis...                                 done
  [5/5] Quality gate: score=0.74 delta=0.91...      PASS

Gate result: pass
Saved: knowledge/notes/transformer-attention-mechanisms-kv-cache.md
```

## Adjusting Quality

If the gate is too strict (bouncing everything):

- Lower `gate_pass_threshold` in ke.yaml (try 0.60)
- Lower `backpressure_min_delta` to 0.001

If output quality is too low:

- Raise `gate_pass_threshold` to 0.75
- Set `default_model: sonnet` (requires `KE_ANTHROPIC_API_KEY`)

## Next Steps

- Try the [continuous-learning example](../continuous-learning/) for scheduled sessions
- Export your knowledge for fine-tuning: `ke export --format jsonl`
