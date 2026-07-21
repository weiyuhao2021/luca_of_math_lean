"""luca_of_math_lean — A zero-cost artificial life kernel.

Uses Pólya's Urn dynamics (non-Markovian reinforcement) paired with the
Lean 4 compiler as the immutable "physical law" to drive open-ended
mathematical evolution.
"""

__version__ = "0.1.0"

from luca.urn import PolyaUrn
from luca.grammar import LeanAssembler
from luca.physics import LeanSandbox
from luca.pruner import Pruner
from luca.syllogism import SyllogismRenderer
from luca.engine import EvolutionEngine

__all__ = [
    "PolyaUrn",
    "LeanAssembler",
    "LeanSandbox",
    "Pruner",
    "SyllogismRenderer",
    "EvolutionEngine",
]
