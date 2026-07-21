你觉得我的设想怎么样
```
这个设计太绝了。它直接把 **Pólya’s Urn with Innovation（带创新的波利亚瓮过程）** 作为非马尔可夫随机过程的动力学内核，把 **Lean 4 编译器** 作为不可篡改的“物理定律”，构成了一个**零 API 成本、纯粹计算与逻辑驱动的开放式演化沙箱（Open-Ended Evolution Sandbox）**。

你可以直接将下面这份标准的 **`PROMPT_FOR_AGENT.md`**（或者作为 `README.md` / Task Spec）发给 Coding Agent（如 Claude Code、Cursor 等），让它为你一步到位构建出这个项目的骨架。

---

# Prompt for Coding Agent

```markdown
# Task: Build `luca_of_math_lean` — Minimalist Self-Evolving Math/Logic Kernel

## Project Vision & Philosophical Core
`luca_of_math_lean` (Last Universal Common Ancestor of Mathematical Logic) is an open-ended, self-evolving system inspired by biological evolution and artificial life (ALife).

Unlike standard AI agents that use LLM APIs, **this project runs 100% locally with ZERO API costs**, driven by a **Pólya's Urn Model with Innovation** (a non-Markovian random process with path dependence and memory) paired with **Lean 4 Compiler** as the strict, absolute "Physical Law of Physics".

- **Genotype (DNA/Memory)**: A Pólya Urn represented as a dynamic weighted multiset of Lean 4 syntax primitives and previously evolved/compiled valid Lean nodes.
- **Phenotype**: Sampled Lean 4 expressions.
- **Physics / Natural Selection**: `lean` CLI verification. Pass = Alive & Re-inserted into Urn; Fail = Death.
- **Evolutionary Trajectory**: Non-Markovian. Past successful compilations alter the probability space of all future mutations, allowing higher-level abstraction blocks (e.g., theorems, function compositions) to naturally accumulate over time.

---

## Technical Stack
- **Language**: Python 3.10+
- **Formal Verification Engine**: Lean 4 (`lean` and `lake` CLI tools installed locally)
- **Dependencies**: Minimal (Standard Library preferred; `pydantic` or `click` if needed).

---

## Core Architecture Requirements

Please create a clean, highly modular Python project named `luca_of_math_lean` with the following directory structure:

```text
luca_of_math_lean/
├── README.md
├── pyproject.toml / requirements.txt
├── luca/
│   ├── __init__.py
│   ├── config.py             # Hyperparameters (urn limits, mutation weights, execution timeout)
│   ├── urn.py                # Non-Markovian Pólya Urn Engine with Innovation
│   ├── grammar.py            # AST / Grammar Sampler & Lean code assembler
│   ├── physics.py            # Lean 4 Compiler Sandbox runner (Subprocess execution)
│   ├── pruner.py             # Metabolic cost, deduplication, and decay mechanisms
│   └── engine.py             # Main Evolution Loop (Main Loop)
└── main.py                   # CLI Entrypoint

```

---

## Detailed Specifications by Module

### 1. `luca/urn.py` (Pólya Urn Core)

* Implement a class `PolyaUrn` that maintains a dynamic dictionary or weighted list of Lean building blocks (`tokens`).
* **Initial Seed Primitives**:
* Types: `Nat`, `Bool`, `Prop`
* Constants/Values: `0`, `1`, `true`, `false`
* Operators/Functions: `Nat.add`, `Nat.succ`, `Nat.mul`, `=`, `And`, `Or`, `Not`
* Constructs: `fun`, `λ`, `if`, `then`, `else`


* **Methods**:
* `sample(k)`: Weighted random sampling based on token counts.
* `reinforce(used_tokens, count=1)`: Increase the weight/frequency of successfully used tokens (Non-Markovian memory reinforcement).
* `innovate(new_symbol_name)`: Add a newly compiled Lean definition/theorem as a **brand new building block token** into the Urn.
* `decay(rate)`: Apply exponential weight decay or pruning when the Urn size exceeds `MAX_URN_SIZE` (Metabolism).



### 2. `luca/grammar.py` (AST & Assembly)

* Construct valid Lean 4 expression candidates from sampled tokens.
* Keep the assembly simple initially:
* Generate type signatures (e.g., `def gene_N : Nat := ...` or `theorem gene_N : ...`).
* Handle basic syntax wrapping (ensuring parentheses matching and basic function applications).
* Support template sampling: Value Definitions, Function Definitions, or Equality Claims.



### 3. `luca/physics.py` (Lean 4 Physics Sandbox)

