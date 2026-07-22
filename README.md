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

---

## Reflections (已知局限)

These are not bugs — they are honest constraints of the current design, recorded for future iteration.
这些问题不是 bug，是当前设计阶段的诚实约束。记录下来供未来迭代。

### 1. Binary Selection Pressure / 选择压力的二元化

The only "natural selection" is the Lean compiler: compiles = alive, otherwise = dead. Real-world selection involves metabolic efficiency, resource competition, niche differentiation, and symbiotic dynamics. Currently missing:
目前唯一的"自然选择"是 Lean 编译器：编译通过 = 存活，否则 = 死亡。自然界的选择压力远不止生死：

- **Metabolic cost differentiation / 代谢成本差异化** — different genes should consume different amounts of "energy"; longer code should be more expensive.
- **Niche competition / 生态位竞争** — genes of similar type should crowd each other out (currently only handled by the urn capacity cap).
- **Cooperation & parasitism / 合作与寄生** — inter-gene dependencies only manifest as compile-time references, with no mutualistic or antagonistic dynamics.

`metabolic_penalty` already scales reinforcement weight by code length, but it is only a first-order approximation. Genuine ecological dynamics would require richer interaction models.
`metabolic_penalty` 已根据代码长度缩放权重加成，但这只是第一阶近似。真正的生态动力学需要更丰富的交互模型。

### 2. Overly Discrete Generations / 过于明确的代际分割

The current model is discrete: all candidates compile in parallel within one generation, then the slate is wiped clean for the next. Nature has no such neat generational boundaries — parents and offspring coexist, death is gradual, birth is continuous.
当前是离散代模型：一代内所有候选并行编译，完成后清空，下一代全新开始。自然界不存在这样整齐的"代"边界——亲代和子代共存，死亡是渐进的，出生是连续的。

A more ideal model would be **continuous time + overlapping generations**: genes have lifespans, can die at any moment, and produce offspring at any time. Implementing this is a significant engineering challenge; the current compromise (parent-based reproduction + historical urn memory) is a pragmatic approximation.
更理想的模型是**连续时间 + 重叠代**：基因有寿命、随时可能死亡、随时产生子代。但这对实现复杂度是巨大挑战，当前折中（亲子繁殖 + 历史瓮记忆）是实用的近似。

### 3. Population Size & Computation Speed / 种群规模与计算速度

Real evolution relies on **massive populations**: millions of individuals across thousands of generations. Currently:
真实演化依赖**巨大种群**：数以百万计的个体、数以万计的世代。当前：

- Population ≈ tens to hundreds (number of tokens in the urn). / 种群 ≈ 几十到几百（瓮中 token 数）。
- Parallelism is bounded by CPU cores (`--workers` caps at dozens). / 并发上限受 CPU 核心限制（`--workers` 最多几十）。
- Single-generation latency is high (500 candidates × 2s ≈ thousands of seconds). / 单代耗时长（500 候选 × 2s = 千秒级）。

This means the combinatorial space explorable on human timescales is severely limited. A true "Cambrian Explosion" would likely require million-fold parallelism on distributed clusters, GPU-accelerated compilers, or an entirely different hardware architecture. On a single machine, we can only observe evolution at a microscopic scale — but just as telescopes can see billions of light-years away, tiny trends accumulated over enough time might still build massive structures.
这意味着在人类时间尺度上，系统能探索的组合空间极其有限。真正的"寒武纪大爆发"可能需要分布式集群上的百万级并行、GPU 加速的编译器、或完全不同的硬件架构。在单机上，我们只能观察微观尺度的演化——但正如望远镜能看到亿万光年外，微小的趋势经过足够长的时间也可能积累出巨大的结构。

---

## Future World / 未来世界

What would mathematics look like for a civilization born on a neutron star, or within a plasma state — where there are no rigid bodies, no Euclidean intuitions, only probability fields and fluid dynamics as the native sensory ground? Their axioms would not begin with points and lines, but with distributions and flows. Their "geometry" might be measure-theoretic from birth. Their concept of "equality" might be replaced by "convergence in distribution."

诞生于中子星或等离子态中的文明，他们的数学会是什么样子？那里没有刚体，没有欧几里得直觉——概率场和流体动力学才是原生的感官基底。他们的公理不会以点和线为起点，而是以分布和流为起点。他们的"几何"可能生来就是测度论的。他们的"相等"概念可能被"依分布收敛"取代。

If LUCA is allowed to run long enough — truly long, on hardware we cannot yet imagine — what kind of mathematics might it discover? Not *our* mathematics, built on the intuitions of savanna apes who evolved to track rigid objects and count discrete items. Something else. Something that might look as alien to us as general relativity would to a flatworm.

如果 LUCA 被允许运行足够久——真正地久，在我们尚无法想象的硬件上——它会发现什么样的数学？不是*我们*的数学，建立在稀树草原猿猴的直觉之上，那些猿猴演化出来是为了追踪刚体和计数离散物体。是别的什么。是对我们来说就像广义相对论之于扁形虫那样陌生的东西。

This is not a feature request. It is the only question that matters.
这不是功能需求。这是唯一重要的问题。
