"""Grammar Sampler & Lean 4 code assembler for evolutionary candidate generation."""

import random
import re
from typing import Optional

from luca.config import MAX_EXPRESSION_TOKENS, MAX_DEFINITION_LENGTH


# ---------------------------------------------------------------------------
# Token classification helpers
# ---------------------------------------------------------------------------

# Tokens that are purely structural / keyword
_STRUCTURAL: set[str] = {
    "def", "theorem", "lemma", "example", "abbrev",
    "structure", "class", "instance",
    "fun", "λ", "if", "then", "else", "let", "have",
    "match", "with", "by", "rfl", "simp", "omega", "sorry",
    "=", "And", "Or", "Not", "Iff", "Exists", "∀", "∃",
    "Eq", "intro", "intros", "apply", "exact", "cases",
    "rcases", "decide",
}

# Tokens that can appear inside expressions
_EXPR_TOKENS: set[str] = {
    "Nat.add", "Nat.mul", "Nat.sub", "Nat.succ", "Nat.pred",
    "Nat.mod", "Nat.div", "Nat.pow", "Nat.min", "Nat.max",
    "Int.add", "Int.mul", "Int.sub", "Int.neg",
    "Bool.and", "Bool.or", "Bool.not",
    "List.map", "List.filter", "List.foldl", "List.length",
    "List.append", "List.reverse", "List.head?",
    "List.range", "List.take", "List.drop", "List.sum",
    "List.elem", "List.concat",
    "Option.map", "Option.bind", "Option.getD",
    "Prod.fst", "Prod.snd", "Prod.mk",
}

# Literal values that can be leaf nodes
_LITERALS: set[str] = {
    "0", "1", "2", "3", "5", "10", "true", "false", "()", "[]", "none", "some",
}

# Types
_TYPES: set[str] = {
    "Nat", "Bool", "Prop", "Unit", "String", "List", "Option", "Fin",
    "Int", "Char", "Array", "Subtype", "Sigma", "Prod",
}

# Logic constants
_LOGIC_CONSTANTS: set[str] = {"True", "False", "trivial", "absurd", "Decidable", "DecidableEq"}


def _is_gene_name(token: str) -> bool:
    """Check if a token looks like a previously-evolved gene name."""
    return bool(re.match(r"^gene_\d+$", token))


