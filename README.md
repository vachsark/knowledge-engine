# knowledge-engine

Continuous knowledge accumulation with structured evaluation loops.

---

## The Problem

Most AI research tools are one-shot: ask a question, get an answer, done. There's no feedback loop, no quality gating, no memory of what was already learned, and no mechanism for the system to get better over time.

**knowledge-engine** is different. It treats knowledge as a living asset that:

- Must pass a structured quality gate before it's persisted
- Accumulates evidence over time and can revise itself
- Knows what it already knows (pre-flight dedup before researching)
- Schedules its own learning autonomously
- Can distill validated knowledge into fine-tuning data

---

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              knowledge-engine                │
                    └─────────────────────────────────────────────┘

 ┌──────────┐    ┌──────────────────────────────────────────────────────┐
 │ Schedule │───▶│                  Research Pipeline                    │
 └──────────┘    │                                                      │
                 │  Pre-flight ──▶ Wave 1 ──▶ Wave 1.5 ──▶ Wave 2      │
                 │  (dedup)       (research)  (critique)   (synthesis)  │
                 └───────────────────────┬──────────────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │      Quality Gate         │
                          │  (backpressure + rubric)  │
                          └────────────┬─────────────┘
                                       │ pass / bounce
                                  ┌────┴─────┐
                              pass│          │bounce (refine → retry)
                                  ▼          │
                     ┌────────────────┐      │
                     │   Curator      │◀─────┘
                     │ (what to keep) │
                     └───────┬────────┘
                             │
                             ▼
              ┌──────────────────────────────────┐
              │         Knowledge Store           │
              │  versioned files + mutation log   │
              │  lessons + rules + evidence       │
              └──────────────┬───────────────────┘
                             │
              ┌──────────────┴───────────────┐
              │                              │
              ▼                              ▼
     ┌────────────────┐           ┌──────────────────┐
     │  Hybrid Search │           │  Distill Export  │
     │ (BM25 + embed) │           │  (training data) │
     └────────────────┘           └──────────────────┘
```

---

## Features

- **Hybrid semantic search**: BM25 + embeddings fused with Reciprocal Rank Fusion (RRF), plus LLM reranking
- **Multi-wave research**: Parallel research agents → adversarial critic → synthesis, adapted from the vault system's research pipeline
- **Backpressure quality gate**: Rejects runs where knowledge delta is below threshold — prevents noise accumulation (from autocontext)
- **Lesson tracking**: Applicability windowing — lessons age out when they stop being relevant
- **Evidence-based rules**: Self-improving rules with hit counters and decay. CRITICAL rules never decay.
- **Heartbeat scheduler**: Configurable task schedule with state/config separation. Avoids OnUnitActiveSec drift.
- **Model routing**: Frontier (Anthropic) for synthesis, local (Ollama) for retrieval/reranking
- **Training export**: Validated knowledge → structured training data for fine-tuning

---

## Benchmarks

Evaluated on [DRB (Deep Research Bench)](https://github.com/deepresearchbench/drb). Run your own benchmark:

```bash
ke benchmark --suite drb --output results/
```

---

## Inspirations

- **Vache's vault system** — heartbeat scheduler, semantic search, adversarial research pipeline, self-improving rules. Read more at [vachsark.com/blog](https://vachsark.com/blog).
- **[autocontext](https://github.com/greyhaven-ai/autocontext)** by greyhaven-ai — structured evaluation loops, backpressure gate, lesson applicability windowing, versioned persistence.
- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy — multi-wave research design and synthesis patterns.

---

## Quick Start

Requires [uv](https://docs.astral.sh/uv/).

```bash
# Clone and install
git clone https://github.com/vachsark/knowledge-engine
cd knowledge-engine
uv sync

# Run a research session
ke research "transformer attention mechanisms"

# Search existing knowledge
ke search "attention mechanisms scalability"

# Check status
ke status
```

### With a local model (no API key needed)

```bash
# Pull an Ollama model first
ollama pull qwen3:8b
ollama pull qwen3-embedding:0.6b

# Configure
export KE_DEFAULT_MODEL=local
export KE_LOCAL_MODEL=qwen3:8b

ke research "topic"
```

### With Anthropic (higher quality)

```bash
export ANTHROPIC_API_KEY=sk-...
export KE_DEFAULT_MODEL=sonnet

ke research "topic" --waves 2 --skeptic
```

---

## Pipeline Flow

```
ke research "topic"
    │
    ├── 1. Pre-flight: search existing knowledge for overlap
    │       └── Skip or narrow topic if >0.85 similarity
    │
    ├── 2. Wave 1: parallel research agents (N agents, M topics)
    │
    ├── 3. Wave 1.5: skeptic challenges claims in Wave 1 output
    │
    ├── 4. Wave 2: synthesis + dedup of all agent outputs
    │
    ├── 5. Quality gate: score against rubric
    │       ├── Pass (score ≥ threshold) → curator
    │       └── Bounce → refine prompt → retry (max 3)
    │
    ├── 6. Curator: decide what to persist, what to update
    │
    └── 7. Persist: versioned note + mutation log entry
```

---

## Configuration

Create `ke.yaml` in your project root:

```yaml
knowledge_dir: ./knowledge
default_model: sonnet
local_model: qwen3:8b
embed_model: qwen3-embedding:0.6b

backpressure_min_delta: 0.005
max_lessons: 50
staleness_window: 10
token_budget_daily: 500000
```

Or use environment variables (all prefixed `KE_`):

```bash
KE_KNOWLEDGE_DIR=./knowledge
KE_DEFAULT_MODEL=sonnet
KE_ANTHROPIC_API_KEY=sk-...
```

---

## Project Layout

```
src/knowledge_engine/
├── config/         # Pydantic settings
├── search/         # Hybrid BM25 + embeddings + RRF
├── research/       # Multi-wave pipeline
├── evaluation/     # Backpressure gate + curator
├── knowledge/      # Versioned store + lessons + rules
├── scheduler/      # Heartbeat + budgeting
├── models/         # Model router (frontier / local)
└── distill/        # Training data export
```

---

## License

MIT — see [LICENSE](LICENSE).