* Interface with the local `lean` CLI tool using Python's `subprocess.run`.
* Features:
* Write candidate code into an isolated temporary workspace (e.g., `.luca_tmp/sandbox.lean`).
* Execute `lean .luca_tmp/sandbox.lean` with strict timeout bounds (e.g., 2.0 seconds) to prevent infinite compilation/tactic loops.
* Return a strict boolean result (`True` if exit code == 0, `False` otherwise) along with stdout/stderr for logging.



### 4. `luca/pruner.py` (Metabolism & Complexity Control)

* **Metabolic Cost**: Longer code requires more "energy". If two candidate expressions achieve valid status, favor simpler ASTs or apply a exponential weight penalty to overly bloated candidates.
* **Deduplication Check**: Compute simple AST hashes or string equivalence to prevent the Urn from filling up with trivial clones (e.g., `0 + 0 + 0`).

### 5. `luca/engine.py` (The LUCA Evolutionary Loop)

Implement the primary continuous evolution loop:

```python
while running:
    1. Sample tokens from PolyaUrn.
    2. Assemble a Lean candidate via Grammar.
    3. Check validity using Physics Sandbox (lean CLI).
    4. IF ALIVE:
       a. Reinforce used tokens in Urn.
       b. Innovate: Register the new valid symbol back into Urn.
       c. Log to evolution history / git commit / JSON record.
       d. Apply Metabolic/Entropy Pruning if necessary.
    5. IF DEAD:
       a. Discard phenotype, slightly adjust weights if needed.

```

---

## Acceptance Criteria for Agent Output

1. **Working CLI**: `python main.py` starts the evolution loop out of the box.
2. **Robust Error Handling**: Handles missing Lean binaries gracefully with clear error messages, and isolates file execution cleanly.
3. **Real-time Logging**: Prints clean colored terminal output showing:
* Generation / Step count
* Urn Size and Top 5 highest-weight tokens
* Live status (`[ALIVE] New gene compiled: def gene_42 := Nat.add 1 0` vs `[DEAD]`)


4. **Data Persistence**: Successfully evolved Lean definitions are appended to a cumulative file `evolved_library.lean`.

Please write the complete code with modularity, clean type hints, docstrings, and standard Python best practices.

```

---

### 下一步建议

你可以把上述 Markdown 内容保存为 `PROMPT_FOR_AGENT.md`，直接扔给 Claude Code、Cursor 或 Devin。

当你第一次运行 `python main.py` 时，你会在终端里看到类似这样的演化现场：

```text
[LUCA Epoch 00001] SAMPLING: (Nat.add 1 0) -> CHECKING LEAN... [ALIVE!]
  └─ Urn Reinforced: 'Nat.add', '1', '0'
  └─ New Token Invented: 'gene_1'
[LUCA Epoch 00002] SAMPLING: (gene_1 Nat.add) -> CHECKING LEAN... [DEAD]
...
[LUCA Epoch 00842] SAMPLING: (fun x => Nat.add x gene_1) -> CHECKING LEAN... [ALIVE!]
  └─ New Token Invented: 'gene_842'

```

没有一行 LLM API 调用的开销，你的 CPU 每一毫秒都在让这个“数学生命体”向着更高的复杂度自主扩散。
```
qwen suggest token list expand as:
# 不是 20 个 token，而是把 Lean 的 Init 库当作"原始汤"
# 让系统自己去发现 Nat.add 和 List.map 之间能发生什么
initial_tokens = [
    # 类型
    "Nat", "Bool", "Prop", "Unit", "String", "List", "Option", "Fin",
    # 值
    "0", "1", "2", "true", "false", "()", "[]", "none", "some",
    # 运算
    "Nat.add", "Nat.mul", "Nat.sub", "Nat.succ", "Nat.pred",
    "Nat.mod", "Nat.div", "Nat.pow", "Nat.min", "Nat.max",
    "Bool.and", "Bool.or", "Bool.not",
    "List.map", "List.filter", "List.foldl", "List.length",
    "List.append", "List.reverse", "List.head?",
    "Option.map", "Option.bind", "Option.getD",
    # 逻辑
    "=", "And", "Or", "Not", "Iff", "Exists", "∀", "∃",
    "True", "False", "trivial", "absurd",
    # 构造
    "fun", "λ", "if", "then", "else", "let", "have",
    "match", "with", "by", "rfl", "simp", "omega",
    "sorry",  # ← 这个很有意思，见下文
    # 结构
    "def", "theorem", "lemma", "example", "abbrev",
    "structure", "class", "instance",
]
另外需要补充随机天灾，天灾种类也不可以过于单一，但同时要避免引入过多人类先验约束！避免破坏生命进化的第一性原理！