class LeanAssembler:
    """Assembles sampled tokens into Lean 4 candidate expressions.

    The assembler uses a template-based approach: it picks a structural
    template (def, theorem, fun, if-then-else) and fills in the blanks
    with content tokens drawn from the Pólya urn sample.

    Correctness is NOT guaranteed -- the Lean compiler (physics.py) is
    the ultimate judge.
    """

    def __init__(self) -> None:
        self._gene_counter: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble(self, tokens: list[str]) -> tuple[str, str]:
        """Build a Lean candidate from sampled tokens.

        Args:
            tokens: Weighted-sampled tokens from the Pólya urn.

        Returns:
            (code_string, gene_name) tuple.  gene_name looks like 'gene_42'.
        """
        self._gene_counter += 1
        gene_name = f"gene_{self._gene_counter}"

        # Classify tokens
        content_tokens = [
            t for t in tokens
            if t in _EXPR_TOKENS or t in _LITERALS or t in _TYPES
            or t in _LOGIC_CONSTANTS or _is_gene_name(t)
        ]
        structural_tokens = [t for t in tokens if t in _STRUCTURAL]

        # If no content tokens, use some defaults
        if not content_tokens:
            content_tokens = ["0", "1", "Nat.add"]

        # Pick a template
        template_roll = random.random()

        if "by" in structural_tokens and "rfl" in structural_tokens and template_roll < 0.2:
            code = self._build_theorem_rfl(gene_name, content_tokens)
        elif ("fun" in structural_tokens or "λ" in structural_tokens) and template_roll < 0.4:
            code = self._build_lambda(gene_name, content_tokens, structural_tokens)
        elif "if" in structural_tokens and template_roll < 0.55:
            code = self._build_ite(gene_name, content_tokens)
        elif "match" in structural_tokens and template_roll < 0.65:
            code = self._build_match(gene_name, content_tokens)
        elif template_roll < 0.8:
            code = self._build_function_def(gene_name, content_tokens)
        else:
            code = self._build_simple_def(gene_name, content_tokens)

        # Truncate if too long
        if len(code) > MAX_DEFINITION_LENGTH:
            code = code[:MAX_DEFINITION_LENGTH].rstrip()

        return code, gene_name

    # ------------------------------------------------------------------
    # Template builders
    # ------------------------------------------------------------------

    def _build_simple_def(self, gene_name: str, tokens: list[str]) -> str:
        """def gene_N : Nat := <simple_expression>"""
        expr = self._build_expression(tokens, arity=random.randint(1, 3))
        ret_type = self._pick_type(tokens)
        return f"def {gene_name} : {ret_type} := {expr}"

    def _build_function_def(self, gene_name: str, tokens: list[str]) -> str:
        """def gene_N (x : Nat) : Nat := <expression with x>"""
        ret_type = self._pick_type(tokens)
        param_type = self._pick_type(tokens)
        expr = self._build_expression(tokens, arity=random.randint(2, 4))
        # Insert the parameter into the expression
        if random.random() < 0.5:
            expr = f"Nat.add x ({expr})"
        return f"def {gene_name} (x : {param_type}) : {ret_type} := {expr}"

    def _build_theorem_rfl(self, gene_name: str, tokens: list[str]) -> str:
        """theorem gene_N : <lhs> = <rhs> := by rfl"""
        lhs = self._build_expression(tokens, arity=random.randint(1, 2))
        rhs = self._build_expression(tokens, arity=random.randint(1, 2))
        # Sometimes make them identical so rfl works
        if random.random() < 0.4:
            rhs = lhs
        return f"theorem {gene_name} : {lhs} = {rhs} := by rfl"

    def _build_lambda(
        self, gene_name: str, tokens: list[str], structural: list[str]
    ) -> str:
        """def gene_N : Nat -> Nat := fun x => <expression>"""
        lam = "λ" if "λ" in structural else "fun"
        ret_type = self._pick_type(tokens)
        expr = self._build_expression(tokens, arity=random.randint(2, 4))
        return f"def {gene_name} : Nat → {ret_type} := {lam} x => {expr}"

    def _build_ite(self, gene_name: str, tokens: list[str]) -> str:
        """def gene_N : Nat := if <cond> then <a> else <b>"""
        ret_type = self._pick_type(tokens)
        cond = self._build_expression(
            [t for t in tokens if t in ("true", "false", "0", "1")] or ["true"],
            arity=1,
        )
        a_expr = self._build_expression(tokens, arity=random.randint(1, 2))
        b_expr = self._build_expression(tokens, arity=random.randint(1, 2))
        return f"def {gene_name} : {ret_type} := if {cond} then {a_expr} else {b_expr}"

    def _build_match(self, gene_name: str, tokens: list[str]) -> str:
        """Simple match expression on a Nat."""
        ret_type = self._pick_type(tokens)
        base = self._build_expression(tokens, arity=1)
        succ_expr = self._build_expression(tokens, arity=random.randint(1, 2))
        return (
            f"def {gene_name} : Nat → {ret_type} := fun n => "
            f"match n with | 0 => {base} | Nat.succ m => {succ_expr}"
        )

    # ------------------------------------------------------------------
    # Expression builder
    # ------------------------------------------------------------------

    def _build_expression(
        self, tokens: list[str], arity: int = 2, depth: int = 0,
    ) -> str:
        """Recursively build an expression from tokens.

        Args:
            tokens: Available content tokens.
            arity: Desired number of sub-expressions (approximate).
            depth: Current recursion depth (hard-capped at 6).
        """
        # Safety cap: force leaf after 6 levels of nesting
        if depth >= 6 or not tokens:
            return "0"

        # Pick an operator token
        ops = [t for t in tokens if t in _EXPR_TOKENS]
        lits = [t for t in tokens if t in _LITERALS or _is_gene_name(t)]

        if not ops and not lits:
            return "0"

        # Decide: leaf or apply?
        if not ops or (lits and random.random() < 0.3):
            return random.choice(lits if lits else ["0"])

        op = random.choice(ops)
        # Determine number of arguments required
        n_args = self._arity_of(op, arity)

        # Build arguments
        args: list[str] = []
        for _ in range(n_args):
            if tokens and random.random() < 0.4:
                arg_tokens = random.sample(
                    tokens, min(3, len(tokens))
                ) if len(tokens) > 1 else tokens
                args.append(self._build_expression(arg_tokens, arity=1, depth=depth + 1))
            else:
                arg = self._pick_leaf(tokens, lits)
                args.append(arg)

        # Assemble: (op arg1 arg2 ...)
        if len(args) == 1:
            return f"({op} {args[0]})"
        elif len(args) == 2:
            return f"({op} {args[0]} {args[1]})"
        else:
            args_str = " ".join(args)
            return f"({op} {args_str})"

    def _pick_leaf(self, tokens: list[str], lits: list[str]) -> str:
        """Pick a leaf node: a literal, gene name, or small expression."""
        if lits and random.random() < 0.7:
            return random.choice(lits)
        if tokens:
            return random.choice(tokens)
        return "0"

    def _pick_type(self, tokens: list[str]) -> str:
        """Pick a return type from available type tokens."""
        types = [t for t in tokens if t in _TYPES]
        if types:
            return random.choice(types)
        return "Nat"

    @staticmethod
    def _arity_of(op: str, default: int = 2) -> int:
        """Estimate the expected number of arguments for an operator."""
        arity_map: dict[str, int] = {
            "Nat.succ": 1, "Nat.pred": 1,
            "Nat.add": 2, "Nat.mul": 2, "Nat.sub": 2,
            "Nat.mod": 2, "Nat.div": 2, "Nat.pow": 2,
            "Nat.min": 2, "Nat.max": 2,
            "Int.add": 2, "Int.mul": 2, "Int.sub": 2, "Int.neg": 1,
            "Bool.and": 2, "Bool.or": 2, "Bool.not": 1,
            "List.map": 2, "List.filter": 2, "List.foldl": 3,
            "List.length": 1, "List.append": 2,
            "List.reverse": 1, "List.head?": 1,
            "List.range": 1, "List.take": 2, "List.drop": 2,
            "List.sum": 1, "List.elem": 2, "List.concat": 2,
            "Option.map": 2, "Option.bind": 2, "Option.getD": 2,
            "Prod.fst": 1, "Prod.snd": 1, "Prod.mk": 2,
        }
        return arity_map.get(op, default)
