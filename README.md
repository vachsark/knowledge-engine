# knowledge-engine

Continuous knowledge accumulation with structured evaluation loops.

> **Status**: This is an early scaffold — interfaces are defined, implementations are coming. Star/watch if you want to follow along.

---

## How this got here

### Stage 1 — The vault (early 2026)

I have an Obsidian vault with 700+ atomic Zettelkasten notes spanning CS, economics, psychology, math, and a handful of other domains. It started as a manual knowledge base, then I added a single Claude agent that would pick topics from a queue and write notes overnight.

It worked. Notes got created consistently, the queue drained, and the vault grew. But there was no quality control. Duplicates accumulated. Cross-domain connections were whatever the agent happened to notice on a given run. Quality was inconsistent — some notes were dense and well-sourced, others were shallow summaries I could have written in five minutes. The problem wasn't throughput. It was that nothing was checking whether the knowledge was actually good.

### Stage 2 — Karpathy's autoresearch (late February 2026)

Then I saw Andrej Karpathy's autoresearch post — his system for running autonomous ML experiments overnight with Claude Code. Three patterns clicked immediately: using a `program.md` as a human-editable strategy file, an append-only `results.tsv` for tracking runs, and simplifying evaluation to a single score you can track over time. That last one sounds obvious but it changes how you build everything. When you commit to a single metric, you stop arguing about what "better" means and start actually improving.

I rebuilt my pipeline around these ideas.

### Stage 3 — autoknowledge (March 2026)

The result was [autoknowledge](https://github.com/vachsark/autoknowledge) — a multi-wave research pipeline where parallel agents research topics, a critic challenges the output, an adversarial skeptic rejects weak cross-domain connections (~60% rejection rate), and a synthesis wave integrates what survives. I added [vault-search](https://github.com/vachsark/vault-search) — hybrid BM25 + embeddings + RRF fusion — as the retrieval layer, so the pipeline could check what the vault already knew before researching anything. Pre-flight deduplication: if a topic has >85% overlap with existing knowledge, skip or narrow.

I built a heartbeat scheduler that runs 16+ automated tasks on a local AMD GPU. All retrieval, reranking, and light synthesis runs at zero API cost. The frontier models only get involved for the synthesis that actually requires them.

I benchmarked the pipeline on DeepResearch Bench (DRB): RACE score 0.5166 across 50 tasks — competitive with Gemini Deep Research and NVIDIA AIQ on report quality. Citation accuracy was 57.8% validity, which is an honest weak point. The pipeline is good at producing coherent, well-structured research but it doesn't verify sources rigorously enough. That's a known issue, actively being addressed.

I also fine-tuned 7 local models on the vault's output over this period. That's a separate thread, but the short version is: if your knowledge base is large enough and consistent enough in style, you can distill some of what it knows into a smaller model. The quality ceiling is low, but for retrieval tasks and light classification it's useful.

### Stage 4 — autocontext (March 2026)

Then I found [autocontext](https://github.com/greyhaven-ai/autocontext) by greyhaven-ai. They'd built something complementary: a closed-loop system for improving agent behavior over repeated runs. Their multi-agent loop (competitor → analyst → coach → architect → curator) addresses problems I hadn't tackled:

- **Backpressure gating**: Rejects runs where the knowledge delta is below a threshold. Prevents noise from accumulating. My system accepted almost everything that passed the quality rubric — which is not the same thing as requiring that a run actually adds something new.
- **Lesson applicability windowing**: Lessons age out if not validated within N generations. I had self-improving rules with hit counters, but nothing that expired stale advice. Old lessons were just sitting there, potentially misleading future runs.
- **Versioned persistence with mutation logs**: Every knowledge change is tracked, checkpointed, and replayable. I had versioned files but no mutation log — no way to trace why a note changed.
- **Knowledge curation**: An LLM-based curator decides what to keep, merge, or discard. My pipeline was append-heavy. Autocontext's curator is a genuine quality gate at the persistence layer.

My system had the research pipeline and the search. Theirs had the evaluation discipline and the persistence architecture. This repo combines both.

---

## What This Combines

| Capability               | Source                                                     | How It Works                                                      |
| ------------------------ | ---------------------------------------------------------- | ----------------------------------------------------------------- |
| Search + knowledge graph | [vault-search](https://github.com/vachsark/vault-search)   | BM25 + embeddings + RRF + entity/relationship graph extraction    |
| Multi-wave research      | [autoknowledge](https://github.com/vachsark/autoknowledge) | Parallel agents → critic → skeptic → synthesis                    |
| Pre-flight dedup         | autoknowledge                                              | Search before researching — skip or narrow if overlap >85%        |
| Adversarial skeptic      | autoknowledge                                              | Challenges claims, rejects ~60% of weak connections               |
| Backpressure gate        | [autocontext](https://github.com/greyhaven-ai/autocontext) | Rejects runs below minimum quality delta                          |
| Knowledge curation       | autocontext                                                | LLM curator: accept / merge / discard decisions                   |
| Lesson tracking          | autocontext                                                | Applicability windowing — lessons decay when stale                |
| Versioned persistence    | autocontext                                                | Mutation log + checkpoints + replay                               |
| Self-improving rules     | vault system                                               | Evidence-tracked rules with hit counters and severity-based decay |
| Heartbeat scheduler      | vault system                                               | Autonomous task scheduling with state/config separation           |
| Model routing            | both                                                       | Frontier (Anthropic) for synthesis, local (Ollama) for retrieval  |
| Training export          | autocontext                                                | Validated knowledge → fine-tuning data                            |

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

## Benchmarks

Evaluated on [DRB (Deep Research Bench)](https://github.com/deepresearchbench/drb). The pipeline scored RACE 0.5166 across 50 tasks — competitive with Gemini Deep Research and NVIDIA AIQ on report quality. Citation accuracy was 57.8% validity, which is a known weak point.

Read the full benchmark analysis: [Building a Multi-Agent Research Pipeline — Benchmarked on DRB](https://blog.vachsark.com/blog/research-pipeline)

Run your own benchmark:

```bash
ke benchmark --suite drb --output results/
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

## Credits

This project wouldn't exist without:

- **[autocontext](https://github.com/greyhaven-ai/autocontext)** by greyhaven-ai — the evaluation loop architecture, backpressure gating, lesson management, and knowledge curation patterns. Their system showed me what disciplined knowledge persistence looks like.
- **[autoresearch](https://x.com/karpathy/status/2029701092347630069)** by Andrej Karpathy — the `program.md` pattern, single-metric evaluation, and the idea that agents should run experiments autonomously overnight.
- **[vault-search](https://github.com/vachsark/vault-search)** — hybrid semantic search + knowledge graph extraction. Powers pre-flight dedup, knowledge search, and entity/relationship context.
- **[autoknowledge](https://github.com/vachsark/autoknowledge)** — the predecessor project where the multi-wave research pipeline was developed and benchmarked.

---

## License

MIT — see [LICENSE](LICENSE).
