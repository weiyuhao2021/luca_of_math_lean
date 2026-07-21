"""Metabolic cost, deduplication, and decay mechanisms for evolutionary pruning."""

import hashlib
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from luca.urn import PolyaUrn


class Pruner:
    """Handles metabolic cost, deduplication, and urn entropy management.

    Longer code pays a higher "energy" cost; duplicate expressions are
    rejected to prevent the urn from filling with trivial clones.
    """

    def __init__(self) -> None:
        self._history_hashes: set[str] = set()
        self._base_length: int = 30  # Reference "normal" code length

    # ------------------------------------------------------------------
    # Metabolic cost
    # ------------------------------------------------------------------

    def metabolic_penalty(self, code: str) -> float:
        """Compute a multiplicative penalty factor based on code length.

        Longer code → higher cost → lower reinforcement weight.

        Args:
            code: The generated Lean source code string.

        Returns:
            A factor in (0, 1] that multiplies the reinforcement weight.
        """
        length = len(code)
        if length <= self._base_length:
            return 1.0
        # Exponential penalty: each extra 50 chars halves the bonus
        excess = length - self._base_length
        return math.exp(-excess / 50.0)

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    def _hash_code(self, code: str) -> str:
        """Normalised hash to detect structurally identical expressions."""
        normalised = " ".join(code.split())  # collapse whitespace
        return hashlib.sha256(normalised.encode()).hexdigest()

    def is_duplicate(self, code: str) -> bool:
        """Check whether semantically equivalent code has been seen before.

        Args:
            code: Lean source code to check.

        Returns:
            True if the code (after whitespace normalisation) was seen before.
        """
        h = self._hash_code(code)
        if h in self._history_hashes:
            return True
        self._history_hashes.add(h)
        return False

    def record_code(self, code: str) -> None:
        """Record a code hash without checking (for tracking dead expressions)."""
        self._history_hashes.add(self._hash_code(code))

    # ------------------------------------------------------------------
    # Urn maintenance
    # ------------------------------------------------------------------

    @staticmethod
    def prune_urn(urn: "PolyaUrn", max_size: int) -> int:
        """Remove lowest-weight tokens until urn is within *max_size*.

        Returns:
            Number of tokens pruned.
        """
        if urn.size() <= max_size:
            return 0
        sorted_tokens = sorted(urn.weights.items(), key=lambda x: x[1])
        to_remove = urn.size() - max_size
        for t, _ in sorted_tokens[:to_remove]:
            del urn.weights[t]
        return to_remove
