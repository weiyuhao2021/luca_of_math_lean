"""Pólya Urn Engine with Innovation -- non-Markovian random process core."""

import random
from typing import Optional

from luca.config import INITIAL_TOKENS, INNOVATION_RATE, DECAY_RATE, MAX_URN_SIZE


class PolyaUrn:
    """A non-Markovian Pólya Urn that maintains a weighted multiset of tokens.

    The urn implements path-dependent reinforcement: tokens used in successful
    Lean expressions gain weight, tilting future sampling probabilities.

    Attributes:
        weights: Mapping from token string to its current weight (float > 0).
    """

    def __init__(self, initial_tokens: Optional[list[str]] = None) -> None:
        """Initialise the urn with an initial token soup.

        Args:
            initial_tokens: List of token strings. Defaults to config.INITIAL_TOKENS.
        """
        tokens = initial_tokens if initial_tokens is not None else INITIAL_TOKENS
        self.weights: dict[str, float] = {}
        for t in tokens:
            self.weights[t] = self.weights.get(t, 0.0) + 1.0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def sample(self, k: int = 1) -> list[str]:
        """Weighted random sample of *k* tokens *without* replacement.

        Returns fewer than *k* tokens if the urn contains fewer items.
        """
        available = list(self.weights.keys())
        if not available:
            return []
        k = min(k, len(available))
        # Weighted sampling without replacement via sequential draws
        weights = [self.weights[t] for t in available]
        chosen: list[str] = []
        pool = list(available)
        ws = list(weights)
        for _ in range(k):
            if not pool or sum(ws) <= 0:
                break
            pick = random.choices(pool, weights=ws, k=1)[0]
            chosen.append(pick)
            idx = pool.index(pick)
            pool.pop(idx)
            ws.pop(idx)
        return chosen

    def reinforce(self, used_tokens: list[str], count: float = 1.0) -> None:
        """Increase weight for successfully used tokens (non-Markovian memory).

        Args:
            used_tokens: Tokens that contributed to a successful expression.
            count: Amount to add (default 1.0).
        """
        for t in used_tokens:
            if t in self.weights:
                self.weights[t] += count

    def innovate(self, new_token: str) -> None:
        """Register a newly compiled definition/theorem as a building block.

        Args:
            new_token: The name of the new gene (e.g. 'gene_42').
        """
        if new_token not in self.weights:
            self.weights[new_token] = INNOVATION_RATE
        else:
            self.weights[new_token] += INNOVATION_RATE * 0.5

    def decay(self, rate: Optional[float] = None) -> None:
        """Apply exponential weight decay to all tokens.

        When the urn exceeds MAX_URN_SIZE, the lowest-weight tokens are pruned.

        Args:
            rate: Multiplicative decay factor. Defaults to config.DECAY_RATE.
        """
        r = rate if rate is not None else DECAY_RATE
        for t in list(self.weights.keys()):
            self.weights[t] *= r
            # Remove tokens that have decayed to near-zero
            if self.weights[t] < 0.01:
                del self.weights[t]

        # Prune if over capacity
        if len(self.weights) > MAX_URN_SIZE:
            sorted_tokens = sorted(self.weights.items(), key=lambda x: x[1])
            to_remove = len(self.weights) - MAX_URN_SIZE
            for t, _ in sorted_tokens[:to_remove]:
                del self.weights[t]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def top(self, n: int = 5) -> list[tuple[str, float]]:
        """Return the *n* highest-weight tokens."""
        return sorted(self.weights.items(), key=lambda x: -x[1])[:n]

    def size(self) -> int:
        """Number of distinct tokens currently in the urn."""
        return len(self.weights)

    def total_weight(self) -> float:
        """Sum of all token weights."""
        return sum(self.weights.values())

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the urn state to a plain dict."""
        return {"weights": dict(self.weights)}

    @classmethod
    def from_dict(cls, data: dict) -> "PolyaUrn":
        """Restore an urn from a serialised dict."""
        urn = cls(initial_tokens=[])
        urn.weights = dict(data.get("weights", {}))
        return urn
