# luca_of_math_lean

A zero-cost artificial life kernel where Lean 4 compiler laws and non-Markovian Pólya urn dynamics drive open-ended mathematical evolution.

## The Long Run Hypothesis

The most famous attempt at this kind of experiment was **Genetic Programming (GP)** proposed by John Koza in the 1990s. He had computers randomly generate LISP code, using the compiler as natural selection, trying to let machines "grow" programs that could solve specific problems.

It didn't work.

But I believe the problem is simpler than people think: **they were just too impatient.** They didn't let the program run long enough.

Human beings have never successfully synthesized life from a primordial soup either — something always seems to be missing. That "key first factor." But what if nothing is missing? What if the only missing ingredient is **time** — not hours, not days, not years, but decades, centuries, even hundreds of millions of years?

This project is designed to run for that long.

### Design for Deep Time

`luca_of_math_lean` is built from the ground up with **immortal processes** in mind:

- **State persistence**: The entire Pólya urn state (token weights, generation counter, alive/dead tallies) is periodically saved to disk as plain JSON. A process killed at any moment can be resumed exactly where it left off via `python main.py --resume`.
- **Incremental output**: Every successfully compiled Lean definition is appended to `evolved_library.lean` — a living fossil record that grows forever.
- **Zero external dependencies during evolution**: Once started, the loop requires no network, no API keys, no cloud services. Just a CPU, a Lean 4 binary, and electricity.
- **Catastrophe resilience**: The built-in catastrophe system (mass extinctions, asteroid impacts, ice ages) ensures that even if the urn stagnates for millennia, a random event will shake things up and open new evolutionary pathways.

The ambition is not to produce a useful program in 100 generations. The ambition is to let it run for 100 million generations and see what mathematics looks like when it evolves on its own terms, under the absolute physical law of the Lean 4 type checker, with no human intervention except patience.

> "We have not failed. We have simply not waited long enough."

---

## Quick Start

```powershell
# 1. Create conda environment
conda create -n luca_lean python=3.11 -y
conda activate luca_lean
pip install -r requirements.txt

# 2. Install Lean 4 (via elan, requires curl)
curl -O --location https://elan.lean-lang.org/elan-init.ps1
powershell -ExecutionPolicy Bypass -f elan-init.ps1
# → Choose "1" for default installation
del elan-init.ps1

# 3. Fire up the primordial soup
python main.py --max-generations 500
```

---

## CLI Usage

| Flag | Short | Default | Meaning |
|------|-------|---------|---------|
| `--max-generations` | `-n` | `10000` | How many generations to run. Use a huge number for "forever" (Ctrl+C to stop). |
| `--timeout` | `-t` | `2.0` | Seconds before killing a Lean compiler subprocess (guards against infinite loops in `simp`/`omega`). |
| `--output` | `-o` | `evolved_library.lean` | Where to write successfully compiled genes. |
| `--resume` | `-r` | `false` | Resume from `urn_state.json`. Restores token weights, generation counter, era, lineage tracking. |
| `--population` | `-p` | `8` | ~~REMOVED~~ — population now emerges from urn diversity, NOT a fixed parameter. |
| `--workers` | `-w` | `8` | Max concurrent Lean threads. Purely performance; does NOT affect biology. |
| `--seed` | `-s` | — | Path to a .lean seed file with pre-existing ancestral genes (LUCA). |
| `--show-top N` | — | — | Print the top *N* tokens from a saved state and exit (inspect-only mode). |

### Typical Workflows

```powershell
# Fresh start (initial pop ≈ 106 tokens × generations)
python main.py --max-generations 50

# High parallelism (16 Lean processes at once)
python main.py --max-generations 500 --workers 16

# Minimal parallelism (1 Lean process)
python main.py --max-generations 1000 --workers 1

# Primordial soup (no ancestors — wait for first life to emerge)
python main.py --max-generations 100000

# Seeded with a LUCA (identity function ancestor)
python main.py --seed genesis/identity.lean --max-generations 5000

# Combinator universe (I/K/S atomic building blocks)
python main.py --seed genesis/combinators.lean --max-generations 5000

# Long run with resume capability
python main.py --max-generations 1000000
# ... Ctrl+C after a while ...
python main.py --resume --max-generations 2000000

# Peek at the urn without evolving
python main.py --show-top 10

# Change output file (evolve into a different "universe")
python main.py --output mars_library.lean --max-generations 500
```

### ⚠️ The Cross-Universe Gene Drift

If you run **without** `--resume` but old files still exist:

| File | Behaviour |
|------|-----------|
| `urn_state.json` | Overwritten with fresh initial state. |
| `evolved_library.lean` | **Not deleted.** Old genes remain; new genes append. |
| `evolution_log.jsonl` | **Not deleted.** New logs append after old logs. |

