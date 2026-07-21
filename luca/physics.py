"""Lean 4 Compiler Sandbox -- the "Physical Law of Physics" for evolution."""

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

from luca.config import LEAN_TIMEOUT, TMP_WORKSPACE


@dataclass
class LeanResult:
    """Outcome of a Lean compilation check."""

    alive: bool
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float


class LeanSandbox:
    """Isolated Lean 4 compiler runner using subprocess.

    Each candidate expression is written to a temporary .lean file and
    verified by the local ``lean`` CLI.  Timeout guards against infinite
    loops in tactics like ``simp`` or ``omega``.
    """

    def __init__(self, workspace: Optional[str] = None) -> None:
        """Initialise the sandbox.

        Args:
            workspace: Directory for temp .lean files. Defaults to config.TMP_WORKSPACE.
        """
        self.workspace = workspace or TMP_WORKSPACE
        os.makedirs(self.workspace, exist_ok=True)
        self._lean_bin: Optional[str] = None
        self._available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Lean binary detection
    # ------------------------------------------------------------------

    def is_lean_available(self) -> bool:
        """Check whether ``lean`` is on PATH and executable.

        Returns:
            True if Lean 4 is available.
        """
        if self._available is not None:
            return self._available
        self._lean_bin = shutil.which("lean")
        self._available = self._lean_bin is not None
        return self._available

    @property
    def lean_bin(self) -> str:
        """Path to the ``lean`` binary.  Raises RuntimeError if not found."""
        if not self.is_lean_available():
            raise RuntimeError(
                "Lean 4 compiler ('lean') not found on PATH. "
                "Please install Lean 4 and ensure 'lean' is accessible. "
                "See https://lean-lang.org/lean4/doc/setup.html"
            )
        assert self._lean_bin is not None
        return self._lean_bin

    # ------------------------------------------------------------------
    # Compilation check
    # ------------------------------------------------------------------

    def verify(self, code: str, gene_name: str = "candidate") -> LeanResult:
        """Write *code* to a temp file and compile with ``lean``.

        Args:
            code: Lean 4 source code to verify.
            gene_name: Used for the temp filename (cosmetic).

        Returns:
            LeanResult with alive=True iff exit_code == 0.
        """
        # Ensure we have a preamble that makes the code standalone
        full_code = self._wrap_code(code)

        # Write to temp file
        filepath = os.path.join(self.workspace, f"{gene_name}.lean")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_code)

            start = time.perf_counter()
            proc = subprocess.run(
                [self.lean_bin, filepath],
                capture_output=True,
                text=True,
                timeout=LEAN_TIMEOUT,
                cwd=self.workspace,
            )
            elapsed = (time.perf_counter() - start) * 1000.0

            return LeanResult(
                alive=(proc.returncode == 0),
                exit_code=proc.returncode,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                elapsed_ms=elapsed,
            )
        except subprocess.TimeoutExpired:
            return LeanResult(
                alive=False,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {LEAN_TIMEOUT}s",
                elapsed_ms=LEAN_TIMEOUT * 1000.0,
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Lean binary '{self.lean_bin}' not found or not executable."
            )
        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    @staticmethod
    def _wrap_code(code: str) -> str:
        """Optionally wrap code with necessary imports/preamble.

        For simple expressions we don't need imports since Lean's Init
        is always available.  We just ensure the code is non-empty.
        """
        code = code.strip()
        if not code:
            return "example : True := trivial"
        return code

    def cleanup(self) -> None:
        """Remove all temp .lean files from the workspace."""
        for fname in os.listdir(self.workspace):
            if fname.endswith(".lean"):
                try:
                    os.remove(os.path.join(self.workspace, fname))
                except OSError:
                    pass
