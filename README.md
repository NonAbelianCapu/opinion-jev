# Opinion spreading with a decision model (Jev)

Does a typed decision model change what an opinion-spreading simulation predicts? This repo asks
TypeSafe's Jev separate questions about each exposure (does the person believe the message, do
they share it, and how would they change it) and compares the answers with a hand-written
logistic rule (the "stand-in"). When someone shares, an LLM rewrites the message the way Jev
said they would, so the rumor mutates as it spreads.

**Caveat for every result here.** Jev is a closed model, reportedly trained on synthetic data.
Its answers show what the model believes about people, not how people behave. Nobody has checked
whether its probabilities are calibrated on this kind of text, and this repo has no labeled
data to check it with.

## Status

- Phase 0 (API check, package, offline tests): done. Raw API responses in `results/phase0/`.
- Mutating spread: done. 2 starting messages x 2 engines x 20 seeds on a 64-node network.
  Results in `results/spread/`, interactive page in `results/spread/rumor.html`.
- Phase 1 response profile and the Colab notebooks: not done yet.

## How a run works

The network is a jittered 8x8 grid: each person links to their 3 nearest neighbors, plus 5
random long links. The message starts at the best-connected person. At each step, everyone who
shared in the previous step sends their version to their contacts. Each newly exposed person:

1. reads one of the versions they were sent,
2. gets P(believe) and P(share) from the engine, and the simulator samples both,
3. if they share (once per person), gets probabilities for five edits (verbatim, exaggerate,
   soften, add a detail, change the source), and the simulator samples one,
4. an LLM (`google/gemini-3.1-flash-lite` through OpenRouter) writes the new version,
5. Jev scores the new version for emotion and extremity (0 to 4).

The stand-in cannot read text, so it uses fixed edit odds and ignores the wording. Its runs are
identical for both messages, seed by seed.

## First results (20 seeds per engine and message)

| | bins, Jev | bins, stand-in | pool, Jev | pool, stand-in |
|---|---|---|---|---|
| shared by the end | 21% | 29% | 21% | 29% |
| believe by the end | 12% | 39% | 13% | 39% |
| most common edits | soften 43%, exaggerate 38% | verbatim 49%, exaggerate 24% | soften 42%, exaggerate 41% | same as bins |
| extremity of new versions (0 to 4) | 1.63 | 2.27 | 1.96 | 2.69 |

Under Jev, belief and sharing come apart: people with belief below 0.5 still shared with mean
probability 0.33. The difference in final belief between engines is clear (95% bootstrap
interval of the difference: -33 to -18 points). The difference in reach is not (-16 to +1).

## Setup

```bash
uv sync
uv run pytest        # offline, no API key needed
```

Rebuild everything from the cache, with no API calls:

```bash
for sc in bins pool; do for en in jev standin; do
  uv run python scripts/run_spread.py --scenario $sc --engine $en --seeds $(seq 0 19)
done; done
uv run python scripts/build_page.py
```

Add `--live` to allow API calls for runs that are not cached yet.

In Colab:

```python
!pip install "git+<repo url>"
```

Add `TYPESAFE_API_KEY` as a Colab secret (key icon in the left sidebar). The code reads the
`TYPESAFE_API_KEY` environment variable first, then the Colab secret, then
`~/.config/typesafe/api_key`. The rewriter reads `OPENROUTER_API_KEY` the same way (fallback
`~/.config/openrouter/api_key`). Never put keys in the repo; `.gitignore` covers `.env`.

## Layout

| Path | What it does |
|---|---|
| `src/jevsim/state_encoder.py` | Builds the state from person, message, source and context: the text Jev reads and the numbers the stand-in reads, from the same inputs |
| `src/jevsim/questions.py` | The three questions: `believe` (choice), `trust_source` (score 0 to 4), `share` (yes/no) |
| `src/jevsim/engines/` | `StandInEngine`, `JevEngine` (cache, retries, version pin), `HttpTransport`, `FakeTransport` |
| `src/jevsim/cache.py` | One JSON file per request under `results/cache/`, keyed by model, state, questions and replicate |
| `src/jevsim/budget.py` | Token and cost estimate before every batch |
| `src/jevsim/logger.py` | JSONL log of every decision |
| `src/jevsim/simulator/` | Contact network, seeded sampling and the mutating spread (`dynamics.py`) |
| `src/jevsim/rewriter.py` | LLM rewrites through OpenRouter, cached |
| `src/jevsim/scenarios.py` | The starting messages |
| `src/jevsim/viz.py` | The interactive HTML page |
| `scripts/` | `run_spread.py` runs or replays seeds, `build_page.py` builds the page |
| `results/thread/` | Draft X thread and its images |

Engines return probabilities. The simulator samples from them with its own seeded RNG.

## Cost and reproducibility

- Price: $0.042 per million input tokens. Output tokens are free.
- A request with three questions uses about 500 input tokens, so 1,000 requests cost about
  $0.02. The 80 runs in `results/spread/` cost about $0.05 of Jev and $0.08 of OpenRouter.
- `run_batch` is a dry run by default. It prints the estimated cost of the uncached requests and
  sends nothing until you pass `dry_run=False`. Above $1 it also requires `confirm=True`.
- The API is not idempotent: the same request can return slightly different numbers and is
  billed every time. The cache key includes a replicate index, so repeated calls on purpose are
  separate entries, and every run replays from the cache afterwards.
- The model is pinned to `jev-1.13.0`. A response from any other version raises an error.
- `JevEngine(..., offline=True)` reads only the cache, so notebooks can rebuild every plot with no
  API calls.