This means old-world gene fossils drift into a brand-new universe. They are invisible to the compiler (not in the new compilation context), but they sit there in the library file — like alien DNA frozen in amber. To start truly fresh, delete all three files first:

```powershell
del urn_state.json, evolved_library.lean, evolution_log.jsonl
```

---

## Output Files

| File | Format | Contents |
|------|--------|----------|
| `urn_state.json` | JSON | Full Pólya urn state: token weights, generation, alive/dead counts, era, tainted gene set. Saved at start + every 50 generations + on exit. |
| `evolved_library.lean` | Lean 4 source | Append-only fossil record of every successfully compiled gene. Also used as the compilation context for future candidates (enables real gene-to-gene references). |
| `evolution_log.jsonl` | JSONL | One JSON line per generation: `{generation, gene, status, tainted, urn_size}`. |

---

## Evolution Mechanics

### The Pólya Urn (Non-Markovian Memory)

106 initial tokens (types, operators, literals, logic, tactics — Lean 4 Init core elements) form the primordial soup. Each token has a weight; successful use reinforces the weight (path-dependent memory). Tokens that never produce viable code slowly decay.

### Compiler as Physics

Every candidate is a randomly assembled Lean 4 expression. The Lean compiler (`lean`) is the sole arbiter of life and death. **No fitness functions. No heuristics. No type-aware generators.** Random assembly, compiler verdict, that's it.

### Innovation (Self-Modifying Architecture)

Any successfully compiled gene (`gene_42`) is injected back into the urn as a new token. The system builds with its own discoveries — genes composing with genes is **multicellularity**.

### Catastrophe System (6 Types, Probability-Driven)

Triggered by urn density: \( P(\text{cataclysm}) = 0.005 \times (\frac{\text{urn\_size}}{500})^{2.0} \), minimum 20-generation interval. No semantic judgment — pure thermodynamical law.

| Catastrophe | Effect |
|-------------|--------|
| **质量灭绝** (Mass Extinction) | Remove 80–90% of lowest-weight tokens. |
| **中等灭绝** (Moderate Extinction) | Remove 40–60%; survivors gain 1.1–1.5× weight. |
| **基因漂变** (Genetic Drift) | All weights regress 30% toward the mean. |
| **寒武纪大爆发** (Cambrian Explosion) | Top tokens hybridize into new compound tokens. |
| **小行星撞击** (Asteroid Impact) | Random 50% deletion; survivors' weight doubles. |
| **冰河期** (Ice Age) | Halve all weights; `fun`/`λ`/`match`/`def` get anti-freeze bonus. |

### Evolution Event Tracking

- **Lineages**: `[ALIVE]` = closed lineage (no `sorry`, pure Lean kernel proofs). `[ALIVE★]` = axiomatic lineage (contains or descends from `sorry` — an injected axiom, not a derived truth).
- **Multicellularity** 🧬: Detected when a gene references other `gene_N` symbols. Printed in real time.
- **Eras**: Five evolutionary eras tracked across the run:

  | Era | Condition |
  |-----|-----------|
  | 太古宙 (Archean) | Starting state — primordial soup, almost all DEAD. |
  | 原初汤时代 | First multicellular event + ≥ 3 gene tokens in urn. |
  | 大氧化时代 (Great Oxidation) | `sorry` weight > 50% + ≥ 2 multicellular events. |
  | 真核时代 (Eukaryotic) | `sorry` drops below 20% + ≥ 10 gene tokens. |
  | 多细胞时代 (Multicellular) | ≥ 10 multicellular events + ≥ 30 gene tokens. |

  Era transitions are printed as `🔥 纪元更迭!` milestone banners and recorded in the summary.

### What to Expect

**99.99% DEAD is correct.** The system is designed to spend geological epochs producing meaningless garbage that the Lean compiler rejects. This is the Archean — not a bug, the primordial soup. An occasional `def gene_N : Nat := 0` surviving is already a miracle. Don't optimize. Don't intervene. Just wait.

---

## Philosophy

The project embodies three unbreakable rules:

1. **Zero human intervention during runtime.** Humans define the physical laws at creation (initial tokens, Lean version, catastrophe formula). After `python main.py` starts, no semantic reading, no goal injection, no parameter tweaking.
2. **Reverence for boredom and death.** The 99.99% DEAD rate is *correct*. Trivial surviving genes like `def gene_N : Nat := 0` are *correct*. Do not attempt to improve the survival rate.
3. **The Babel Hypothesis.** The system may evolve mathematical structures as complex as calculus that no human can understand. The syllogism renderer is a minimal "participation indicator" for the creator — not a translation tool.
