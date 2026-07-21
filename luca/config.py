"""Hyperparameters and global configuration for luca_of_math_lean."""

import os

# ---------------------------------------------------------------------------
# Urn limits & evolution
# ---------------------------------------------------------------------------
MAX_URN_SIZE: int = 500          # Max number of distinct tokens in the Pólya urn
INNOVATION_RATE: float = 2.0     # Initial weight for newly invented tokens
DECAY_RATE: float = 0.999        # Per-generation multiplicative weight decay
CATASTROPHE_PROBABILITY: float = 0.005  # Per-generation chance of a catastrophe

# ---------------------------------------------------------------------------
# Lean compiler sandbox
# ---------------------------------------------------------------------------
LEAN_TIMEOUT: float = 2.0        # Seconds before killing a lean subprocess

# ---------------------------------------------------------------------------
# Grammar / assembly limits
# ---------------------------------------------------------------------------
MAX_EXPRESSION_TOKENS: int = 8   # Max tokens sampled per candidate expression
MAX_DEFINITION_LENGTH: int = 512 # Max chars in generated Lean code

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
    # Types
    "Nat", "Bool", "Prop", "Unit", "String", "List", "Option", "Fin",
    # Values
    "0", "1", "2", "true", "false", "()", "[]", "none", "some",
    # Arithmetic
    "Nat.add", "Nat.mul", "Nat.sub", "Nat.succ", "Nat.pred",
    "Nat.mod", "Nat.div", "Nat.pow", "Nat.min", "Nat.max",
    # Boolean
    "Bool.and", "Bool.or", "Bool.not",
    # List
    "List.map", "List.filter", "List.foldl", "List.length",
    "List.append", "List.reverse", "List.head?",
    # Option
    "Option.map", "Option.bind", "Option.getD",
    # Logic
    "=", "And", "Or", "Not", "Iff", "Exists", "∀", "∃",
    "True", "False", "trivial", "absurd",
    # Constructs
    "fun", "λ", "if", "then", "else", "let", "have",
    "match", "with", "by", "rfl", "simp", "omega",
    "sorry",
    # Structures
    "def", "theorem", "lemma", "example", "abbrev",
    "structure", "class", "instance",
]


def ensure_workspace() -> str:
    """Create the temporary workspace directory if it does not exist."""
    os.makedirs(TMP_WORKSPACE, exist_ok=True)
    return TMP_WORKSPACE
