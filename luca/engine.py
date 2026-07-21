"""Main Evolution Loop -- the LUCA evolutionary engine with catastrophe system."""

import json
import math
import os
import random
import tempfile
import time
from typing import Optional

from luca.config import (
    MAX_URN_SIZE,
    INNOVATION_RATE,
    DECAY_RATE,
    CATASTROPHE_PROBABILITY,
    MAX_EXPRESSION_TOKENS,
    EVOLUTION_OUTPUT_FILE,
    URN_STATE_FILE,
    EVOLUTION_LOG_FILE,
)
from luca.urn import PolyaUrn
from luca.grammar import LeanAssembler
from luca.physics import LeanSandbox
from luca.pruner import Pruner
from luca.syllogism import SyllogismRenderer

# Rich is optional but highly recommended for colored output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


# ---------------------------------------------------------------------------
# Catastrophe definitions
# ---------------------------------------------------------------------------

_CATASTROPHE_NAMES: dict[str, str] = {
    "mass_extinction": "质量灭绝",
    "genetic_drift": "基因漂变",
    "cambrian_explosion": "寒武纪大爆发",
    "asteroid_impact": "小行星撞击",
    "ice_age": "冰河期",
}

_CATASTROPHE_DESCRIPTIONS: dict[str, str] = {
    "mass_extinction": "环境剧变——低权重 token 被大量清除，仅强者幸存",
    "genetic_drift": "种群瓶颈——所有基因权重向均值回归，多样性骤降",
    "cambrian_explosion": "共生大爆发——存活基因两两杂交，新复合 token 涌现",
    "asteroid_impact": "天外撞击——随机半数基因湮灭，幸存者获得超强选择优势",
    "ice_age": "冰河降临——万物凋零，唯抽象结构（fun/λ/match）独享抗冻加成",
}


