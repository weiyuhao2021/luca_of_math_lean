"""Hyperparameters and global configuration for luca_of_math_lean."""

import os

# ---------------------------------------------------------------------------
# Urn limits & evolution
# ---------------------------------------------------------------------------
MAX_URN_SIZE: int = 500          # Max number of distinct tokens in the Pólya urn
INNOVATION_RATE: float = 2.0     # Initial weight for newly invented tokens
DECAY_RATE: float = 0.999        # Per-generation multiplicative weight decay

# Catastrophe: probability-driven by urn size (P = p0 × (size/MAX)^α)
CATASTROPHE_BASE_P: float = 0.005    # p0: base probability at full urn
CATASTROPHE_SIZE_EXPONENT: float = 2.0  # α: how steeply risk grows with size
CATASTROPHE_MIN_INTERVAL: int = 20   # Minimum generations between catastrophes

# ---------------------------------------------------------------------------
# Lean compiler sandbox
# ---------------------------------------------------------------------------
LEAN_TIMEOUT: float = 2.0        # Seconds before killing a lean subprocess

# ---------------------------------------------------------------------------
# Grammar / assembly limits
# ---------------------------------------------------------------------------
MAX_EXPRESSION_TOKENS: int = 8   # Max tokens sampled per candidate expression
MAX_DEFINITION_LENGTH: int = 512 # Max chars in generated Lean code
MAX_WORKERS: int = 8             # Max concurrent Lean verification threads (performance only)

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
EVOLUTION_OUTPUT_FILE: str = "evolved_library.lean"
URN_STATE_FILE: str = "urn_state.json"
EVOLUTION_LOG_FILE: str = "evolution_log.jsonl"
TMP_WORKSPACE: str = ".luca_tmp"

# ---------------------------------------------------------------------------
# Initial token soup (expanded per qwen's suggestion)
# ---------------------------------------------------------------------------
INITIAL_TOKENS: list[str] = [
    # ── 类型（化学元素周期表）──
    "Nat", "Bool", "Prop", "Unit", "String", "List", "Option", "Fin",
    "Int", "Char", "Array", "Subtype", "Sigma",
    # ── 值 / 字面量 ──
    "0", "1", "2", "3", "5", "10", "true", "false", "()", "[]", "none", "some",
    # ── 自然数运算 ──
    "Nat.add", "Nat.mul", "Nat.sub", "Nat.succ", "Nat.pred",
    "Nat.mod", "Nat.div", "Nat.pow", "Nat.min", "Nat.max",
    # ── 整数运算 ──
    "Int.add", "Int.mul", "Int.sub", "Int.neg",
    # ── 布尔运算 ──
    "Bool.and", "Bool.or", "Bool.not",
    # ── 列表操作 ──
    "List.map", "List.filter", "List.foldl", "List.length",
    "List.append", "List.reverse", "List.head?",
    "List.range", "List.take", "List.drop", "List.sum",
    "List.elem", "List.concat",
    # ── Option 操作 ──
    "Option.map", "Option.bind", "Option.getD",
    # ── 积类型 ──
    "Prod", "Prod.fst", "Prod.snd", "Prod.mk",
    # ── 逻辑连接词与量词 ──
    "=", "And", "Or", "Not", "Iff", "Exists", "∀", "∃",
    "True", "False", "trivial", "absurd",
    "Eq", "Decidable", "DecidableEq",
    # ── 构造与关键字 ──
    "fun", "λ", "if", "then", "else", "let", "have",
    "match", "with", "by", "rfl", "simp", "omega",
    "decide", "sorry",
    # ── 结构声明 ──
    "def", "theorem", "lemma", "example", "abbrev",
    "structure", "class", "instance",
    # ── 策略词（tactic primitives）──
    "intro", "intros", "apply", "exact", "cases",
    "rcases",
]


def ensure_workspace() -> str:
    """Create the temporary workspace directory if it does not exist."""
    os.makedirs(TMP_WORKSPACE, exist_ok=True)
    return TMP_WORKSPACE