def _apply_catastrophe(urn: PolyaUrn, catastrophe_type: str) -> str:
    """Apply a catastrophe to the urn and return a human-readable description."""
    weights = urn.weights

    if catastrophe_type == "mass_extinction":
        # Remove 20-40% of the lowest-weight tokens
        fraction = random.uniform(0.2, 0.4)
        sorted_items = sorted(weights.items(), key=lambda x: x[1])
        kill_count = max(1, int(len(sorted_items) * fraction))
        for t, _ in sorted_items[:kill_count]:
            del weights[t]
        return f"移除 {kill_count} 个低权重 token（{fraction:.0%}）"

    elif catastrophe_type == "genetic_drift":
        # Regress all weights toward the mean by 30%
        if not weights:
            return "瓮已空，无漂变可施"
        mean_w = sum(weights.values()) / len(weights)
        for t in list(weights.keys()):
            weights[t] = weights[t] * 0.7 + mean_w * 0.3
        return f"所有权重向均值 {mean_w:.2f} 回归 30%"

    elif catastrophe_type == "cambrian_explosion":
        # Combine pairs of high-weight tokens into new compound tokens
        top_tokens = sorted(weights.items(), key=lambda x: -x[1])
        top_n = min(20, len(top_tokens))
        top_items = top_tokens[:top_n]
        new_tokens = 0
        for i in range(min(10, len(top_items))):
            for j in range(i + 1, min(10, len(top_items))):
                if random.random() < 0.3:
                    a, b = top_items[i][0], top_items[j][0]
                    new_name = f"{a}_{b}"
                    if new_name not in weights:
                        avg_w = (weights[a] + weights[b]) / 2 * 0.5
                        weights[new_name] = avg_w
                        new_tokens += 1
        return f"杂交生成 {new_tokens} 个新复合 token"

    elif catastrophe_type == "asteroid_impact":
        # Randomly delete 50% of tokens, double weight of survivors
        all_tokens = list(weights.keys())
        kill_count = max(1, len(all_tokens) // 2)
        victims = set(random.sample(all_tokens, kill_count))
        for t in victims:
            del weights[t]
        for t in weights:
            weights[t] *= 2.0
        return f"湮灭 {kill_count} 个 token，幸存者权重翻倍"

    elif catastrophe_type == "ice_age":
        # Halve all weights, but fun/λ/match/def get a bonus
        cold_resistant = {"fun", "λ", "match", "def", "theorem", "let", "have"}
        for t in list(weights.keys()):
            if t in cold_resistant:
                weights[t] *= 1.5  # Anti-freeze bonus
            else:
                weights[t] *= 0.5
            if weights[t] < 0.1:
                del weights[t]
        return "抽象构造 token（fun/λ/match/def）获得抗冻加成，其余权重减半"

    return "未知天灾"


# ---------------------------------------------------------------------------
# Evolution Engine
# ---------------------------------------------------------------------------

class EvolutionEngine:
    """Orchestrates the continuous open-ended evolution loop.

    The loop follows the Pólya urn reinforcement cycle:

    1. Sample tokens from urn
    2. Assemble Lean candidate via grammar
    3. Verify with Lean compiler (physics)
    4. If alive: reinforce, innovate, log, prune
    5. If dead: discard, slight penalty
    6. Occasionally trigger random catastrophes
    """

    def __init__(
        self,
        max_generations: int = 10_000,
        lean_timeout: Optional[float] = None,
        output_file: Optional[str] = None,
        resume: bool = False,
    ) -> None:
        self.max_generations = max_generations
        self.output_file = output_file or EVOLUTION_OUTPUT_FILE

        # Modules
        self.urn = PolyaUrn()
        self.assembler = LeanAssembler()
        self.sandbox = LeanSandbox()
        self.pruner = Pruner()
        self.renderer = SyllogismRenderer()

        # State
        self.generation: int = 0
        self.alive_count: int = 0
        self.dead_count: int = 0
        self.start_time: float = 0.0
        self._running: bool = False
        self._catastrophe_timer: int = random.randint(50, 200)

        # Rich console
        self.console = Console() if _HAS_RICH else None

        # Resume from previous state
        if resume:
            self._load_state()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the evolution loop."""
        self._print_banner()

        if not self.sandbox.is_lean_available():
            self._print_error(
                "Lean 4 compiler ('lean') not found on PATH.\n"
                "Install Lean 4: https://lean-lang.org/lean4/doc/setup.html\n"
                "Then ensure 'lean' is on your PATH and try again."
            )
            return

        self._running = True
        self.start_time = time.perf_counter()

        try:
            while self._running and self.generation < self.max_generations:
                self.generation += 1
                self._step()
        except KeyboardInterrupt:
            self._print_warning("\n演化被用户中断。")
        finally:
            self._save_state()
            self._print_summary()

    def stop(self) -> None:
        """Gracefully stop the evolution loop."""
        self._running = False

    # ------------------------------------------------------------------
    # Single generation step
    # ------------------------------------------------------------------

    def _step(self) -> None:
        """Execute one generation of the evolution cycle."""
        # 1. Sample tokens
        k = random.randint(3, MAX_EXPRESSION_TOKENS)
        tokens = self.urn.sample(k)

        # 2. Assemble Lean candidate
        code, gene_name = self.assembler.assemble(tokens)

        # 3. Dedup check
        if self.pruner.is_duplicate(code):
            self._log_dead(gene_name, code, "DUPLICATE")
            return

        # 4. Lean verification
        result = self.sandbox.verify(code, gene_name)

        if result.alive:
            # 5a. ALIVE: reinforce, innovate, log, prune
            penalty = self.pruner.metabolic_penalty(code)
            self.urn.reinforce(tokens, count=penalty)
            self.urn.innovate(gene_name)
            self.alive_count += 1

            # Append to evolved library
            self._append_to_library(code, gene_name)

            # Log
            self._log_alive(gene_name, code, result, penalty)

            # Periodic decay
            if self.generation % 10 == 0:
                self.urn.decay(DECAY_RATE)

            # Prune if oversized
            self.pruner.prune_urn(self.urn, MAX_URN_SIZE)

        else:
            # 5b. DEAD: discard
            self.dead_count += 1
            self.pruner.record_code(code)

            # Slight penalty to overused dead-end tokens
            if self.generation % 5 == 0:
                for t in tokens:
                    if t in self.urn.weights:
                        self.urn.weights[t] *= 0.99

            self._log_dead(gene_name, code, "COMPILE_ERROR")

        # 6. Catastrophe check
        self._catastrophe_timer -= 1
        if self._catastrophe_timer <= 0:
            self._trigger_catastrophe()
            self._catastrophe_timer = random.randint(50, 200)

        # 7. Periodic state save
        if self.generation % 100 == 0:
            self._save_state()

    # ------------------------------------------------------------------
    # Catastrophe system
    # ------------------------------------------------------------------

    def _trigger_catastrophe(self) -> None:
        """Randomly select and apply a catastrophe."""
        ctype = random.choice(list(_CATASTROPHE_NAMES.keys()))
        name = _CATASTROPHE_NAMES[ctype]
        desc = _CATASTROPHE_DESCRIPTIONS[ctype]
        detail = _apply_catastrophe(self.urn, ctype)

        if self.console:
            panel = Panel(
                f"[bold red]╔══════════════════════════════════════╗[/bold red]\n"
                f"[bold red]║[/bold red]  [bold yellow]天灾降临: {name}[/bold yellow]\n"
                f"[bold red]║[/bold red]  {desc}\n"
                f"[bold red]║[/bold red]  {detail}\n"
                f"[bold red]╚══════════════════════════════════════╝[/bold red]",
                border_style="red",
            )
            self.console.print(panel)
        else:
            print(f"\n!!! 天灾: {name} — {desc} ({detail})\n")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _print_banner(self) -> None:
        """Print welcome banner."""
        banner = r"""
╔══════════════════════════════════════════════════════════╗
║         luca_of_math_lean  — 数学演化内核 v0.1            ║
║  零 API 成本 · Pólya 瓮动力学 · Lean 4 物理定律           ║
╚══════════════════════════════════════════════════════════╝
"""
        if self.console:
            self.console.print(banner, style="bold cyan")
        else:
            print(banner)

    def _log_alive(
        self, gene_name: str, code: str, result, penalty: float
    ) -> None:
        """Log a successful compilation."""
        code_short = code.replace("\n", " ").strip()
        if len(code_short) > 80:
            code_short = code_short[:77] + "..."

        syllogism = self.renderer.render(code, gene_name)

        if self.console:
            self.console.print(
                f"[bold cyan][LUCA Epoch {self.generation:05d}][/bold cyan] "
                f"[green]SAMPLING → CHECKING LEAN... [ALIVE!][/green] "
                f"({result.elapsed_ms:.0f}ms)"
            )
            self.console.print(f"  [dim]└─ Code:[/dim] {code_short}")
            self.console.print(f"  [dim]└─[/dim] [green]{syllogism}[/green]")
            self.console.print(
                f"  [dim]└─ Urn: {self.urn.size()} tokens | "
                f"Alive={self.alive_count} Dead={self.dead_count} | "
                f"Penalty={penalty:.3f}[/dim]"
            )
        else:
            print(f"[LUCA Epoch {self.generation:05d}] SAMPLING → CHECKING LEAN... [ALIVE!] ({result.elapsed_ms:.0f}ms)")
            print(f"  └─ Code: {code_short}")
            print(f"  └─ {syllogism}")
            print(f"  └─ Urn: {self.urn.size()} tokens | Alive={self.alive_count} Dead={self.dead_count}")

    def _log_dead(self, gene_name: str, code: str, reason: str) -> None:
        """Log a failed compilation."""
        code_short = code.replace("\n", " ").strip()
        if len(code_short) > 80:
            code_short = code_short[:77] + "..."

        if self.console:
            self.console.print(
                f"[bold cyan][LUCA Epoch {self.generation:05d}][/bold cyan] "
                f"[red]SAMPLING → CHECKING LEAN... [DEAD][/red] "
                f"[dim]({reason})[/dim]"
            )
            self.console.print(f"  [dim]└─ Code:[/dim] {code_short}")
        else:
            print(f"[LUCA Epoch {self.generation:05d}] SAMPLING → CHECKING LEAN... [DEAD] ({reason})")
            print(f"  └─ Code: {code_short}")

    def _print_error(self, msg: str) -> None:
        """Print an error message."""
        if self.console:
            self.console.print(f"[bold red]ERROR:[/bold red] {msg}")
        else:
            print(f"ERROR: {msg}")

    def _print_warning(self, msg: str) -> None:
        """Print a warning."""
        if self.console:
            self.console.print(f"[yellow]{msg}[/yellow]")
        else:
            print(msg)

    def _print_summary(self) -> None:
        """Print final evolution statistics."""
        elapsed = time.perf_counter() - self.start_time
        top_tokens = self.urn.top(10)

        if self.console:
            self.console.print("\n" + "=" * 60)
            self.console.print("[bold]演化终止 — 最终统计[/bold]")
            self.console.print(f"  总代数:     {self.generation}")
            self.console.print(f"  存活:       [green]{self.alive_count}[/green]")
            self.console.print(f"  消亡:       [red]{self.dead_count}[/red]")
            survival_rate = (
                self.alive_count / max(1, self.alive_count + self.dead_count) * 100
            )
            self.console.print(f"  存活率:     {survival_rate:.1f}%")
            self.console.print(f"  瓮中 Token: {self.urn.size()}")
            self.console.print(f"  耗时:       {elapsed:.1f}s")

            if top_tokens:
                self.console.print("\n[bold]权重 TOP 10:[/bold]")
                for t, w in top_tokens:
                    self.console.print(f"  {t:30s} {w:.2f}")
            self.console.print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("演化终止 — 最终统计")
            print(f"  总代数:     {self.generation}")
            print(f"  存活:       {self.alive_count}")
            print(f"  消亡:       {self.dead_count}")
            print(f"  瓮中 Token: {self.urn.size()}")
            print(f"  耗时:       {elapsed:.1f}s")
            if top_tokens:
                print("\n权重 TOP 10:")
                for t, w in top_tokens:
                    print(f"  {t:30s} {w:.2f}")
            print("=" * 60)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _append_to_library(self, code: str, gene_name: str) -> None:
        """Append a successfully verified definition to the evolved library."""
        header = f"\n-- [{self.generation:05d}] {gene_name} (ALIVE)\n"
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(header)
                f.write(code + "\n")
        except OSError:
            pass

    def _save_state(self) -> None:
        """Save urn state to JSON for resumption (atomic write for crash safety)."""
        state = {
            "generation": self.generation,
            "alive_count": self.alive_count,
            "dead_count": self.dead_count,
            "urn": self.urn.to_dict(),
        }
        try:
            # Atomic write: write to temp file first, then rename.
            # This prevents corruption if the process crashes mid-write.
            dirname = os.path.dirname(URN_STATE_FILE) or "."
            fd, tmp_path = tempfile.mkstemp(
                suffix=".json", prefix="urn_state_", dir=dirname
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, URN_STATE_FILE)
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except OSError:
            pass

    def _load_state(self) -> None:
        """Load urn state from a previous run.

        Restores generation counter, alive/dead tallies, urn weights,
        and sets the assembler's gene counter to avoid name collisions.
        """
        if not os.path.exists(URN_STATE_FILE):
            return
        try:
            with open(URN_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            self.generation = state.get("generation", 0)
            self.alive_count = state.get("alive_count", 0)
            self.dead_count = state.get("dead_count", 0)
            urn_data = state.get("urn", {})
            self.urn = PolyaUrn.from_dict(urn_data)

            # Restore gene counter so gene names don't collide across sessions.
            # We set it to generation * 2 as a safe upper bound (each generation
            # produces exactly one gene_name, so generation is sufficient).
            self.assembler._gene_counter = max(
                self.assembler._gene_counter, self.generation
            )

            # Reset catastrophe timer to a fresh random interval
            self._catastrophe_timer = random.randint(50, 200)

            if self.console:
                self.console.print(
                    f"[green]已恢复状态: 第 {self.generation} 代, "
                    f"瓮中有 {self.urn.size()} 个 token[/green]"
                )
            else:
                print(
                    f"已恢复状态: 第 {self.generation} 代, "
                    f"瓮中有 {self.urn.size()} 个 token"
                )
        except (OSError, json.JSONDecodeError):
            pass

    # ------------------------------------------------------------------
    # Top tokens display
    # ------------------------------------------------------------------

    def show_top_tokens(self, n: int = 10) -> None:
        """Display the highest-weight tokens."""
        top = self.urn.top(n)
        if self.console:
            table = Table(title=f"Top {n} Tokens")
            table.add_column("Token", style="cyan")
            table.add_column("Weight", style="green", justify="right")
            for t, w in top:
                table.add_row(t, f"{w:.3f}")
            self.console.print(table)
        else:
            print(f"\nTop {n} Tokens:")
            for t, w in top:
                print(f"  {t:30s} {w:.3f}")
